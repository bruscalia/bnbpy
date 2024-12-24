try:
    from bnbpy.cython.node import Node as BaseNode
except ModuleNotFoundError as e:
    print("Cython Node not found, using Python version")
    print(e)
    from bnbpy.pypure.node import Node as BaseNode  # noqa: F401


class Node(BaseNode):
    pass
