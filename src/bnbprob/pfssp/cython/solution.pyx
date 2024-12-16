# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

import copy

from bnbprob.pfssp.cython.permutation cimport Permutation
from bnbpy import Solution


class FlowSolution(Solution):

    perm: Permutation

    def __init__(self, perm: Permutation):
        super().__init__(0)
        self.perm = perm

    def __del__(self):
        del self.perm
        self.perm = None

    @property
    def sequence(self):
        return self.perm.sequence

    @property
    def free_jobs(self):
        return self.perm.free_jobs

    def is_feasible(self):
        return self.perm.is_feasible()

    def calc_lb_1m(self):
        return self.perm.calc_lb_1m()

    def calc_lb_2m(self):
        return self.perm.calc_lb_2m()

    def lower_bound_1m(self):
        return self.perm.lower_bound_1m()

    def lower_bound_2m(self):
        return self.perm.lower_bound_1m()

    def push_job(self, j: int):
        self.perm.push_job(j)

    def copy(self):
        other = copy.copy(self)
        other.perm = self.perm.copy()
        return other
