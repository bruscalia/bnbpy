"""Explicit random trees with known optimum for end-to-end tests."""

import random
from dataclasses import dataclass

from bnbpy import Node, Problem

INF = float('inf')
FEASIBLE_LEAF_PROB = 0.5


@dataclass
class Tree:
    """Explicit tree: bounds are non-decreasing from parents to children,
    and only leaves can be feasible (their cost is their bound)."""

    bound: list[float]
    feasible: list[bool]
    children: list[list[int]]

    @property
    def optimum(self) -> float:
        costs = [b for b, f in zip(self.bound, self.feasible) if f]
        return min(costs, default=INF)


def random_tree(seed: int, max_depth: int = 4) -> Tree:
    rng = random.Random(seed)
    tree = Tree([float(rng.randint(0, 3))], [False], [[]])
    stack = [(0, 0)]
    while stack:
        idx, depth = stack.pop()
        n_children = rng.randint(0, 3) if depth < max_depth else 0
        if n_children == 0:
            tree.feasible[idx] = rng.random() < FEASIBLE_LEAF_PROB
            continue
        for _ in range(n_children):
            child = len(tree.bound)
            # Integer increments produce ties, to exercise tie-breaking
            tree.bound.append(tree.bound[idx] + rng.randint(0, 3))
            tree.feasible.append(False)
            tree.children.append([])
            tree.children[idx].append(child)
            stack.append((child, depth + 1))
    return tree


class TreeProblem(Problem):
    def __init__(self, tree: Tree, idx: int = 0) -> None:
        super().__init__()
        self.tree = tree
        self.idx = idx

    def calc_bound(self) -> float:
        return self.tree.bound[self.idx]

    def is_feasible(self) -> bool:
        return self.tree.feasible[self.idx]

    def branch(self) -> list['TreeProblem']:
        children = self.tree.children[self.idx]
        return [TreeProblem(self.tree, c) for c in children]


def small_tree(feasible: bool = True) -> Tree:
    """root(0) -> a(1), b(2); a -> c(3, feasible cost 2), d(4, cost 3);
    b -> e(5, cost 4). Only leaves may be feasible."""
    return Tree(
        bound=[0.0, 1.0, 1.0, 2.0, 3.0, 4.0],
        feasible=[False, False, False, feasible, feasible, feasible],
        children=[[1, 2], [3, 4], [5], [], [], []],
    )


def walk(node: Node[TreeProblem]) -> list[Node[TreeProblem]]:
    nodes = [node]
    for child in node.children or []:
        assert child.parent is node
        nodes.extend(walk(child))
    return nodes
