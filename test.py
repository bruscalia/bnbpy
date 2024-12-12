from bnbprob.pfssp.cython.job import Job as CJob
from bnbprob.pfssp.cython.sequence import Sigma2 as CSigma2

p = [
    [5, 9, 7, 4],
    [9, 3, 3, 8],
    [8, 10, 5, 6],
    [1, 8, 6, 2]
]

import time

s = time.time()

for _ in range(3):

    print("here")

    cjobs = [
        CJob(i, p[i], [0] * len(p[i]), [0] * len(p[i]), [[]])
        for i in range(len(p))
    ]

    print("2")

    x = []
    C = [0] * len(p[0])
    c = CSigma2(x, C)

    print("3")

    for i in range(len(cjobs)):
        # c.pyadd_job(cjobs[i])
        print("4", i)

    print(time.time() - s)
