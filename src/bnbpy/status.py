__all__ = ["OptStatus"]

try:
    from bnbpy.cython.status import OptStatus
except (ModuleNotFoundError, ImportError) as e:
    print("Cython Node not found, using Python version")
    print(e)
    from bnbpy.pypure.status import OptStatus  # type: ignore
