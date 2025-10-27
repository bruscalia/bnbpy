import gc
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import cast

import pandas as pd

from bnbprob.pafssp import CallbackBnB, PermFlowShop
from bnbprob.pafssp.instances import AssemblyFlowShopInstance
from bnbpy import configure_logfile

configure_logfile('dfm-experiments.log', mode='w')

gc.disable()


class WsFlowShop(PermFlowShop):
    def warmstart(self) -> 'WsFlowShop':
        jobs = self.sequence
        p = jobs[0].p
        m = len(p)
        n = len(jobs)
        return cast(WsFlowShop, super().randomized_heur(n * m, 42))


@dataclass
class Experiment:
    name: str
    warmstart: int
    lb1_start: int
    lb5_start: int
    incumbent: int
    lower_bound: int
    execution_time: float
    gap: float
    nodes: int
    sequence: list[int]


def run_experiment(
    name: str, instance: AssemblyFlowShopInstance, timelimit: int = 3600
) -> Experiment:
    # Initialization
    cutoff_mach = 10
    if len(instance.p[0]) - 4 >= cutoff_mach:
        problem = WsFlowShop.from_p(instance.p, edges=instance.edges)
    else:
        problem = PermFlowShop.from_p(instance.p, edges=instance.edges)
    bnb = CallbackBnB(rtol=0.0001, save_tree=False)
    # Lower bounds and warmstart
    lb1_start = problem.calc_lb_1m()
    lb5_start = problem.calc_lb_2m()
    warmstart_prob = problem.warmstart()
    ws2 = warmstart_prob.local_search()
    if ws2 is not None:
        warmstart_prob = ws2
    warmstart = warmstart_prob.calc_lb_1m()
    # Solve
    start_time = time.time()
    sol = bnb.solve(problem, maxiter=100_000_000, timelimit=timelimit)
    execution_time = time.time() - start_time
    # Results
    sequence_jobs = sol.problem.sequence
    sequence = [job.j for job in sequence_jobs] if sequence_jobs else []
    experiment = Experiment(
        name,
        warmstart,
        lb1_start,
        lb5_start,
        int(bnb.ub),
        int(bnb.lb),
        execution_time,
        bnb.gap,
        bnb.explored,
        sequence,
    )
    gc.collect()
    time.sleep(0.2)
    return experiment


if __name__ == '__main__':
    experiments = list[Experiment]()

    input_path = './../data/pafssp/d2f'
    # Scan directory for all instances
    all_files = os.listdir(input_path)
    all_files.sort()
    for file in all_files:
        if not file.endswith('.json'):
            continue
        name = file[:-5]
        idx = int(name[4:7])
        with open(os.path.join(input_path, file), 'r', encoding='utf8') as f:
            data = json.load(f)
        instance = AssemblyFlowShopInstance(data["p"], data["edges"])
        experiment = run_experiment(name, instance, timelimit=3600)
        experiments.append(experiment)
        print(experiment)

    df_dfm = pd.DataFrame([asdict(e) for e in experiments])
    df_dfm.to_csv('dfm-experiments.csv', index=False)
