# Package Class Diagram

The core components of the package are:

- {doc}`Problem <bnbpy.cython.problem>`: Abstract base class representing a discrete optimization (sub)problem. Users subclass it to define bounding, feasibility, and branching logic.
- {doc}`BranchAndBound <bnbpy.cython.search>`: The main search engine. It traverses the search tree, tracks incumbent solutions and global bounds, and delegates node selection to a manager.
- {doc}`Node <bnbpy.cython.node>`: Wraps a `Problem` instance and maintains the rooted tree structure (parent, depth level, and children, which are only kept when the search uses `save_tree=True`).
- {doc}`BaseNodeManager <bnbpy.cython.manager>`: Abstract interface for storing unexplored nodes and deciding which node to explore next. It keeps track of the lower bounds of the stored nodes; concrete implementations define the search strategy through four hooks (`_enqueue`, `_dequeue`, `_filter_by_lb`, `_clear`).
- {doc}`Solution <bnbpy.cython.solution>`: Holds the optimization status, lower bound, and cost (upper bound) for a given subproblem.
- {doc}`OptStatus <bnbpy.cython.status>`: Enum encoding possible optimization states (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).

A concise class diagram can be represented as shown below.

```{mermaid}
classDiagram

    direction LR

    class Solution {
        +cost : double
        +lb : double
        +status : OptStatus
    }

    class Problem {
        <<abstract>>
        +solution : Solution
        +calc_bound()* double
        +is_feasible()* bool
        +branch()* list~Problem~
    }

    class Node {
        +problem : Problem
        +parent : Node
        +level : int
        +lb : double
        +children : list~Node~
    }

    class BaseNodeManager {
        <<abstract>>
        +enqueue(node)
        +dequeue() Node
        #_enqueue(node)*
        #_dequeue()* Node
    }

    class BranchAndBound {
        +problem : Problem
        +root : Node
        +manager : BaseNodeManager
        +incumbent : Node
        +bound_node: Node
    }

    Problem *-- Solution
    Node *-- Problem

    BranchAndBound --> Problem
    BranchAndBound --> Node : root, incumbent, bound_node
    BranchAndBound o-- BaseNodeManager : manager

    BaseNodeManager ..> Node : enqueue, dequeue
```

Which, in a more detailed form, can encompass additional elements.

```{mermaid}
classDiagram
    direction LR

    class OptStatus {
        <<enumeration>>
        NO_SOLUTION
        RELAXATION
        OPTIMAL
        FEASIBLE
        INFEASIBLE
        FATHOM
        ERROR
        OTHER
    }

    class Solution {
        +cost : double
        +lb : double
        +status : OptStatus
        +set_lb(lb)
        +set_optimal()
        +set_feasible()
        +set_infeasible()
        +fathom()
        +copy(deep) Solution
    }

    class Problem {
        <<abstract>>
        +solution : Solution
        +calc_bound()* double
        +is_feasible()* bool
        +branch()* list~Problem~
        +warmstart() Problem | None
        +primal_heuristic() Problem | None
        +stronger_bound() double
        +upgrade_bound(new_lb)
        +copy(deep) Problem
        +child_copy(deep) Problem
    }

    class Node {
        +problem : Problem
        +parent : Node
        +level : int
        +lb : double
        +children : list~Node~
        +compute_bound()
        +check_feasible() bool
        +branch() list~Node~
        +primal_heuristic() Node
        +upgrade_bound()
        +cleanup()
    }

    class BaseNodeManager {
        <<abstract>>
        +enqueue(node)
        +dequeue() Node
        +not_empty() bool
        +size() int
        +get_lower_bound() Node
        +filter_by_lb(max_lb)
        +clear()
        #_enqueue(node)*
        #_dequeue()* Node
        #_filter_by_lb(max_lb)*
        #_clear()*
    }

    class SearchResults {
        +solution : Solution
        +problem : Problem
        +cost : double
        +lb : double
        +status : OptStatus
    }

    class BranchAndBound {
        +problem : Problem
        +root : Node
        +manager : BaseNodeManager
        +incumbent : Node
        +bound_node: Node
        +eval_node : str
        +save_tree : bool
        +explored : int
        +gap : double
        +rtol : double
        +atol : double
        +ub : double
        +lb : double
        +solve(maxiter, timelimit, rtol, atol) SearchResults
        +reset()
        +build_manager(strategy, **options)$ BaseNodeManager
        +set_manager(manager)
        +branch(node)
        +prune(node)
        +set_solution(node)
        +primal_heuristic(node)
        +upgrade_bound(node)
        +pre_eval_callback(node)
        +post_eval_callback(node)
        +enqueue_callback(node)
        +dequeue_callback(node)
        +solution_callback(node)
    }

    Solution --> OptStatus
    Problem *-- Solution
    Node *-- Problem
    Node o-- Node : parent / children

    BranchAndBound --> Problem
    BranchAndBound --> Node : root, incumbent, bound_node
    BranchAndBound o-- BaseNodeManager : manager
    BranchAndBound ..> SearchResults : returns

    BaseNodeManager ..> Node : enqueue, dequeue

    SearchResults --> Solution
    SearchResults --> Problem
```

The node managers implementing the search strategies, and the
corresponding Branch & Bound shortcuts, are organized as follows.

```{mermaid}
classDiagram
    direction TB

    class BaseNodeManager {
        <<abstract>>
    }
    class LifoManager
    class FifoManager
    class PriorityManagerTemplate {
        <<abstract>>
        +make_priority(node)* list~double~
    }
    class DepthFirstSearch
    class BestFirstSearch
    class LevelManagerInterface {
        <<abstract>>
        +levels : list~LevelQueue~
        +max_size : int
        +permanent_fallback : bool
        +new_level(level)* LevelQueue
    }
    class LevelQueue {
        +make_priority(node) list~double~
    }
    class NodePriQueueWrapper
    class CyclicBestSearch
    class DfsPriority

    BaseNodeManager <|-- LifoManager
    LifoManager <|-- FifoManager
    BaseNodeManager <|-- PriorityManagerTemplate
    PriorityManagerTemplate <|-- DepthFirstSearch
    PriorityManagerTemplate <|-- BestFirstSearch
    BaseNodeManager <|-- LevelManagerInterface
    LevelManagerInterface <|-- CyclicBestSearch
    LevelManagerInterface <|-- DfsPriority
    LevelManagerInterface *-- LevelQueue
    PriorityManagerTemplate *-- NodePriQueueWrapper
    LevelQueue *-- NodePriQueueWrapper
```

| Shortcut | Manager | `build_manager` alias |
|---|---|---|
| `BranchAndBound`, `DepthFirstBnB` | `DepthFirstSearch` | `'dfs'` |
| `BestFirstBnB` | `BestFirstSearch` | `'best'` |
| `BreadthFirstBnB`, `FifoBnB` | `FifoManager` | `'bfs'`, `'fifo'` |
| `LifoBnB` | `LifoManager` | `'lifo'` |
| — | `CyclicBestSearch` | `'cbfs'` |
| — | `DfsPriority` | — |
