Node Priority Queue
===================

The ``nodequeue`` module provides
:class:`~bnbpy.cython.nodequeue.NodePriQueueWrapper`, a min-heap of nodes
with ``vector[double]`` priorities (compared lexicographically) backed by a
native C++ binary heap.

It is the low-level building block of the priority managers
(:class:`~bnbpy.cython.primanager.PriorityManagerTemplate` and its
subclasses, see :doc:`bnbpy.cython.primanager`) and of each
:class:`~bnbpy.cython.levelqueue.LevelQueue` of the level-based managers
(see :doc:`bnbpy.cython.levelqueue`). It does not track lower bounds by
itself: that is done by :class:`~bnbpy.cython.manager.BaseNodeManager`.


NodePriQueueWrapper
-------------------

.. autoclass:: bnbpy.cython.nodequeue::NodePriQueueWrapper
   :class-doc-from: both
   :members: push, pop, filter, size, clear
   :undoc-members:
   :member-order: bysource
