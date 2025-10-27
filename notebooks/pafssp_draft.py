import gc
import json
import time

from bnbprob.pafssp import CallbackBnB, CutoffBnB
from bnbpy import configure_logfile

configure_logfile("pfssp-bench-script.log", mode="w")

with open("./../data/flow-shop/ta017.json", mode="r", encoding="utf8") as f:
    p = json.load(f)

print(f"{len(p)} Jobs; {len(p[0])} Machines")

gc.disable()


problem = PermFlowShop2MHalf.from_p(p, constructive='neh')
bnb = CutoffBnB(1484)
# bnb = CallbackBnB()

start = time.time()
sol = bnb.solve(problem, maxiter=10_000_000, timelimit=300)
end = time.time()
print(f"Solved in {end - start:.2f} seconds")
print(sol)

