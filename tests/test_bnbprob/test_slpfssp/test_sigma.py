import pytest

from bnbprob.slpfssp.job import Job
from bnbprob.slpfssp.sigma import Sigma


@pytest.fixture
def oneline_job() -> Job:
    p = [[1, 2, 3, 5, 7]]
    r = [[3, 6, 9, 12, 15]]
    q = [[1, 2, 3, 4, 5]]
    job = Job(0, p, s=2)
    job.r = r
    job.q = q
    return job


@pytest.fixture
def oneline_sigma() -> Sigma:
    C = [[2, 7, 8, 8, 12]]
    return Sigma([], [C[0].copy()])


@pytest.mark.slpfssp
def test_job_to_top_oneline(oneline_job: Job, oneline_sigma: Sigma) -> None:
    sigma = oneline_sigma.copy(deep=True)
    sigma.job_to_top(oneline_job)
    # Replace with the expected result after job_to_top
    expected_C = [[30, 29, 27, 24, 19]]
    assert sigma.C == expected_C


@pytest.mark.slpfssp
def test_job_to_bottom_oneline(oneline_job: Job, oneline_sigma: Sigma) -> None:
    sigma = oneline_sigma.copy(deep=True)
    sigma.job_to_bottom(oneline_job)
    # Replace with the expected result after job_to_top
    expected_C = [[4, 9, 12, 17, 24]]
    assert sigma.C == expected_C
