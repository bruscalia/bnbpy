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

    @property
    def _signature(self) -> str:
        return f'Job({self.id})'

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    def __lt__(self, other: 'Job') -> bool:
        return self.id > other.id
