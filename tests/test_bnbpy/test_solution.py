import pytest

from bnbpy.solution import Solution
from bnbpy.status import OptStatus


@pytest.mark.solution
class TestSolution:
    lb_value = 100
    cost_value = 200
    copy_value = 400

    @staticmethod
    def test_initial_state():
        """Test the initial state of the Solution instance."""
        sol = Solution()
        assert sol.cost == float('inf')
        assert sol.lb == -float('inf')
        assert sol.status == OptStatus.NO_SOLUTION
        assert (str(sol)) == 'Status: NO_SOLUTION | Cost: inf | LB: -inf'

    @staticmethod
    def test_set_optimal():
        """Test setting the status to OPTIMAL."""
        sol = Solution()
        sol.set_optimal()
        assert sol.status == OptStatus.OPTIMAL

    def test_set_lb(self):
        """Test setting a lower bound (lb) and checking status."""
        sol = Solution()
        sol.set_lb(self.lb_value)
        assert sol.lb == self.lb_value
        assert sol.status == OptStatus.RELAXATION

    def test_set_feasible(self):
        """Test setting the status to FEASIBLE and ensuring cost is set to lb."""
        sol = Solution()
        sol.set_lb(self.cost_value)
        sol.set_feasible()
        assert sol.status == OptStatus.FEASIBLE
        assert sol.cost == self.cost_value

    @staticmethod
    def test_set_infeasible():
        """Test setting the status to INFEASIBLE and ensuring cost is reset."""
        sol = Solution()
        sol.set_lb(300)
        sol.set_infeasible()
        assert sol.status == OptStatus.INFEASIBLE
        assert sol.cost == float('inf')

    def test_copy(self):
        """Test copying functionality."""
        sol = Solution()
        sol.set_lb(self.copy_value)
        shallow_copy = sol.copy(deep=False)
        deep_copy = sol.copy(deep=True)

        assert shallow_copy.lb == self.copy_value
        assert deep_copy.lb == self.copy_value
        assert shallow_copy is not sol
        assert deep_copy is not sol
        assert shallow_copy.status == sol.status
        assert deep_copy.status == sol.status
