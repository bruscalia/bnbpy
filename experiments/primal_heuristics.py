import gc
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, cast

import pandas as pd

from bnbprob.pafssp import CallbackBnB, LazyBnB
from bnbprob.pafssp.cython.problem import PermFlowShop
from bnbpy import configure_logfile

configure_logfile('primal-heur-experiments.log', mode='w')


class MultistartFlowShop(PermFlowShop):
    def warmstart(self) -> 'MultistartFlowShop':
        return cast(
            MultistartFlowShop, super().randomized_heur(n_iter=200, seed=42)
        )


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
    # {'name': 'ta017', 'optimal': True, 'value': 1484},
    {'name': 'ta018', 'optimal': True, 'value': 1538},
    {'name': 'ta019', 'optimal': True, 'value': 1593},
    {'name': 'ta020', 'optimal': True, 'value': 1591},
]

experiment_data = [ExperimentData(**d) for d in data_ritt]


@dataclass
class Experiment:
    name: str
    execution_time: float
    upper_bound: float
    lower_bound: float
    gap: float
    status: str
    nodes: int


BnbType = type[CallbackBnB] | type[LazyBnB]
FlowType = type[PermFlowShop] | type[MultistartFlowShop]


def run_experiment(  # noqa: PLR0913, PLR0917
    name: str,
    p: list[list[int]],
    bnb_cls: BnbType,
    timelimit: int = 3600,
) -> Experiment:
    # Initialization
    problem = PermFlowShop.from_p(p, constructive='neh')
    bnb = bnb_cls(delay_lb5=True)
    # Solve
    start_time = time.time()
    sol = bnb.solve(problem, maxiter=1000_000_000, timelimit=timelimit)
    execution_time = time.time() - start_time
    # Results
    experiment = Experiment(
        name,
        execution_time,
        sol.cost,
        sol.lb,
        bnb.gap,
        str(sol.status),
        bnb.explored,
    )
    gc.collect()
    time.sleep(0.2)
    return experiment


if __name__ == '__main__':
    experiments_heur = list[Experiment]()

    # Scan directory for all instances
    for ed in experiment_data:
        with open(
            f'./../data/flow-shop/{ed.name}.json', mode='r', encoding='utf8'
        ) as f:
            p = json.load(f)
        experiment = run_experiment(
            ed.name, p, CallbackBnB, 3600
        )
        experiments_heur.append(experiment)
        print(experiment)

    df_heur = pd.DataFrame([asdict(e) for e in experiments_heur])
    df_heur.to_csv('heur-experiments.csv', index=False)

    experiments_bench = list[Experiment]()

    # Scan directory for all instances
    for ed in experiment_data:
        with open(
            f'./../data/flow-shop/{ed.name}.json', mode='r', encoding='utf8'
        ) as f:
            p = json.load(f)
        experiment = run_experiment(
            ed.name, p, LazyBnB, 3600
        )
        experiments_bench.append(experiment)
        print(experiment)

    df_base = pd.DataFrame([asdict(e) for e in experiments_bench])
    df_base.to_csv('no-heur-experiments.csv', index=False)
