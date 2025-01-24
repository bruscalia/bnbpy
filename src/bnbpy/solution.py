try:
    from bnbpy.cython.solution import Solution
except (ModuleNotFoundError, ImportError) as e:
    print("Cython Node not found, using Python version")
    print(e)
    from bnbpy.pypure.solution import Solution  # noqa: F401
