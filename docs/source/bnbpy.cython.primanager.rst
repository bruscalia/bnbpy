Priority Managers
=================

Priority-manager node managers use a native C++ binary min-heap to select
the next node according to a configurable ordering criterion (depth-first or
best-first bound).  They all extend
:class:`~bnbpy.cython.primanager.PriorityManagerTemplate`, which itself
extends :class:`~bnbpy.cython.manager.BaseNodeManager`.

For simpler stack / queue managers without priority ordering see
:doc:`bnbpy.cython.manager`.


PriorityManagerTemplate
-----------------------

.. autoclass:: bnbpy.cython.primanager::PriorityManagerTemplate
   :class-doc-from: both
   :members: not_empty, size, enqueue, enqueue_all, dequeue,
             get_lower_bound, clear, filter_by_lb, make_priority
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


DepthFirstSearch
----------------

.. autoclass:: bnbpy.cython.primanager::DepthFirstSearch
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource


BestFirstSearch
---------------

.. autoclass:: bnbpy.cython.primanager::BestFirstSearch
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource
