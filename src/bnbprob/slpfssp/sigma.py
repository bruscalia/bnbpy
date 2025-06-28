import copy

from bnbprob.slpfssp.job import Job


class Sigma:
    """Base sequence of jobs and partial completion times for machines"""

    jobs: list[Job]
    """Jobs included into sequence (permutation)"""
    C: list[list[int]]
    """Partial completion times for machines of each parallel semiline"""
    m: list[int]
    """Number of machines on each parallel semiline"""

    def __init__(self, jobs: list[Job], C: list[list[int]]):
        """Base sequence of jobs and partial completion times for machines

        Parameters
        ----------
        jobs : list[Job]
            Jobs included into sequence

        C : list[list[int]]
            Partial completion times
        """
        self.jobs = jobs
        self.C = C
        self.m = [len(c) for c in C]

    def __del__(self) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        del self.jobs

    @property
    def cost(self) -> int:
        """Cost of the sequence, i.e. the maximum completion time
        on all machines

        Returns
        -------
        int
            Cost of the sequence
        """
        return max(ci for c in self.C for ci in c)

    def get_cost(self) -> int:
        """Returns the cost of the sequence, i.e. the maximum completion time
        on all machines

        Returns
        -------
        int
            Cost of the sequence
        """
        return self.cost

    def job_to_bottom(self, job: Job) -> None:
        """Inserts job to the last position of sequence
        (assume sequence is a bottom sequence)

        Parameters
        ----------
        job : Job
            New job included
        """
        self.jobs.append(job)
        # Update on each semiline until reconciliation machine
        c_sl = 0  # The earliest release on the reconciliation machine
        for sl, c in enumerate(self.C):
            c[0] = max(c[0], job.r[sl][0]) + job.p[sl][0]
            for k in range(1, self.m[sl] - job.s):
                c[k] = max(c[k], c[k - 1]) + job.p[sl][k]
            c_sl = max(c[k], c_sl)

        # Update on reconciliation machine
        for sl, c in enumerate(self.C):
            c[-job.s] = max(c_sl, job.r[sl][-job.s]) + job.p[sl][-job.s]
            for k in range(self.m[sl] - job.s + 1, self.m[sl]):
                c[k] = max(c[k], c[k - 1]) + job.p[sl][k]

    def job_to_top(self, job: Job) -> None:
        """Inserts job to the first position of sequence
        (assume sequence is a top sequence)

        Parameters
        ----------
        job : Job
            New job included
        """
        self.jobs.insert(0, job)
        # Update on each semiline on reconciliation machines
        c_sl = 0  # The earliest wait time on the reconciliation machine
        for sl, c in enumerate(self.C):
            m_sl = self.m[sl] - 1
            if m_sl == -1:
                continue
            c[m_sl] = max(c[m_sl], job.q[sl][m_sl]) + job.p[sl][m_sl]
            for _ in range(1, job.s):
                m_sl -= 1
                c[m_sl] = max(c[m_sl], c[m_sl + 1]) + job.p[sl][m_sl]
            c_sl = max(c[m_sl], c_sl)

        # Update on parallel semilines
        for sl, c in enumerate(self.C):
            m_sl = self.m[sl] - job.s - 1
            if m_sl == -1:
                continue
            c[m_sl] = max(c_sl, job.q[sl][m_sl]) + job.p[sl][m_sl]
            for _ in range(1, self.m[sl] - job.s):
                m_sl -= 1
                c[m_sl] = max(c[m_sl], c[m_sl + 1]) + job.p[sl][m_sl]

    def copy(self, deep: bool = False) -> 'Sigma':
        if deep:
            return copy.deepcopy(self)
        sigma = Sigma.__new__(Sigma)
        sigma.jobs = self.jobs.copy()
        sigma.C = [c.copy() for c in self.C]
        sigma.m = self.m
        return sigma

    @staticmethod
    def empty_sigma(m: list[int]) -> 'Sigma':
        """Creates an empty `Sigma` instance of `m` machines on
        each parallel semiline

        Parameters
        ----------
        m : list[int]
            Number of machines considered on each parallel semiline

        Returns
        -------
        Sigma
            New sequence
        """
        return empty_sigma(m)


def empty_sigma(m: list[int]) -> Sigma:
    """Creates an empty `Sigma` instance of `m` machines on
    each parallel semiline

    Parameters
    ----------
    m : list[int]
        Number of machines considered on each parallel semiline

    Returns
    -------
    Sigma
        New sequence
    """
    sigma = Sigma.__new__(Sigma)
    sigma.jobs = []
    sigma.C = [[0] * mi for mi in m]
    sigma.m = m
    return sigma
