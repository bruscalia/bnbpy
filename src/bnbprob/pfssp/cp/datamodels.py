from dataclasses import dataclass, field

from ortools.sat.python import cp_model


@dataclass
class CPJob:
    j: int
    p: list[int]
    r: list[int] = field(default_factory=list)
    starts: list[cp_model.IntVar] = field(default_factory=list)
    ends: list[cp_model.IntVar] = field(default_factory=list)
    intervals: list[cp_model.IntervalVar] = field(default_factory=list)


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
