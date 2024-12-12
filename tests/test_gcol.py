import os

import pytest

from bnbprob import gcol
from bnbpy import BranchAndBound, OptStatus

HERE = os.path.dirname(__file__)


@pytest.mark.gcol
class TestGcol:
    @pytest.mark.parametrize(
        ('filename', 'solution', 'explored', 'mode'),
        [
            ('gcol_50.txt', 14, 36, "heur"),
            ('gcol_50.txt', 14, 39, "hybr"),
            # ('gcol_50.txt', 14, 308, "mip"),
            ('gcol_32.txt', 8, 6, "heur"),
            ('gcol_32.txt', 8, 10, "hybr"),
            ('gcol_32.txt', 8, 21, "mip"),
        ],
    )
    def test_gcol(self, filename, solution, explored, mode):
        fpath = os.path.join(HERE, "instances", "gcol", filename)
        instance = gcol.load_instance(fpath)
        price_tol = 0.1
        bnb = BranchAndBound()
        pricing = self.get_pricing(mode, instance["edges"], price_tol)
        problem = gcol.ColGenColor(
            instance['edges'],
            pricing=pricing,
            max_iter_price=1000,
        )
        sol = bnb.solve(problem, maxiter=500)
        assert sol.status == OptStatus.OPTIMAL, "Subptimal solution"
        assert sol.cost == solution, "Wrong cost"
        assert bnb.explored == explored, "Wrong number of nodes"

    @staticmethod
    def get_pricing(mode, edges, price_tol):
        if mode == "hybr":
            return gcol.ColorHybrPricing(
                edges,
                heur=gcol.TargetMultiStart(
                    12, price_tol + 1, 20, 200
                ),
                price_tol=price_tol
            )
        elif mode == "heur":
            return gcol.ColorHeurPricing(
                edges,
                heur=gcol.TargetMultiStart(
                    12, price_tol + 1, 20, 200
                ),
                price_tol=price_tol
            )
        return gcol.ColorMIPPricing(
            edges,
            price_tol=price_tol
        )
