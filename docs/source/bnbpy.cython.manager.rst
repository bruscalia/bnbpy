Node Managers
=============

Node managers implement the :class:`~bnbpy.cython.manager.BaseNodeManager`
interface and control how nodes are stored and retrieved during Branch & Bound
search.  The manager is the *strategy* object injected into
:class:`~bnbpy.cython.search.BranchAndBound` via the ``manager`` parameter
(or the :meth:`~bnbpy.cython.search.BranchAndBound.build_manager` factory).

Simple managers (:class:`~bnbpy.cython.manager.LifoManager`,
:class:`~bnbpy.cython.manager.FifoManager`) use a plain Python ``list`` and
impose pure stack / queue traversal with no priority ordering.  For
bound-based traversal strategies see :doc:`bnbpy.cython.primanager` and
:doc:`bnbpy.cython.levelqueue`.

Custom managers subclass :class:`~bnbpy.cython.manager.BaseNodeManager`
and implement four hooks: ``_enqueue`` (add a node), ``_dequeue`` (remove
and return the next node, or ``None``), ``_filter_by_lb`` (remove the nodes
with ``lb >= max_lb`` and mark them with ``node.fathom()``) and ``_clear``
(remove all nodes). The public methods (``enqueue``, ``dequeue``,
``filter_by_lb``, ``get_lower_bound``, …) wrap these hooks and keep track
of the lower bounds of the nodes, so they should not be overridden.


BaseNodeManager
---------------

.. autoclass:: bnbpy.cython.manager::BaseNodeManager
   :class-doc-from: both
   :members: not_empty, size, enqueue, enqueue_all, dequeue,
             get_lower_bound, clear, filter_by_lb, _enqueue, _dequeue,
             _filter_by_lb, _clear
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
