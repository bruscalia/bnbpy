Level Queue
===========

The ``levelqueue`` module provides level-based node managers.  Nodes are
grouped by search depth (level) and each level maintains its own
:class:`~bnbpy.cython.nodequeue.PriorityManagerInterface` queue.

:class:`~bnbpy.cython.levelqueue.LevelManagerInterface` is the abstract
base class.  Two concrete strategies are provided:

* :class:`~bnbpy.cython.levelqueue.CyclicBestSearch` — cyclic best-first
  search, cycling through levels before falling back to the global best.
* :class:`~bnbpy.cython.levelqueue.DfsPriority` — depth-first with
  priority ordering within each level.

For simpler priority-queue managers without level cycling see
:doc:`bnbpy.cython.nodequeue`.


LevelQueue
----------

.. autoclass:: bnbpy.cython.levelqueue::LevelQueue
   :class-doc-from: both
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


LevelManagerInterface
---------------------

.. autoclass:: bnbpy.cython.levelqueue::LevelManagerInterface
   :class-doc-from: both
   :members: not_empty, size, enqueue, enqueue_all, dequeue,
             get_lower_bound, pop_lower_bound, clear, filter_by_lb, pop_all,
             new_level, add_level
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


CyclicBestSearch
----------------

.. autoclass:: bnbpy.cython.levelqueue::CyclicBestSearch
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource


DfsPriority
-----------

.. autoclass:: bnbpy.cython.levelqueue::DfsPriority
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource
