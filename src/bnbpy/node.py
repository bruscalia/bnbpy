try:
    from bnbpy.cython.node import Node
except ModuleNotFoundError as e:
    print("Cython Node not found, using Python version")
    print(e)
    from bnbpy.pypure.node import Node  # noqa: F401
