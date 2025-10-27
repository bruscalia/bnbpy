import gc
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Literal

import pandas as pd

from bnbprob.pafssp import CallbackBnB, PermFlowShop
from bnbprob.pafssp.instances import AssemblyFlowShopInstance
from bnbpy import configure_logfile

configure_logfile('dfm-experiments-split.log', mode='w')

gc.disable()


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
    name: str,
    p: list[list[int]],
    timelimit: int = 3600,
    constructive: Literal['multistart', 'neh'] = 'multistart',
) -> Experiment | None:
    # Initialization
    problem = PermFlowShop.from_p(
        p, constructive=constructive
    )
    delay_lb5 = CallbackBnB.delay_by_root(problem)
    bnb = CallbackBnB(rtol=0.0001, save_tree=False, delay_lb5=delay_lb5)
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
    sol = bnb.solve(problem, maxiter=1000_000_000, timelimit=timelimit)
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
    experiments_1 = list[Experiment]()
    experiments_2 = list[Experiment]()

    input_path = './../data/pafssp/d2f'
    # Scan directory for all instances
    all_files = os.listdir(input_path)
    all_files.sort()
    for file in all_files:
        if not file.endswith('.json'):
            continue
        name = file[:-5]
        mach_def = file.split('.')[0].split('-')[-1]
        if mach_def == '15x15':
            continue
        idx = int(name[4:7])
        with open(os.path.join(input_path, file), 'r', encoding='utf8') as f:
            data = json.load(f)
        # Prevent from extra computational effort in simple instances
        constructive: Literal['multistart', 'neh'] = 'neh'
        if mach_def != '7x7':
            constructive = 'multistart'
        instance = AssemblyFlowShopInstance(data['p'], data['edges'])
        if len(data['p']) > 20 and mach_def != '7x7':
            continue
        m = len(data['p'][0]) // 2
        p1 = [row[:m] for row in data['p']]
        experiment = run_experiment(
            name, p1, timelimit=3600, constructive=constructive
        )
        if experiment is None:
            continue
        experiments_1.append(experiment)
        print(experiment)
        p2 = [row[m:] for row in data['p']]
        experiment = run_experiment(
            name, p2, timelimit=3600, constructive=constructive
        )
        if experiment is None:
            continue
        experiments_2.append(experiment)
        print(experiment)

    df_dfm_1 = pd.DataFrame([asdict(e) for e in experiments_1])
    df_dfm_1.to_csv('dfm-experiments-split-1.csv', index=False)
    df_dfm_2 = pd.DataFrame([asdict(e) for e in experiments_2])
    df_dfm_2.to_csv('dfm-experiments-split-2.csv', index=False)
