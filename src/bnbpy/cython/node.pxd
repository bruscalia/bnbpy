# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import copy
import itertools
from typing import List, Optional, Union

from bnbpy.problem import Problem
from bnbpy.solution import Solution


cdef class Node:

    cdef public:
        object problem
        Node parent
        int level
        double lb
        list[Node] children
        int _sort_index
        object _counter

    cpdef list[Node] branch(Node self)

    cpdef Node child_problem(Node self, object problem)

    cpdef Node shallow_copy(Node self)
