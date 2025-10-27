import gc
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from bnbprob.pafssp import (
    BenchCutoffBnB,
    BenchPermFlowShop,
    CutoffBnB,
    PermFlowShop,
)
from bnbpy import configure_logfile

configure_logfile('delayed-bound-experiments.log', mode='w')


@dataclass
class ExperimentData:
    name: str
    optimal: bool
    value: int


data_ritt: Any = [
    {'name': 'ta001', 'optimal': True, 'value': 1278},
    {'name': 'ta002', 'optimal': True, 'value': 1359},
    {'name': 'ta003', 'optimal': True, 'value': 1081},
    {'name': 'ta004', 'optimal': True, 'value': 1293},
    {'name': 'ta005', 'optimal': True, 'value': 1235},
    {'name': 'ta006', 'optimal': True, 'value': 1195},
    {'name': 'ta007', 'optimal': True, 'value': 1234},
    {'name': 'ta008', 'optimal': True, 'value': 1206},
    {'name': 'ta009', 'optimal': True, 'value': 1230},
    {'name': 'ta010', 'optimal': True, 'value': 1108},
    {'name': 'ta011', 'optimal': True, 'value': 1582},
    {'name': 'ta012', 'optimal': True, 'value': 1659},
    {'name': 'ta013', 'optimal': True, 'value': 1496},
    {'name': 'ta014', 'optimal': True, 'value': 1377},
    {'name': 'ta015', 'optimal': True, 'value': 1419},
    {'name': 'ta016', 'optimal': True, 'value': 1397},
    {'name': 'ta017', 'optimal': True, 'value': 1484},
    {'name': 'ta018', 'optimal': True, 'value': 1538},
    {'name': 'ta019', 'optimal': True, 'value': 1593},
    {'name': 'ta020', 'optimal': True, 'value': 1591},
    {'name': 'ta031', 'optimal': True, 'value': 2724},
    {'name': 'ta032', 'optimal': True, 'value': 2834},
    {'name': 'ta033', 'optimal': True, 'value': 2621},
    {'name': 'ta034', 'optimal': True, 'value': 2751},
    {'name': 'ta035', 'optimal': True, 'value': 2863},
    {'name': 'ta036', 'optimal': True, 'value': 2829},
    {'name': 'ta037', 'optimal': True, 'value': 2725},
    {'name': 'ta038', 'optimal': True, 'value': 2683},
    {'name': 'ta039', 'optimal': True, 'value': 2552},
    {'name': 'ta040', 'optimal': True, 'value': 2782},
    {'name': 'ta041', 'optimal': True, 'value': 2991},
    {'name': 'ta042', 'optimal': True, 'value': 2867},
    {'name': 'ta043', 'optimal': True, 'value': 2839},
    {'name': 'ta044', 'optimal': True, 'value': 3063},
    {'name': 'ta045', 'optimal': True, 'value': 2976},
    {'name': 'ta046', 'optimal': True, 'value': 3006},
    {'name': 'ta047', 'optimal': True, 'value': 3093},
    {'name': 'ta048', 'optimal': True, 'value': 3037},
    {'name': 'ta049', 'optimal': True, 'value': 2897},
    {'name': 'ta050', 'optimal': True, 'value': 3065},
]

experiment_data = [ExperimentData(**d) for d in data_ritt]


@dataclass
class Experiment:
    name: str
    execution_time: float
    lower_bound: int
    status: str
    nodes: int


BnbType = type[CutoffBnB] | type[BenchCutoffBnB]
FlowType = type[PermFlowShop]


def run_experiment(  # noqa: PLR0913, PLR0917
    name: str,
    p: list[list[int]],
    bnb_cls: BnbType,
    pfsp_cls: FlowType,
    ub: int,
    timelimit: int = 3600,
) -> Experiment:
    # Initialization
    problem = pfsp_cls.from_p(p, constructive='quick')
    bnb = bnb_cls(ub, delay_lb5=True)
    # Solve
    start_time = time.time()
    sol = bnb.solve(problem, maxiter=1000_000_000, timelimit=timelimit)
    execution_time = time.time() - start_time
    # Results
    experiment = Experiment(
        name, execution_time, int(sol.lb), str(sol.status), bnb.explored
    )
    gc.collect()
    time.sleep(0.2)
    return experiment


if __name__ == '__main__':
    experiments_delay = list[Experiment]()

    # Scan directory for all instances
    for ed in experiment_data:
        with open(
            f'./../data/flow-shop/{ed.name}.json', mode='r', encoding='utf8'
        ) as f:
            p = json.load(f)
        experiment = run_experiment(
            ed.name, p, CutoffBnB, PermFlowShop, ed.value, 3600
        )
        experiments_delay.append(experiment)
        print(experiment)

    df_delay = pd.DataFrame([asdict(e) for e in experiments_delay])
    df_delay.to_csv('delayed-bound-experiments-new.csv', index=False)

    experiments_bench = list[Experiment]()

    # Scan directory for all instances
    for ed in experiment_data:
        with open(
            f'./../data/flow-shop/{ed.name}.json', mode='r', encoding='utf8'
        ) as f:
            p = json.load(f)
        experiment = run_experiment(
            ed.name, p, BenchCutoffBnB, BenchPermFlowShop, ed.value, 3600
        )
        experiments_bench.append(experiment)
        print(experiment)

    df_base = pd.DataFrame([asdict(e) for e in experiments_bench])
    df_base.to_csv('delayed-bound-experiments-bench.csv', index=False)
