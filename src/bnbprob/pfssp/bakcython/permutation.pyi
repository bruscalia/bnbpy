from bnbprob.pfssp.cython.job import Job
from bnbprob.pfssp.cython.sequence import Sigma

class Permutation:

    m: int
    free_jobs: list[Job]
    sigma1: Sigma
    sigma2: Sigma
    level: int

    def __init__(
        self,
        m: int,
        free_jobs: list[Job],
        sigma1: Sigma,
        sigma2: Sigma,
        level: int = 0
    ):
        ...

    def cleanup(self):
        ...

    @staticmethod
    def from_p(p: list[list[int]]):
        ...

    @property
    def sequence(self) -> list[Job]:
        """Sequence of jobs in current solution"""
        ...

    @property
    def n_jobs(self):
        ...

    @property
    def n_free(self):
        ...

    def push_job(self, j: int) -> None:
        ...

    def update_params(self) -> None:
        ...

    def front_updates(self) -> None:
        ...

    def back_updates(self) -> None:
        ...

    def calc_lb_1m(self) -> int:
        ...

    def calc_lb_2m(self) -> int:
        ...

    def calc_lb_full(self) -> int:
        ...

    def compute_starts(self) -> None:
        ...

    def lower_bound_1m(self) -> int:
        ...

    def lower_bound_2m(self) -> int:
        ...
