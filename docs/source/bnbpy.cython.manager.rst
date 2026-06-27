Node Managers
=============

Node managers implement the :class:`~bnbpy.cython.manager.BaseNodeManager`
interface and control how nodes are stored and retrieved during Branch & Bound
search.  The manager is the *strategy* object injected into
:class:`~bnbpy.cython.search.BranchAndBound` via the ``manager`` parameter
(or the :meth:`~bnbpy.cython.search.BranchAndBound.build_manager` factory).

Simple managers (:class:`~bnbpy.cython.manager.LifoManager`,
:class:`~bnbpy.cython.manager.FifoManager`) use a plain ``deque`` and impose
pure stack / queue traversal with no priority ordering.  For bound-based
traversal strategies see :doc:`bnbpy.cython.primanager`.


BaseNodeManager
---------------

.. autoclass:: bnbpy.cython.manager::BaseNodeManager
   :class-doc-from: both
   :members: not_empty, size, enqueue, enqueue_all, dequeue,
             get_lower_bound, clear, filter_by_lb
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


LifoManager
-----------

.. autoclass:: bnbpy.cython.manager::LifoManager
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource


FifoManager
-----------

.. autoclass:: bnbpy.cython.manager::FifoManager
   :class-doc-from: both
   :members:
   :show-inheritance:
   :member-order: bysource
