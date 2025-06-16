__all__ = ["Node"]

try:
    from bnbpy.cython.node import Node
except (ModuleNotFoundError, ImportError) as e:
    print("Cython Node not found, using Python version")
    print(e)
    from bnbpy.pypure.node import Node  # type: ignore
