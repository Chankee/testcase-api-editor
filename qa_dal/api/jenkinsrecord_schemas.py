from typing import List, Optional, Union
from pydantic import BaseModel


class JenkinsBase(BaseModel):
    id: Optional[int]


class SaveResult(JenkinsBase):
    job_id:Optional[int]
    build_id:Optional[int]
    run_time:Optional[str]
    run_result:Optional[str]
    report_id:Optional[int]

