import json
import os
from dataclasses import asdict

from bnbprob.machdeadline import LagrangianDeadline, MachineDeadlineInstance

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    num_jobs = [20, 40, 60]

    i = 1
    for nj in num_jobs:
        completed = 0
        target = 30
        j = 0
        while completed < target:
            instance = MachineDeadlineInstance.randomized(nj, seed=j)
            problem = LagrangianDeadline(instance.jobs)
            warmstart = problem.warmstart()
            j += 1
            if warmstart is None:
                continue
            filename = os.path.join(
                HERE,
                f'n{nj}_{str(i).zfill(3)}.json',
            )
            with open(filename, mode='w', encoding='utf-8') as f:
                json.dump(asdict(instance), f, indent=4)
            i += 1
            completed += 1


if __name__ == '__main__':
    main()
