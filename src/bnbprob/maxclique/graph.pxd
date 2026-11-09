# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp.vector cimport vector

from bnbprob.maxclique.node cimport (
    Node,
    c_add_neighbor,
    c_set_color,
    c_notify_colored_neighbor,
    c_clean_copy,
    c_pop_max_node,
    c_alloc_node,
    c_free_node
)


cdef extern from *:
    """
    #include <algorithm>
    #include <queue>
    #include <vector>

    // Forward declaration
    struct Node;

    inline void sort_nodes_by_degree(std::vector<Node*>& nodes) {
        std::sort(nodes.begin(), nodes.end(), [](Node* a, Node* b) {
            return a->degree < b->degree;
        });
    }
    """
    void sort_nodes_by_degree(vector[Node*]&)


cdef class NodeWrapper:
    cdef public:
        int index
        int color
        list[int] neighbors


cdef NodeWrapper wrap_node(Node* node)


cdef class Graph:

    cdef:
        vector[Node*] _nodes
        vector[Node*] _active_nodes
        int _size
        int _active_size

    cdef inline vector[Node*] get_nodes(self):
        return self._active_nodes

    cdef inline int get_active_size(self):
        return self._active_size

    cdef inline Node* c_next_node(self):
        return self._active_nodes.back()

    cpdef NodeWrapper next_node(self)

    cpdef int next_index(self)

    cpdef Graph copy_remove(self, int node_idx)

    cpdef Graph copy_branch(self, int node_idx)


cdef class DSatur:
    cdef:
        Graph _G
        int _num_colors
        int _max_saturation


    cdef int _find_next_color(self, Node* node)

    cpdef void solve(self)

    cpdef void resolve(self)
