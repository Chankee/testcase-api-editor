from typing import List, Optional,Union
from pydantic import BaseModel

'''定时任务'''
class JobBase(BaseModel):
    id:Optional[int]


class JobSave(JobBase):
    job_name:Optional[str]
    business_list: Optional[Union[list,str]]
    notice: Optional[Union[list,str]]
    run_time: Optional[str]
    run_state: Optional[int]
    run_type: Optional[int]
    pro_code:Optional[str]
    select_business:Optional[Union[list,str]]
    dingding_token:Optional[str]

    class Config:
        orm_mode = True

