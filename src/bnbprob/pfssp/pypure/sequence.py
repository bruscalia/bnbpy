import copy

from bnbprob.pfssp.pypure.job import Job


class Sigma:
    """Base sequence of jobs and partial completion times for machines"""

    def __init__(self, jobs: list[Job], C: list[int]):
        """Base sequence of jobs and partial completion times for machines

        Parameters
        ----------
        jobs : list[Job]
            Jobs included into sequence

        C : list[int]
            Partial completion times
        """
        self.jobs = jobs
        self.C = C
        self.m = len(self.C)

    def __del__(self):
        self.cleanup()

    def cleanup(self) -> None:
        for job in self.jobs:
            del job
        del self.jobs

    def job_to_bottom(self, job: Job) -> None:
        """Inserts job to the last position of sequence
        (assume sequence is a bottom sequence)

        Parameters
        ----------
        job : Job
            New job included
        """
        self.jobs.append(job)
        # Update
        self.C[0] = max(self.C[0], job.r[0]) + job.p[0]
        for k in range(1, self.m):
            self.C[k] = max(self.C[k], self.C[k - 1]) + job.p[k]

    def job_to_top(self, job: Job) -> None:
        """Inserts job to the first position of sequence
        (assume sequence is a top sequence)

        Parameters
        ----------
        job : Job
            New job included
        """
        self.jobs.insert(0, job)
        # Update
        m = self.m - 1
        if m == -1:
            return

        self.C[m] = max(self.C[m], job.q[m]) + job.p[m]
        if m == 0:
            return

        for k in range(1, m + 1):
            self.C[m - k] = (
                max(self.C[m - k], self.C[m - k + 1]) + job.p[m - k]
            )

    def copy(self, deep=False) -> 'Sigma':
        if deep:
            return copy.deepcopy(self)
        sigma = Sigma.__new__(Sigma)
        sigma.jobs = self.jobs.copy()
        sigma.C = self.C.copy()
        sigma.m = self.m
        return sigma

    @staticmethod
    def empty_sigma(m: int) -> 'Sigma':
        """Creates an empty `Sigma` instance of `m` machines

        Parameters
        ----------
        m : int
            Number of machines considered

        Returns
        -------
        Sigma
            New sequence
        """
        return empty_sigma(m)


def empty_sigma(m: int) -> Sigma:
    """Creates an empty `Sigma` instance of `m` machines

    Parameters
    ----------
    m : int
        Number of machines considered

    Returns
    -------
    Sigma
        New sequence
    """
    sigma = Sigma.__new__(Sigma)
    sigma.jobs = []
    sigma.C = [0] * m
    sigma.m = m
    return sigma
