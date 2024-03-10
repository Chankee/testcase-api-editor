from typing import List, Optional
from pydantic import BaseModel

'''需求模块'''
class DemandBase(BaseModel):
    id:Optional[int]



class DemandSave(DemandBase):
    demand_name: Optional[str]
    module_code: Optional[str]
    tester: Optional[str]
    issuspend: Optional[int]
    plan_start: Optional[str]
    plan_end: Optional[str]
    version_id: Optional[int]
    jira_num: Optional[str]
    jira_state: Optional[str]
    remark: Optional[str]
    pro_code: Optional[str]

    class Config:
        orm_mode = True

