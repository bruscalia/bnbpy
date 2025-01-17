try:
    from bnbprob.pfssp.cython.problem import (  # noqa: F401
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.cython.solution import FlowSolution  # noqa: F401
except (ModuleNotFoundError, ImportError) as e:
    print("Cython imports failed")
    print(e)
    from bnbprob.pfssp.pypure.problem import (  # noqa: F401
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.pypure.solution import FlowSolution  # noqa: F401
