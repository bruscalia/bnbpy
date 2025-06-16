__all__ = ["Problem"]

try:
    from bnbpy.cython.problem import Problem
except (ModuleNotFoundError, ImportError) as e:
    print("Cython Node not found, using Python version")
    print(e)
    from bnbpy.pypure.problem import Problem  # type: ignore
