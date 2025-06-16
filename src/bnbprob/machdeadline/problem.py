import logging
from typing import Dict, Hashable, List, Optional

from bnbprob.machdeadline.job import Job
from bnbprob.machdeadline.solution import MachSolution
from bnbpy import Problem

log = logging.getLogger(__name__)


class MachDeadlineProb(Problem):
    solution: MachSolution
    jobs: Dict[Hashable, Job]
    lb: int
    cost: Optional[int]

    def __init__(self, jobs: List[Job]) -> None:
        self.solution = MachSolution([])
        self.jobs = {job.id: job for job in jobs}

    def calc_bound(self) -> int:
        fixed = self.get_fixed()
        unfixed = self.get_unfixed()
        self.find_wspt(unfixed)
        fixed.sort(
            key=lambda job: job.k if job.k is not None else -1, reverse=False
        )
        self.solution = MachSolution(unfixed + fixed)
        return self.solution.calc_bound()

    def is_feasible(self) -> bool:
        return self.solution.check_feasible()

    def branch(self) -> Optional[List['MachDeadlineProb']]:
        # Get fixed and unfixed job lists to create new solution
        fixed_jobs = self.get_fixed()
        unfixed_jobs = self.get_unfixed()
        if len(unfixed_jobs) == 0:
            return None
        # Find next position to fix and iterate creating children
        next_k = self._find_next_pos(fixed_jobs, unfixed_jobs)
        children = []
        unfixed_makespan = sum(job.p for job in unfixed_jobs)
        for job in unfixed_jobs:
            feas_check = unfixed_makespan <= job.dl
            if feas_check:
                child = self.copy_to_child()
                child.fix_job(job.id, next_k)
                children.append(child)
        return children

    @staticmethod
    def _find_next_pos(fixed_jobs: List[Job], unfixed_jobs: List[Job]) -> int:
        if len(fixed_jobs) == 0:
            next_k = len(unfixed_jobs) - 1
        else:
            next_k = min(job.k for job in fixed_jobs if job.k is not None) - 1
        return next_k

    def fix_job(self, j: Hashable, k: int) -> None:
        job = self.jobs[j]
        job.set_position(k)
        job.fix()

    def unfix_job(self, j: int) -> None:
        self.jobs[j].unfix()

    def get_fixed(self) -> List[Job]:
        return [job for job in self.jobs.values() if job.fixed]

    def get_unfixed(self) -> List[Job]:
        return [job for job in self.jobs.values() if not job.fixed]

    def copy_to_child(self) -> 'MachDeadlineProb':
        child = MachDeadlineProb(self.jobs_to_copy_list())
        return child

    def jobs_to_copy_list(self) -> List[Job]:
        return [job.model_copy() for job in self.jobs.values()]

    @staticmethod
    def find_wspt(jobs: List[Job]) -> None:
        jobs.sort(key=lambda job: job.w / job.p, reverse=True)
