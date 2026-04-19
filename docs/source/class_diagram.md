# Package Class Diagram

The core components of the package are:

- {doc}`Problem <bnbpy.cython.problem>`: Abstract base class representing a discrete optimization (sub)problem. Users subclass it to define bounding, feasibility, and branching logic.
- {doc}`BranchAndBound <bnbpy.cython.search>`: The main search engine. It traverses the search tree, tracks incumbent solutions and global bounds, and delegates node selection to a manager.
- {doc}`Node <bnbpy.cython.node>`: Wraps a `Problem` instance and maintains the rooted tree structure (parent, children, depth level).
- {doc}`BaseNodeManager <bnbpy.cython.manager>`: Abstract interface for storing unexplored nodes and deciding which node to explore next. Concrete implementations define the search strategy.
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
        +enqueue(node)*
        +dequeue()* Node
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
    }

    class Solution {
        +cost : double
        +lb : double
        +status : OptStatus
        +set_optimal()
        +set_feasible()
        +set_infeasible()
        +fathom()
    }

    class Problem {
        <<abstract>>
        +solution : Solution
        +calc_bound()* double
        +is_feasible()* bool
        +branch()* list~Problem~
        +warmstart() Problem
        +primal_heuristic() Problem
        +stronger_bound() double
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
    }

    class BaseNodeManager {
        <<abstract>>
        +enqueue(node)*
        +dequeue()* Node
        +not_empty()* bool
        +size()* int
        +get_lower_bound()* Node
        +filter_by_lb(max_lb)
        +clear()
    }

    class SearchResults {
        +solution : Solution
        +problem : Problem
    }

    class BranchAndBound {
        +problem : Problem
        +root : Node
        +manager : BaseNodeManager
        +incumbent : Node
        +bound_node: Node
        +explored : int
        +gap : double
        +rtol : double
        +atol : double
        +solve(maxiter, maxtime) SearchResults
        +branch(node)
        +prune(node)
        +primal_heuristic(node)
        +set_manager(manager)
        +reset()
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