import random

from pydantic.dataclasses import dataclass

from bnbprob.machdeadline.job import Job

_L_values = [round(0.6 + 0.1 * i, 1) for i in range(5)]
_R_values = [round(0.2 + 0.2 * i, 1) for i in range(8)]


@dataclass(slots=True, frozen=True)
class MetaData:
    L: float
    R: float
    P: int
    deadline_range: tuple[int, int]


@dataclass(slots=True, frozen=True)
class MachineDeadlineInstance:
    jobs: list[Job]
    """List of jobs to schedule"""
    meta: MetaData
    """Metadata for the instance"""

    @staticmethod
    def randomized(
        n: int,
        seed: int | None = None,
        L: float | None = None,
        R: float | None = None,
    ) -> 'MachineDeadlineInstance':
        """Generates random instance according to procedures
        described in Potts & Van Wassenhove (1983).

        Parameters
        ----------
        n : int
            Number of jobs in the instance

        seed : int | None, optional
            Random seed for reproducibility, by default None

        L : float | None, optional
            Lower bound for the deadline range, by default None

        R : float | None, optional
            Range for the deadline, by default None

        Returns
        -------
        MachineDeadlineInstance
            Randomly generated machine deadline instance
        """
        return _generate_jobs_from_paper(n, seed, L, R)


def _generate_jobs_from_paper(
    n: int, seed: int | None, L: float | None = None, R: float | None = None
) -> MachineDeadlineInstance:
    """
    Generate a single-machine instance following the paper's setup.

    - p_i ~ U{1, 100}
    - w_i ~ U{1, 10}
    - d_i ~ U{P(L - R/2), P(L + R/2)} where P = sum(p_i)
    - If L or R is not provided, sample from the paper's tested grids.

    @article{POTTS1983379,
        title = {An algorithm for single machine sequencing
        with deadlines to minimize total weighted completion time},
        journal = {European Journal of Operational Research},
        volume = {12},
        number = {4},
        pages = {379-387},
        year = {1983},
        issn = {0377-2217},
        doi = {https://doi.org/10.1016/0377-2217(83)90159-5},
        url = {https://www.sciencedirect.com/science/article/pii/0377221783901595},
        author = {C.N. Potts and L.N. {Van Wassenhove}},
    }
    """
    rng = random.Random(seed)

    if L is None:
        L = rng.choice(_L_values)
    if R is None:
        R = rng.choice(_R_values)

    p = [rng.randint(1, 100) for _ in range(n)]
    w = [rng.randint(1, 10) for _ in range(n)]

    P = sum(p)
    d_low = int(P * (L - R / 2))
    d_high = int(P * (L + R / 2))

    d_low = max(1, d_low)
    d_high = max(d_low, d_high)

    d = [rng.randint(d_low, d_high) for _ in range(n)]

    jobs = [Job(j, p[j], w[j], d[j]) for j in range(n)]
    meta = MetaData(L, R, P, (d_low, d_high))
    return MachineDeadlineInstance(jobs=jobs, meta=meta)
