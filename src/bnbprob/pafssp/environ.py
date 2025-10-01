__all__ = [
    'CallbackBnB',
    'CallbackBnBAge',
    'LazyBnB',
    'PermFlowShop',
    'PermFlowShop2M'
]

try:
    from bnbprob.pafssp.cython.bnb import (
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pafssp.cython.problem import (
        PermFlowShop,
        PermFlowShop2M,
    )
except (ModuleNotFoundError, ImportError) as e:
    print('Cython imports failed')
    print(e)
    from bnbprob.pafssp.pypure import (  # type: ignore
        CallbackBnB,
        CallbackBnBAge,
        LazyBnB,
    )
    from bnbprob.pafssp.pypure.problem import (  # type: ignore
        PermFlowShop,
        PermFlowShop2M,
    )
