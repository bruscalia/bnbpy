import pytest

from bnbprob.pafssp.machinegraph import CyclicGraphError, MachineGraph

# Test constants
SINGLE_MACHINE = 1
TWO_MACHINES = 2
THREE_MACHINES = 3
FOUR_MACHINES = 4
FIVE_MACHINES = 5
SIX_MACHINES = 6
TEN_MACHINES = 10
ELEVEN_MACHINES = 11
SINK_NODE = 3
NODE_FIVE = 5


@pytest.mark.pafssp
class TestMachineGraph:
    """Test class for MachineGraph functionality."""

    @staticmethod
    def test_single_edge() -> None:
        """Test MachineGraph with a single edge."""
        edges = [(0, 1)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == TWO_MACHINES
        assert graph.prec == [[], [0]]
        assert graph.succ == [[1], []]
        assert graph.topo_order == [0, 1]
        assert graph.rev_topo_order == [1, 0]
        assert graph.descendants == [[1], []]

    @staticmethod
    def test_linear_chain() -> None:
        """Test MachineGraph with a linear chain of machines."""
        edges = [(0, 1), (1, 2), (2, 3)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == FOUR_MACHINES
        assert graph.prec == [[], [0], [1], [2]]
        assert graph.succ == [[1], [2], [3], []]
        assert graph.topo_order == [0, 1, 2, 3]
        assert graph.rev_topo_order == [3, 2, 1, 0]
        # Machine 0 has all downstream as descendants
        assert set(graph.descendants[0]) == {1, 2, 3}
        assert set(graph.descendants[1]) == {2, 3}
        assert set(graph.descendants[2]) == {3}
        assert graph.descendants[3] == []

    @staticmethod
    def test_parallel_branches() -> None:
        """Test MachineGraph with parallel branches."""
        # Machine 0 branches to 1 and 2, both converge to 3
        edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == FOUR_MACHINES
        assert set(graph.prec[0]) == set()
        assert set(graph.prec[1]) == {0}
        assert set(graph.prec[2]) == {0}
        assert set(graph.prec[3]) == {1, 2}
        assert set(graph.succ[0]) == {1, 2}
        assert set(graph.succ[1]) == {3}
        assert set(graph.succ[2]) == {3}
        assert set(graph.succ[3]) == set()
        # Check descendants
        assert set(graph.descendants[0]) == {1, 2, 3}
        assert set(graph.descendants[1]) == {3}
        assert set(graph.descendants[2]) == {3}
        assert graph.descendants[3] == []

    @staticmethod
    def test_complex_dag() -> None:
        """Test MachineGraph with a more complex DAG structure."""
        # More complex precedence: 0->1, 0->2, 1->3, 2->3, 2->4, 3->4
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (3, 4)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == FIVE_MACHINES
        assert set(graph.prec[0]) == set()
        assert set(graph.prec[1]) == {0}
        assert set(graph.prec[2]) == {0}
        assert set(graph.prec[3]) == {1, 2}
        assert set(graph.prec[4]) == {2, 3}
        # Check topological order is valid (all prec come before node)
        topo_positions = {
            node: idx for idx, node in enumerate(graph.topo_order)
        }
        for node in range(graph.M):
            for pred in graph.prec[node]:
                assert topo_positions[pred] < topo_positions[node]

    @staticmethod
    def test_multiple_roots() -> None:
        """Test MachineGraph with multiple root nodes."""
        # Two separate chains: 0->1, 2->3
        edges = [(0, 1), (2, 3)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == FOUR_MACHINES
        assert set(graph.prec[0]) == set()
        assert set(graph.prec[1]) == {0}
        assert set(graph.prec[2]) == set()
        assert set(graph.prec[3]) == {2}
        assert set(graph.descendants[0]) == {1}
        assert graph.descendants[1] == []
        assert set(graph.descendants[2]) == {3}
        assert graph.descendants[3] == []

    @staticmethod
    def test_reverse_topological_order() -> None:
        """Test that reverse topological order is correct."""
        edges = [(0, 1), (1, 2)]
        graph = MachineGraph.from_edges(edges)

        assert graph.topo_order == [0, 1, 2]
        assert graph.rev_topo_order == [2, 1, 0]
        # Verify it's actually reversed
        assert graph.rev_topo_order == list(reversed(graph.topo_order))

    @staticmethod
    def test_simple_cycle_detection() -> None:
        """Test that a simple cycle is detected."""
        # Self-loop
        edges = [(0, 0)]
        with pytest.raises(CyclicGraphError) as exc_info:
            MachineGraph.from_edges(edges)
        assert 'cycle' in str(exc_info.value).lower()

    @staticmethod
    def test_two_node_cycle() -> None:
        """Test that a two-node cycle is detected."""
        edges = [(0, 1), (1, 0)]
        with pytest.raises(CyclicGraphError) as exc_info:
            MachineGraph.from_edges(edges)
        assert 'cycle' in str(exc_info.value).lower()

    @staticmethod
    def test_complex_cycle() -> None:
        """Test that a cycle in a larger graph is detected."""
        # Valid edges plus a cycle: 0->1->2->3->1 (cycle)
        edges = [(0, 1), (1, 2), (2, 3), (3, 1)]
        with pytest.raises(CyclicGraphError) as exc_info:
            MachineGraph.from_edges(edges)
        assert 'cycle' in str(exc_info.value).lower()

    @staticmethod
    def test_empty_graph() -> None:
        """Test behavior with empty edge list."""
        edges: list[tuple[int, int]] = []
        graph = MachineGraph.from_edges(edges)

        # Empty graph should have 0 machines
        assert graph.M == 0
        assert graph.prec == []
        assert graph.succ == []
        assert graph.topo_order == []
        assert graph.rev_topo_order == []
        assert graph.descendants == []

    @staticmethod
    def test_non_consecutive_nodes() -> None:
        """Test graph with non-consecutive node numbers."""
        # Nodes 0, 2, 5 (gaps in numbering)
        edges = [(0, 2), (2, 5)]
        graph = MachineGraph.from_edges(edges)

        # M should be max(nodes) + 1 = 6
        assert graph.M == SIX_MACHINES
        # Nodes 1, 3, 4 have no predecessors or successors
        assert graph.prec[1] == []
        assert graph.succ[1] == []
        assert graph.prec[3] == []
        assert graph.succ[3] == []
        assert graph.prec[4] == []
        assert graph.succ[4] == []
        # Check valid nodes
        assert graph.prec[2] == [0]
        assert graph.succ[0] == [2]
        assert graph.prec[5] == [2]
        assert graph.succ[2] == [5]

    @staticmethod
    def test_descendants_correctness() -> None:
        """Test that descendants are computed correctly."""
        # Create a tree: 0->1, 0->2, 1->3, 1->4
        edges = [(0, 1), (0, 2), (1, 3), (1, 4)]
        graph = MachineGraph.from_edges(edges)

        # Machine 0 should have all others as descendants
        assert set(graph.descendants[0]) == {1, 2, 3, 4}
        # Machine 1 should have 3 and 4 as descendants
        assert set(graph.descendants[1]) == {3, 4}
        # Machine 2 has no descendants
        assert graph.descendants[2] == []
        # Machines 3 and 4 have no descendants
        assert graph.descendants[3] == []
        assert graph.descendants[4] == []

    @staticmethod
    def test_topological_order_validity() -> None:
        """Test that topological order respects all precedences."""
        edges = [(0, 2), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5)]
        graph = MachineGraph.from_edges(edges)

        # Create position mapping
        position = {
            node: idx for idx, node in enumerate(graph.topo_order)
        }

        # Verify every edge (u, v) has u before v in topological order
        for u, v in edges:
            assert position[u] < position[v], (
                f'Edge ({u}, {v}) violates topological order'
            )

    @staticmethod
    def test_dataclass_properties() -> None:
        """Test that MachineGraph properties are accessible."""
        edges = [(0, 1), (1, 2)]
        graph = MachineGraph.from_edges(edges)

        # Test all properties are accessible
        assert hasattr(graph, 'M')
        assert hasattr(graph, 'prec')
        assert hasattr(graph, 'succ')
        assert hasattr(graph, 'topo_order')
        assert hasattr(graph, 'rev_topo_order')
        assert hasattr(graph, 'descendants')
        # Test they have expected types
        assert isinstance(graph.M, int)
        assert isinstance(graph.prec, list)
        assert isinstance(graph.succ, list)
        assert isinstance(graph.topo_order, list)
        assert isinstance(graph.rev_topo_order, list)
        assert isinstance(graph.descendants, list)


@pytest.mark.pafssp
class TestMachineGraphEdgeCases:
    """Test class for MachineGraph edge cases and special scenarios."""

    @staticmethod
    def test_diamond_structure() -> None:
        """Test diamond-shaped precedence graph."""
        # 0 -> 1, 2 -> 3 (diamond: one source, two middle, one sink)
        edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == FOUR_MACHINES
        assert set(graph.descendants[0]) == {1, 2, 3}
        # Both paths from 0 to 3 should be captured
        assert SINK_NODE in graph.descendants[0]
        assert SINK_NODE in graph.descendants[1]
        assert SINK_NODE in graph.descendants[2]

    @staticmethod
    def test_wide_fan_out() -> None:
        """Test graph with wide fan-out from a single node."""
        # One node feeding into many
        edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == SIX_MACHINES
        assert len(graph.succ[0]) == FIVE_MACHINES
        assert set(graph.succ[0]) == {1, 2, 3, 4, 5}
        for i in range(1, 6):
            assert graph.prec[i] == [0]
            assert graph.succ[i] == []

    @staticmethod
    def test_wide_fan_in() -> None:
        """Test graph with wide fan-in to a single node."""
        # Many nodes feeding into one
        edges = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == SIX_MACHINES
        assert len(graph.prec[NODE_FIVE]) == FIVE_MACHINES
        assert set(graph.prec[NODE_FIVE]) == {0, 1, 2, 3, 4}
        for i in range(5):
            assert graph.prec[i] == []
            assert graph.succ[i] == [NODE_FIVE]

    @staticmethod
    def test_long_chain() -> None:
        """Test very long linear chain."""
        n = TEN_MACHINES
        edges = [(i, i + 1) for i in range(n)]
        graph = MachineGraph.from_edges(edges)

        assert graph.M == ELEVEN_MACHINES
        assert graph.topo_order == list(range(ELEVEN_MACHINES))
        # First node has all others as descendants
        assert len(graph.descendants[0]) == n
        # Last node has no descendants
        assert graph.descendants[n] == []
