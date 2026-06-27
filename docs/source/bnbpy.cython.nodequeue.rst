Node Priority Queue
===================

The ``nodequeue`` module provides a C++-backed priority queue for node
management.  :class:`~bnbpy.cython.nodequeue.PriorityManagerInterface`
is the abstract base class and extends
:class:`~bnbpy.cython.manager.BaseNodeManager`.
:class:`~bnbpy.cython.nodequeue.BestFirstSearch` is the built-in
concrete implementation that selects nodes by lowest lower bound.

For level-based managers built on top of this module see
:doc:`bnbpy.cython.levelqueue`.


PriorityManagerInterface
------------------------

.. autoclass:: bnbpy.cython.nodequeue::PriorityManagerInterface
   :class-doc-from: both
   :members: not_empty, size, enqueue, enqueue_all, dequeue,
             get_lower_bound, pop_lower_bound, clear, filter_by_lb, pop_all
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


BestFirstSearch
---------------

.. autoclass:: bnbpy.cython.nodequeue::BestFirstSearch
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource
