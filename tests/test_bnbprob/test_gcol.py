import os
import random
from typing import cast

import pytest

from bnbprob import gcol
from bnbprob.gcol import SetCover, SetCoverHeur
from bnbpy.colgen import Pricing
from bnbpy.cython.search import BranchAndBound
from bnbpy.cython.status import OptStatus

HERE = os.path.dirname(__file__)


@pytest.mark.gcol
class TestGcol:
    @pytest.mark.parametrize(
        ('filename', 'solution', 'mode'),
        [
            ('gcol_50.txt', 14, 'heur'),
            ('gcol_50.txt', 14, 'hybr'),
            ('gcol_32.txt', 8, 'heur'),
            ('gcol_32.txt', 8, 'hybr'),
            ('gcol_32.txt', 8, 'mip'),
        ],
    )
    def test_gcol(self, filename: str, solution: int, mode: str) -> None:
        fpath = os.path.join(HERE, os.pardir, 'instances', 'gcol', filename)
        instance = gcol.load_instance(fpath)
        edges = cast(list[tuple[int, int]], instance['edges'])
        price_tol = 0.1
        pricing = self.get_pricing(mode, edges, price_tol)
        problem = gcol.ColGenColor(
            edges,
            pricing=pricing,
            max_iter_price=1000,
        )
        bnb = BranchAndBound(problem)
        sol = bnb.solve(maxiter=500)
        assert sol.status == OptStatus.OPTIMAL, 'Subptimal solution'
        assert sol.cost == solution, 'Wrong cost'

    @staticmethod
    def get_pricing(
        mode: str, edges: list[tuple[int, int]], price_tol: float
    ) -> Pricing:
        if mode == 'hybr':
            return gcol.ColorHybrPricing(
                edges,
                heur=gcol.TargetMultiStart(12, price_tol + 1, 20, 200),
                price_tol=price_tol,
            )
        elif mode == 'heur':
            return gcol.ColorHeurPricing(
                edges,
                heur=gcol.TargetMultiStart(12, price_tol + 1, 20, 200),
                price_tol=price_tol,
            )
        return gcol.ColorMIPPricing(edges, price_tol=price_tol)


@pytest.mark.gcol
@pytest.mark.parametrize('seed', range(50))
def test_set_cover_heuristic_covers_all(seed: int) -> None:
    rng = random.Random(seed)
    n = 8
    sets = [set(rng.sample(range(n), rng.randint(1, 4))) for _ in range(7)]
    sets.append(set(range(n)) - set().union(*sets) or {0})
    set_cover = SetCover()
    for s in sets:
        set_cover.add_set(s, rng.randint(1, 3))
    sol = SetCoverHeur().solve(set_cover)
    covered = set().union(*({node.index for node in s.nodes} for s in sol))
    assert covered == set(set_cover.nodes)
