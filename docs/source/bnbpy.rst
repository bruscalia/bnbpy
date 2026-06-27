Core Package
============

Here you'll find the main contents of the bnbpy package.

For the core components of the branch-and-bound framework, please refer to the following sections:

* :doc:`Problem <bnbpy.cython.problem>` for the definition of the optimization problem.
* :doc:`Search <bnbpy.cython.search>` for the branch-and-bound search algorithm.
* :doc:`Solution <bnbpy.cython.solution>` for the representation of solutions.
* :doc:`OptStatus <bnbpy.cython.status>` for optimization status.
* :doc:`Node Managers <bnbpy.cython.manager>` for node manager interface and simple LIFO/FIFO managers.
* :doc:`Priority Managers <bnbpy.cython.primanager>` for priority manager node managers.
* :doc:`Node Priority Queue <bnbpy.cython.nodequeue>` for C++-backed priority queue managers.
* :doc:`Level Queue <bnbpy.cython.levelqueue>` for level-based node managers (cyclic best-first and DFS).
* :doc:`Node <bnbpy.cython.node>` for the representation of nodes.

For a detailed documentation of its column generation submodule, please refer to :doc:`Column Generation <bnbpy.colgen>`.

.. toctree::
   :maxdepth: 2
   :caption: Core Components:
   :hidden:

   bnbpy.cython.problem
   bnbpy.cython.search
   bnbpy.cython.solution
   bnbpy.cython.status
   bnbpy.cython.manager
   bnbpy.cython.primanager
   bnbpy.cython.nodequeue
   bnbpy.cython.levelqueue
   bnbpy.cython.node
