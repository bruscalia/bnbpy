from dataclasses import dataclass

from ortools.sat.python import cp_model


@dataclass
class CPJob:
    j: int
    p: list[int]
    r: list[int] = None
    starts: list[cp_model.IntVar] = None
    ends: list[cp_model.IntVar] = None
    intervals: list[cp_model.IntervalVar] = None


@dataclass
class CPFlowShop:
    model: cp_model.CpModel
    jobs: dict[int, CPJob]
    machines: list[int]
    makespan: cp_model.IntVar


@dataclass
class CPResults:
    makespan: int
    sequence: list[CPJob]
