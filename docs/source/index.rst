bnbpy
=====

A generic, configurable Python framework for solving optimization problems
using Branch & Bound. Also supports Column Generation and Branch & Price.

Installation
------------

Install the package directly from GitHub:

.. code-block:: bash

   pip install git+https://github.com/bruscalia/bnbpy.git

To include development resources for tests and linters, use the ``dev`` extra:

.. code-block:: bash

   pip install "bnbpy[dev] @ git+https://github.com/bruscalia/bnbpy.git"

For local development with editable mode:

.. code-block:: bash

   git clone https://github.com/bruscalia/bnbpy.git
   cd bnbpy
   python -m pip install -e .[dev]

Basic Usage
-----------

Branch & Bound
~~~~~~~~~~~~~~

.. code-block:: python

   from bnbpy import BranchAndBound, Problem

   class MyProblem(Problem):
       # Define your problem specifications by implementing abstract methods

       def calc_bound(self):
           # Compute node lower bound
           pass

       def is_feasible(self):
           # Verify if node is feasible in the complete problem
           pass

       def branch(self):
           # Return a list of subproblems if not fathomed
           pass

   # Apply Branch & Bound
   problem = MyProblem()
   bnb = BranchAndBound()
   bnb.solve(problem)
   print(bnb.solution)

Branch & Price
~~~~~~~~~~~~~~

.. code-block:: python

   import bnbpy as bbp

   class MyMaster(bbp.Master):
       def __init__(self, *args):
           # Implement your master problem
           pass

       def add_col(self, c) -> bool:
           # Include a new column and return True if accepted
           return True

       def solve(self) -> bbp.MasterSol:
           # cost = ...
           # duals = ...
           # return MasterSol(cost=cost, duals=duals)
           pass

   class MyPricing(bbp.Pricing):
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           # Instantiate your pricing problem

       def set_weights(self, c):
           # Modify the instance by incorporating new weights
           pass

       def solve(self) -> bbp.PriceSol:
           # red_cost = ...
           # new_col = ...
           # return PriceSol(red_cost=red_cost, new_col=new_col)
           pass

   class MyCG(bbp.ColumnGenProblem):
       def __init__(self, **kwargs):
           master = MyMaster()
           pricing = MyPricing(**kwargs)
           super().__init__(
               master=master,
               pricing=pricing,
           )

       def branch(self) -> list['MyCG'] | None:
           # Create children
           pass

       def is_feasible(self) -> bool:
           # Check for feasibility in the complete formulation
           pass


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   bnbpy
   bnbpy.colgen
   examples

