# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from cpython.object cimport Py_EQ, Py_NE, Py_LT, Py_GT, Py_LE, Py_GE
from libcpp cimport bool
from libcpp.vector cimport vector


cdef:
    int BASE_SIZE = 8


cdef Node* c_alloc_node(int index):
    """Allocate and initialize a new Node using the constructor."""
    return new Node(index)


cdef void c_free_node(Node* node):
    """Free a node allocated with c_alloc_node."""
    if node != NULL:
        del node


cdef void c_add_neighbor(Node& node, Node& neighbor):
    # This uses a list intentionally for performance
    # Duplicates are not expected and should be avoided by the caller
    # A set would be more appropriate for correctness,
    # but it would add overhead
    node.neighbors.push_back(&neighbor)
    node.degree += 1


cdef bool c_can_color(Node& node, int color):
    if <size_t>color >= node.neighbor_colors.size():
        node.neighbor_colors.resize(
            max(node.neighbor_colors.size(), <size_t>color) + BASE_SIZE,
            False
        )
    return not node.neighbor_colors[color]


cdef void c_set_color(Node& node, int color):
    cdef:
        Node* neighbor

    node.color = color
    node.has_color = True
    for neighbor in node.neighbors:
        c_notify_colored_neighbor(neighbor, color)


cdef void c_notify_colored_neighbor(Node* node, int color):
    cdef:
        size_t i

    # Resize if necessary (note: must check before subtracting 1 to avoid underflow)
    if <size_t>color >= node.neighbor_colors.size() - 1:
        node.neighbor_colors.resize(
            max(<size_t>color + 1, node.neighbor_colors.size()) + BASE_SIZE,
            False
        )

    if not node.neighbor_colors[color]:
        node.neighbor_colors[color] = True
        node.colored_degree += 1

        if color == node.color:
            # Find next available color
            for i in range(<size_t>color, node.neighbor_colors.size()):
                if not node.neighbor_colors[i]:
                    node.color = i
                    break


cdef void c_color_clean(Node& node):
    cdef vector[bool] empty_colors
    empty_colors.resize(BASE_SIZE, False)

    node.color = 0
    node.has_color = False
    node.colored_degree = 0
    node.neighbor_colors = empty_colors


cdef Node* c_clean_copy(const Node& node):
    cdef:
        Node* other
        vector[bool] empty_colors
        vector[Node*] empty_neighbors

    other = c_alloc_node(node.index)
    other.neighbors.reserve(node.neighbors.size())
    return other


cdef Node* c_pop_max_node(vector[Node*]& nodes):
    cdef:
        Node* max_node
        Node* node
        int max_color_degree
        int max_degree
        size_t max_index
        size_t j

    if nodes.size() == 0:
        return NULL

    # Initialize with first node
    max_node = nodes[0]
    max_color_degree = max_node.colored_degree
    max_degree = max_node.degree
    max_index = 0

    # Check remaining nodes
    for j in range(1, nodes.size()):
        node = nodes[j]
        if node.colored_degree > max_color_degree:
            max_color_degree = node.colored_degree
            max_degree = node.degree
            max_node = node
            max_index = j
        elif node.colored_degree == max_color_degree:
            if node.degree > max_degree:
                max_color_degree = node.colored_degree
                max_degree = node.degree
                max_node = node
                max_index = j

    # Swap with last element and pop (O(1) instead of O(n) erase)
    if max_index != nodes.size() - 1:
        nodes[max_index] = nodes.back()
    nodes.pop_back()
    return max_node


cdef Node* c_find_max_sat_node(vector[Node*]& nodes):
    cdef:
        Node* max_node
        Node* node
        int max_color_degree
        int max_degree
        size_t j

    if nodes.size() == 0:
        return NULL

    # Initialize with first node
    max_node = nodes[0]
    max_color_degree = max_node.colored_degree
    max_degree = max_node.degree

    # Check remaining nodes
    for j in range(1, nodes.size()):
        node = nodes[j]
        if node.colored_degree > max_color_degree:
            max_color_degree = node.colored_degree
            max_degree = node.degree
            max_node = node
        elif node.colored_degree == max_color_degree:
            if node.degree > max_degree:
                max_color_degree = node.colored_degree
                max_degree = node.degree
                max_node = node

    return max_node


cdef Node* c_find_max_node_degree(vector[Node*]& nodes):
    cdef:
        Node* max_node
        Node* node
        int max_degree
        size_t max_index
        size_t j

    max_degree = -1
    max_index = 0
    for j in range(nodes.size()):
        node = nodes[j]
        if node.degree > max_degree:
            max_degree = node.degree
            max_node = node
            max_index = j

    return max_node
