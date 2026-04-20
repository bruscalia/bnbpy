Priority Queues
===============

Priority-queue node managers use a priority queue from Python's `heapq`
module to select the next node according to a configurable ordering
criterion (depth, breadth, or best bound).  They all
extend :class:`~bnbpy.cython.priqueue.PriorityQueue`, which itself extends
:class:`~bnbpy.cython.manager.BaseNodeManager`.

For simpler stack / queue managers without priority ordering see
:doc:`bnbpy.cython.manager`.


PriorityQueue
-------------

.. autoclass:: bnbpy.cython.priqueue::PriorityQueue
   :class-doc-from: both
   :members: not_empty, size, enqueue, enqueue_all, dequeue,
             get_lower_bound, pop_lower_bound, clear, filter_by_lb, pop_all
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


DfsPriQueue
-----------

.. autoclass:: bnbpy.cython.priqueue::DfsPriQueue
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource


BfsPriQueue
-----------

.. autoclass:: bnbpy.cython.priqueue::BfsPriQueue
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource


BestPriQueue
------------

.. autoclass:: bnbpy.cython.priqueue::BestPriQueue
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource

