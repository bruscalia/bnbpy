# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector


cdef extern from *:
    """
    #include <vector>

    struct Node {
        int index;
        std::vector<Node*> neighbors;
        int color;
        bool has_color;
        std::vector<bool> neighbor_colors;
        int colored_degree;
        int degree;

        // Default constructor
        Node() : index(0), color(0), has_color(false),
                 neighbor_colors(4, false),
                 colored_degree(0), degree(0) {}

        // Constructor with index
        Node(int idx) : index(idx), color(0), has_color(false),
                        neighbor_colors(4, false),
                        colored_degree(0), degree(0) {}
    };
    """
    cppclass Node:
        int index
        vector[Node*] neighbors
        int color
        bool has_color
        vector[bool] neighbor_colors
        int colored_degree
        int degree
        Node()
        Node(int index)

cdef void c_add_neighbor(Node& node, Node& neighbor)

cdef bool c_can_color(Node& node, int color)

cdef void c_set_color(Node& node, int color)

cdef void c_notify_colored_neighbor(Node* node, int color)

cdef void c_color_clean(Node& node)

cdef Node* c_clean_copy(const Node& node)

cdef Node* c_pop_max_node(vector[Node*]& nodes)

cdef Node* c_find_max_sat_node(vector[Node*]& nodes)

cdef Node* c_find_max_node_degree(vector[Node*]& nodes)

cdef Node* c_alloc_node(int index)

cdef void c_free_node(Node* node)
