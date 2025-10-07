__all__ = [
    'CallbackBnB',
    'LazyBnB',
    'CutoffBnB',
    'PermFlowShop',
    'PermFlowShop2M',
    'PermFlowShop2MHalf'
]

from logging import getLogger

log = getLogger(__name__)

try:
    from bnbprob.pafssp.cython.bnb import (
        CallbackBnB,
        CutoffBnB,
        LazyBnB,
    )
    from bnbprob.pafssp.cython.problem import (
        PermFlowShop,
        PermFlowShop2M,
        PermFlowShop2MHalf,
    )
except (ModuleNotFoundError, ImportError) as e:
    log.error('Cython imports failed for PFSSP - No Python fallback')
    log.error(e)
    raise e
