import json
from typing import Hashable, Optional

from pydantic import BaseModel


class Job(BaseModel):
    id: Hashable
    """Job unique identifier"""
    p: int
    """Job processing time"""
    w: int
    """Job weight in objective function"""
    dl: int
    """Job deadline"""
    fixed: bool = False
    """If job is fixed in the current solution"""
    k: Optional[int] = None
    """Position of the job in the sequence."""
    c: Optional[int] = None
    """Completion time of the job."""

    @property
    def feasible(self):
        if self.c is None:
            return None
        return self.c <= self.dl

    @property
    def _signature(self):
        j = self.model_dump(include=["id", "c"])
        return json.dumps(
            j,
            indent=4
        )

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    def set_position(self, k: int):
        self.k = k

    def set_completion(self, c: int):
        self.c = c

    def fix(self):
        self.fixed = True

    def unfix(self):
        self.fixed = False
