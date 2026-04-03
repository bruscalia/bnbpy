# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from dataclasses import dataclass
from heapq import heapify, heappop

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.maxclique.node cimport (
    Node,
    c_add_neighbor,
    c_can_color,
    c_set_color,
    c_notify_colored_neighbor,
    c_color_clean,
    c_clean_copy,
    c_pop_max_node,
    c_find_max_sat_node,
    c_find_max_node_degree,
    c_alloc_node,
    c_free_node
)


cdef class NodeWrapper:

    def __init__(self, int index, int color, list[int] neighbors):
        self.index = index
        self.color = color
        self.neighbors = neighbors

    def __repr__(self):
        return f"N({self.index})"


cdef NodeWrapper wrap_node(Node* node):
    cdef:
        size_t j
        list[int] neighbor_indices
        NodeWrapper wrapper

    neighbor_indices = [None] * node.neighbors.size()
    for j in range(node.neighbors.size()):
        neighbor_indices[j] = node.neighbors[j].index

    wrapper = NodeWrapper.__new__(NodeWrapper)
    wrapper.index = node.index
    wrapper.color = node.color
    wrapper.neighbors = neighbor_indices
    return wrapper


cdef class Graph:

    def __init__(self, int size) -> None:
        self._size = size
        self._active_size = 0

    def __del__(self) -> None:
        cdef size_t i
        for i in range(self._nodes.size()):
            c_free_node(self._nodes[i])
        self._nodes.clear()

    @classmethod
    def from_edges(cls, edges: list[tuple[int, int]]) -> 'Graph':
        cdef:
            Graph graph
            int i, j, max_index, idx
            tuple[int, int] e

        max_index = -1
        for e in edges:
            i, j = e
            max_index = max(max_index, i, j)

        graph = Graph.__new__(Graph)
        graph._size = max_index + 1
        graph._active_size = graph._size
        graph._nodes.resize(graph._size, NULL)
        graph._active_nodes.reserve(graph._size)

        # Initialize all nodes
        for idx in range(graph._size):
            graph._nodes[idx] = c_alloc_node(idx)
            graph._active_nodes.push_back(graph._nodes[idx])

        # Add edges
        for e in edges:
            i, j = e
            c_add_neighbor(graph._nodes[i][0], graph._nodes[j][0])
            c_add_neighbor(graph._nodes[j][0], graph._nodes[i][0])

        # Sort by degree
        sort_nodes_by_degree(graph._active_nodes)

        return graph

    @property
    def nodes(self) -> list[NodeWrapper]:
        cdef:
            size_t i
            list[NodeWrapper] node_wrappers

        node_wrappers = [None] * self._active_nodes.size()
        for i in range(self._active_nodes.size()):
            if self._active_nodes[i] != NULL:
                node_wrappers[i] = wrap_node(self._active_nodes[i])
        return node_wrappers

    @property
    def node_map(self) -> dict[int, NodeWrapper]:
        cdef:
            size_t i
            dict[int, NodeWrapper] node_map

        node_map = {}
        for i in range(self._active_nodes.size()):
            if self._active_nodes[i] != NULL:
                node_map[i] = wrap_node(self._active_nodes[i])
        return node_map

    @property
    def num_nodes(self) -> int:
        return self._active_size

    @property
    def active_ratio(self) -> float:
        if self._size == 0:
            return 0.0
        return (<float>self._active_size) / self._size

    def are_neighbors(self, int i, int j) -> bool:
        cdef:
            size_t k
            Node* node_i
            Node* neighbor

        node_i = self._nodes[i]
        for k in range(node_i.neighbors.size()):
            neighbor = node_i.neighbors[k]
            if neighbor.index == j:
                return True
        return False

    cpdef NodeWrapper next_node(self):
        cdef:
            Node* node

        node = self._active_nodes.back()
        return wrap_node(node)

    cpdef int next_index(self):
        cdef:
            Node* node

        node = self._active_nodes.back()
        return node.index

    cpdef Graph copy_remove(self, int node_idx):
        """Create a copy of the graph with node at node_idx removed."""
        cdef:
            Graph other
            Node* old_node
            Node* new_node
            Node* old_neighbor
            Node* new_neighbor
            size_t i, j
            bool is_neighbor

        other = Graph.__new__(Graph)
        other._size = self._size
        other._nodes.resize(self._size, NULL)
        other._active_nodes.reserve(self._active_size - 1)

        # Create clean copies of all nodes except the removed one
        for i in range(self._active_size):
            old_node = self._active_nodes[i]
            if old_node.index == node_idx:
                continue
            new_node = c_clean_copy(old_node[0])
            other._nodes[old_node.index] = new_node
            other._active_nodes.push_back(new_node)

        other._active_size = other._active_nodes.size()

        # Rebuild edges (excluding connections to removed node)
        for i in range(other._active_size):
            new_node = other._active_nodes[i]
            old_node = self._nodes[new_node.index]

            # Skip current removed
            if old_node.index == node_idx:
                continue

            for j in range(old_node.neighbors.size()):
                old_neighbor = old_node.neighbors[j]
                # Skip the removed node and already processed neighbors
                if old_neighbor.index < new_node.index:
                    continue
                if other._nodes[old_neighbor.index] != NULL:
                    new_neighbor = other._nodes[old_neighbor.index]
                    c_add_neighbor(new_node[0], new_neighbor[0])
                    c_add_neighbor(new_neighbor[0], new_node[0])

        return other

    cpdef Graph copy_branch(self, int node_idx):
        """Create a subgraph containing only the neighbors of the reference node."""
        cdef:
            Graph other
            Node* reference
            Node* old_node
            Node* new_node
            Node* old_neighbor
            Node* new_neighbor
            size_t i, j

        reference = self._nodes[node_idx]

        other = Graph.__new__(Graph)
        other._size = self._size
        other._nodes.resize(self._size, NULL)
        other._active_nodes.reserve(reference.neighbors.size())

        # Create clean copies of the reference node's neighbors
        for i in range(reference.neighbors.size()):
            old_node = reference.neighbors[i]
            new_node = c_clean_copy(old_node[0])
            other._nodes[old_node.index] = new_node
            other._active_nodes.push_back(new_node)

        other._active_size = other._active_nodes.size()

        # Rebuild edges between neighbors (excluding reference node)
        for i in range(reference.neighbors.size()):
            old_node = reference.neighbors[i]
            new_node = other._nodes[old_node.index]

            for j in range(old_node.neighbors.size()):
                old_neighbor = old_node.neighbors[j]
                # Skip the reference node and already processed neighbors
                if old_neighbor.index == node_idx or old_neighbor.index < old_node.index:
                    continue
                if other._nodes[old_neighbor.index] != NULL:
                    new_neighbor = other._nodes[old_neighbor.index]
                    c_add_neighbor(new_node[0], new_neighbor[0])
                    c_add_neighbor(new_neighbor[0], new_node[0])

        return other


cdef class DSatur:

    def __init__(self, graph: Graph):
        self._G = graph
        self._num_colors = 0
        self._max_saturation = 0


    cdef int _find_next_color(self, Node* node):
        cdef:
            int next_color

        next_color = node[0].color
        if next_color >= self._num_colors:
            self._num_colors = next_color + 1
        return next_color

    cpdef void solve(self):
        cdef:
            Node* node
            int next_color, i
            vector[Node*] Q, nodes

        # Copy all active nodes to the queue
        nodes = self._G.get_nodes()
        Q = nodes

        while Q.size() > 0:
            node = c_pop_max_node(Q)
            next_color = self._find_next_color(node)
            c_set_color(node[0], next_color)

        for i in range(nodes.size()):
            node = nodes[i]
            self._max_saturation = max(
                self._max_saturation, node.colored_degree
            )

    cpdef void resolve(self):
        cdef:
            Node* node
            int next_color, i
            vector[Node*] Q, nodes

        # Copy all active nodes to the queue
        nodes = self._G.get_nodes()
        for i in range(nodes.size()):
            node = nodes[i]
            c_notify_colored_neighbor(node, node.color)

        c_notify_colored_neighbor
        Q = nodes
        restart = True
        while Q.size() > 0:
            node = c_pop_max_node(Q)
            next_color = self._find_next_color(node)
            c_set_color(node[0], next_color)

        for i in range(nodes.size()):
            node = nodes[i]
            self._max_saturation = max(
                self._max_saturation, node.colored_degree
            )

    @property
    def cost(self) -> int:
        return self._num_colors

    @property
    def bound(self) -> int:
        return min(self._max_saturation + 1, self._num_colors)

    @property
    def max_saturation(self) -> int:
        return self._max_saturation + 1
