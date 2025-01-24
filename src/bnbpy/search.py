try:
    from bnbpy.cython.search import (
        BestFirstBnB,
        BranchAndBound,
        BreadthFirstBnB,
        DepthFirstBnB,
        configure_logfile,
    )
except (ModuleNotFoundError, ImportError) as e:
    print('Cython Node not found, using Python version')
    print(e)
    from bnbpy.pypure.search import (
        BestFirstBnB,  # noqa: F401
        BranchAndBound,  # noqa: F401
        BreadthFirstBnB,  # noqa: F401
        DepthFirstBnB,  # noqa: F401
        configure_logfile,  # noqa: F401
    )
