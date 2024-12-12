from typing import List

from pydantic import BaseModel

from bnbprob.machdeadline.job import Job


class MachInstance(BaseModel):
    jobs: List[Job]
