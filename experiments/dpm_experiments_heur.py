import gc
import json
import os
import time
from dataclasses import asdict, dataclass

import pandas as pd

from bnbprob.pafssp import PermFlowShop
from bnbprob.pafssp.instances import AssemblyFlowShopInstance
from bnbpy import configure_logfile

configure_logfile('dpm-experiments-heur.log', mode='w')

gc.disable()


@dataclass
class Experiment:
    name: str
    neh: int
    neh_ls: int
    multistart: int
    iga: int


def run_experiment(
    name: str,
    instance: AssemblyFlowShopInstance
) -> Experiment:
    # Initialization
    problem = PermFlowShop.from_p(
        instance.p, edges=instance.edges, constructive="quick"
    )
    # Lower bounds and warmstart
    neh_prob = problem.neh_initialization()
    neh_prob.compute_bound()
    neh_val = neh_prob.calc_lb_1m()
    neh_ls = neh_prob.local_search()
    if neh_ls is None:
        neh_ls = neh_prob.copy()
    neh_ls_val = neh_ls.calc_lb_1m()
    ms_prob = problem.multistart_initialization()
    ms_val = ms_prob.calc_lb_1m()
    iga_prob = problem.iga_initialization()
    iga_val = iga_prob.calc_lb_1m()
    # Results
    experiment = Experiment(
        name,
        neh_val,
        neh_ls_val,
        ms_val,
        iga_val
    )
    gc.collect()
    time.sleep(0.2)
    return experiment


if __name__ == '__main__':
    experiments = list[Experiment]()

    input_path = './../data/pafssp/dpm'
    # Scan directory for all instances
    all_files = os.listdir(input_path)
    all_files.sort()
    for file in all_files:
        if not file.endswith('.json'):
            continue
        name = file[:-5]
        mach_def = file.split('.')[0].split('-')[-1]
        idx = int(name[4:7])
        with open(os.path.join(input_path, file), 'r', encoding='utf8') as f:
            data = json.load(f)
        instance = AssemblyFlowShopInstance(data['p'], data['edges'])
        experiment = run_experiment(
            name, instance
        )
        if experiment is None:
            continue
        experiments.append(experiment)
        print(experiment)

    df_dpm = pd.DataFrame([asdict(e) for e in experiments])
    df_dpm.to_csv('dpm-experiments-heur.csv', index=False)
