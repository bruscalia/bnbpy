try:
    from bnbprob.pfssp.cython.bnb import (  # noqa: F401
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pfssp.cython.job import Job  # noqa: F401
    from bnbprob.pfssp.cython.permutation import Permutation  # noqa: F401
    from bnbprob.pfssp.cython.problem import (  # noqa: F401
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.cython.solution import FlowSolution  # noqa: F401
except ModuleNotFoundError as e:
    print("Cython imports failed")
    print(e)
    from bnbprob.pfssp.pypure.bnb import (  # noqa: F401
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pfssp.pypure.job import Job  # noqa: F401
    from bnbprob.pfssp.pypure.permutation import Permutation  # noqa: F401
    from bnbprob.pfssp.pypure.problem import (  # noqa: F401
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.pypure.solution import FlowSolution  # noqa: F401
