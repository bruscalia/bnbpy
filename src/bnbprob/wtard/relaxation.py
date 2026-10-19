"""
Transportation relaxation lower bound for 1 || sum w_j T_j
(Pinedo, 2008, Section 3.6).

Each job j is split into p_j unit jobs and each unit is assigned to one of
the slots 1..T, T being the total processing time of the jobs. A unit of
job j assigned to slot k costs

    c_jk = 0,    if k <= d_j
    c_jk = w_j,  if k > d_j

so the relaxation maximizes the total weight of units completed on time
(early units), and its cost is the weighted number of late units.

Every early unit of job j must be assigned to a slot in [1, min(d_j, T)],
so the constraints are nested intervals sharing their left end. A set of
early units is therefore feasible if and only if, for every due date D,
at most D units have due date <= D. These sets form a matroid and the
optimal solution can be obtained in O(n log n) without enumerating slots:
jobs are scanned by nondecreasing due date while keeping the early units
in a min-heap by weight, and whenever the capacity of the current due
date is exceeded the lightest units become late.
"""

from heapq import heappop, heappush, heapreplace
from typing import Sequence

from .state import Job


def preemptive_bound(jobs: Sequence[Job], horizon: int) -> int:
    """Solves the transportation relaxation of a set of jobs processed
    in the interval [0, horizon].

    Parameters
    ----------
    jobs : Sequence[Job]
        Jobs sorted by nondecreasing due date. Due dates must be
        non-negative.

    horizon : int
        Total processing time of the jobs.

    Returns
    -------
    int
        Total weight of the late units, a lower bound for the
        total weighted tardiness of the jobs.
    """
    early: list[tuple[int, int]] = []  # (weight, units) min-heap
    load = 0
    cost = 0
    for job in jobs:
        heappush(early, (job.w, job.p))
        load += job.p
        excess = load - min(job.d, horizon)
        if excess <= 0:
            continue
        load -= excess
        while excess > 0:
            w, units = early[0]
            if units <= excess:
                heappop(early)
                cost += w * units
                excess -= units
            else:
                heapreplace(early, (w, units - excess))
                cost += w * excess
                excess = 0
    return cost
