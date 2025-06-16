from typing import Optional, Union

import numpy as np

K = 0.5


class CoverNode:
    index: int
    sets: set['CoverNodeSet']
    covered: bool

    def __init__(
        self,
        index: int,
        cover_sets: Optional[set['CoverNodeSet']] = None,
        covered: bool = False,
    ):
        self.index = index
        if cover_sets is None:
            cover_sets = set()
        self.cover_sets = cover_sets
        self.covered = covered

    def add_set(self, cover_set: 'CoverNodeSet') -> None:
        self.cover_sets.add(cover_set)

    def cover(self) -> None:
        if not self.covered:
            for cover_set in self.cover_sets:
                cover_set.cost -= 1


class CoverNodeSet:
    index: int
    weight: Union[float, int]
    nodes: set[CoverNode]
    cost: int

    def __init__(
        self,
        index: int,
        weight: Union[int, float] = 1,
        nodes: Optional[set[CoverNode]] = None,
    ):
        self.index = index
        self.weight = weight
        if nodes is None:
            nodes = set()
        self.nodes = set()
        self.cost = 0
        for node in nodes:
            self.add_node(node)

    def __repr__(self) -> str:
        return f'S({self.index})'

    def __str__(self) -> str:
        return f'S({self.index})'

    @property
    def priority(self) -> float:
        return self.weight * (self.cost + 1)

    def add_node(self, node: CoverNode) -> None:
        self.nodes.add(node)
        node.add_set(self)
        if not node.covered:
            self.cost += 1

    def select(self) -> None:
        for node in self.nodes:
            node.cover()

    def clean(self) -> None:
        for node in self.nodes:
            node.covered = False
        self.cost = len(self.nodes)


class SetCover:
    nodes: dict[int, CoverNode]
    cover_sets: list[CoverNodeSet]
    queue: list[CoverNodeSet]
    sol: set[CoverNodeSet]

    def __init__(self) -> None:
        self.nodes = {}
        self.cover_sets = []
        self.queue = []
        self.sol = set()

    def add_set(
        self, new_set: set[int], new_weight: Union[float, int] = 1
    ) -> None:
        index = len(self.cover_sets)
        cover_set = CoverNodeSet(index, weight=new_weight)
        for i in new_set:
            if i not in self.nodes:
                self.nodes[i] = CoverNode(i)
            node = self.nodes[i]
            cover_set.add_node(node)
        self.cover_sets.append(cover_set)

    def add_matrix(self, A: np.ndarray, c: np.ndarray) -> None:
        new_sets = [
            set(np.nonzero(A[:, j] >= K)[0].tolist())
            for j in range(A.shape[1])
        ]
        for j, new_set in enumerate(new_sets):
            self.add_set(new_set, c[j])

    def add_array(self, a: np.ndarray, c: Union[float, int]) -> None:
        new_set = set(np.nonzero(a >= K)[0].tolist())
        self.add_set(new_set, c)

    def clean(self) -> None:
        for cover_set in self.cover_sets:
            cover_set.clean()


class SetCoverHeur:
    queue: list[CoverNodeSet]
    sol: set[CoverNodeSet]

    def __init__(self) -> None:
        self.queue = []
        self.sol = set()

    def solve(self, set_cover: SetCover) -> set[CoverNodeSet]:
        set_cover.clean()
        self.queue = list(set_cover.cover_sets)
        self.sol = set()
        while len(self.queue) > 0:
            s = self.dequeue()
            if s.cost > 0:
                s.select()
                self.sol.add(s)
        return self.sol

    def dequeue(self) -> CoverNodeSet:
        s = max(self.queue, key=lambda x: x.priority)
        self.queue.remove(s)
        return s
