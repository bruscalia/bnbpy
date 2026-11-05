Level Queue
===========

The ``levelqueue`` module provides level-based node managers.  Nodes are
grouped by search depth (level) and each level is a
:class:`~bnbpy.cython.levelqueue.LevelQueue`, which wraps a
:class:`~bnbpy.cython.nodequeue.NodePriQueueWrapper` (C++ min-heap)
ordered by :meth:`~bnbpy.cython.levelqueue.LevelQueue.make_priority`.

:class:`~bnbpy.cython.levelqueue.LevelManagerInterface` is the abstract
base class.  Two concrete strategies are provided:

* :class:`~bnbpy.cython.levelqueue.CyclicBestSearch` — cyclic best-first
  search: cycles through levels, dequeuing the best node of each level.
  When the number of nodes exceeds ``max_size`` it falls back to the
  deepest non-empty level (depth-first), returning to cycling once the
  count drops to ``max_size // 2`` (unless ``permanent_fallback`` is set).
* :class:`~bnbpy.cython.levelqueue.DfsPriority` — depth-first with
  best-first ordering within each level (permanent fallback).

For simpler priority-queue managers without level cycling see
:doc:`bnbpy.cython.primanager`.


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
             get_lower_bound, clear, filter_by_lb, new_level, reset_level,
             levels, current_level, start_level, last_level, max_size,
             use_fallback, permanent_fallback
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
