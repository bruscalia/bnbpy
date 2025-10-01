__all__ = [
    'CallbackBnB',
    'CallbackBnBAge',
    'LazyBnB',
    'PermFlowShop',
    'PermFlowShop2M',
    'FlowSolution',
]

try:
    from bnbprob.pfssp.cython.bnb import (
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pfssp.cython.problem import (
        PermFlowShop,
        PermFlowShop2M,
    )
except (ModuleNotFoundError, ImportError) as e:
    print('Cython imports failed')
    print(e)
    from bnbprob.pfssp.pypure import (  # type: ignore
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pfssp.pypure.problem import (  # type: ignore
        PermFlowShop,
        PermFlowShop2M,
    )
    from bnbprob.pfssp.pypure.solution import (  # type: ignore
        FlowSolution,
    )
