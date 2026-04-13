BranchAndBound
--------------

.. autoclass:: bnbpy.cython.search::BranchAndBound
   :class-doc-from: both
   :members: solve, reset, enqueue, dequeue, branch, build_manager, pre_eval_callback, post_eval_callback, enqueue_callback, dequeue_callback, solution_callback, set_solution, log_row
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


DepthFirstBnB
-------------

.. autoclass:: bnbpy.cython.search::DepthFirstBnB
   :class-doc-from: both
   :show-inheritance:


BreadthFirstBnB
---------------

.. autoclass:: bnbpy.cython.search::BreadthFirstBnB
   :class-doc-from: both
   :show-inheritance:


BestFirstBnB
------------

.. autoclass:: bnbpy.cython.search::BestFirstBnB
   :class-doc-from: both
   :show-inheritance:


LifoBnB
-------

.. autoclass:: bnbpy.cython.search::LifoBnB
   :class-doc-from: both
   :show-inheritance:


FifoBnB
-------

.. autoclass:: bnbpy.cython.search::FifoBnB
   :class-doc-from: both
   :show-inheritance:


SearchResults
-------------

.. autoclass:: bnbpy.cython.search.SearchResults
   :class-doc-from: both
   :members: solution, cost, lb, status
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
