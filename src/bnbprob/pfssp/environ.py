__all__ = [
    'CallbackBnB',
    'CallbackBnBAge',
    'LazyBnB',
    'PermFlowShop',
    'PermFlowShop2M',
    'FlowSolution',
]

try:
    from bnbprob.pfssp.cython.bnb import (  # noqa: F401
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pfssp.cython.problem import (  # noqa: F401
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.cython.solution import FlowSolution  # noqa: F401
except (ModuleNotFoundError, ImportError) as e:
    print('Cython imports failed')
    print(e)
    from bnbprob.pfssp.pypure import (  # type: ignore # noqa: F401
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pfssp.pypure.problem import (  # type: ignore # noqa: F401
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.pypure.solution import (  # type: ignore # noqa: F401
        FlowSolution,
    )
