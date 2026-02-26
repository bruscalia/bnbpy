import heapq
import logging
from dataclasses import dataclass

from bnbprob.machdeadline.job import Job

log = logging.getLogger(__name__)


LARGE_INT = 100000000


@dataclass(frozen=True, slots=True)
class SmithResults:
    jobs: list[Job]
    success: bool


class SmithHelper:
    @staticmethod
    def apply(
        jobs: list[Job], total_time: int | None = None, reverse: bool = True
    ) -> SmithResults:
        if total_time is None:
            total_time = sum(job.p for job in jobs)
        pool = sorted(jobs, key=lambda j: j.d, reverse=False)
        sol: list[Job] = []
        candidates: list[tuple[float, Job]] = []
        for _ in range(len(jobs)):
            SmithHelper._update_pool(pool, candidates, total_time)
            if len(candidates) == 0:
                return SmithResults(jobs=jobs, success=False)
            next_job = heapq.heappop(candidates)[1]
            sol.append(next_job)
            total_time -= next_job.p

        if reverse:
            sol.reverse()

        return SmithResults(jobs=sol, success=True)

    @staticmethod
    def _update_pool(
        pool: list[Job], candidates: list[tuple[float, Job]], tot_time: int
    ) -> None:
        for _ in range(len(pool)):
            if pool[-1].d >= tot_time:
                job = pool.pop()
                heapq.heappush(candidates, (job.w / job.p, job))
            else:
                break
