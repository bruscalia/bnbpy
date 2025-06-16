import pytest

from bnbprob.machdeadline import Job, MachDeadlineProb
from bnbpy import BestFirstBnB, BreadthFirstBnB, DepthFirstBnB


@pytest.mark.machdeadline
class TestMachDeadLine:
    p = [4, 3, 8, 2, 7, 6]
    w = [1, 1, 1, 1, 1, 1]
    dl = [10, 20, 20, 30, 30, 30]
    sol_value = 86
    dfs_nodes = 3
    bfs_nodes = 5
    bb_nodes = 3

    @pytest.fixture
    def problem(self) -> MachDeadlineProb:  # noqa: PLR6301
        jobs = [
            Job(id=j, p=self.p[j], w=self.w[j], dl=self.dl[j])
            for j in range(len(self.p))
        ]
        problem = MachDeadlineProb(jobs)
        return problem

    def test_dfs(self, problem: MachDeadlineProb) -> None:
        bnb = DepthFirstBnB(eval_node='in')
        bnb.solve(problem)
        cost = bnb.solution.cost
        assert (
            bnb.solution.cost == self.sol_value
        ), f'Wrong solution for DFS {cost}, expected {self.sol_value}'
        assert bnb.explored == self.dfs_nodes, (
            f'Wrong number of explored nodes for DFS {bnb.explored},'
            f' expected {self.dfs_nodes}'
        )

    def test_bfs(self, problem: MachDeadlineProb) -> None:
        bnb = BreadthFirstBnB(eval_node='in')
        bnb.solve(problem)
        cost = bnb.solution.cost
        assert (
            bnb.solution.cost == self.sol_value
        ), f'Wrong solution for BFS {cost}, expected {self.sol_value}'
        assert bnb.explored == self.bfs_nodes, (
            f'Wrong number of explored nodes for BFS {bnb.explored},'
            f' expected {self.bfs_nodes}'
        )

    def test_bbs(self, problem: MachDeadlineProb) -> None:
        bnb = BestFirstBnB(eval_node='in')
        bnb.solve(problem)
        cost = bnb.solution.cost
        assert (
            bnb.solution.cost == self.sol_value
        ), f'Wrong solution for lb priority {cost}, expected {self.sol_value}'
        assert bnb.explored == self.bb_nodes, (
            f'Wrong number of explored nodes for lb priority'
            f' {bnb.explored}, expected {self.bb_nodes}'
        )
