from dataclasses import field

from pydantic.dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Job:
    id: int
    """Job unique identifier"""
    p: int
    """Job processing time"""
    w: int
    """Job weight in objective function"""
    d: int
    """Job deadline"""
    pri: float = field(init=False, repr=False)
    """Job priority, calculated as w/p"""

    def __post_init__(self) -> None:
        object.__setattr__(self, 'pri', self.w / self.p)

    @property
    def _signature(self) -> str:
        return f'Job({self.id})'

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    def __lt__(self, other: 'Job') -> bool:
        return self.pri < other.pri
