from typing import List, Optional
from pydantic import BaseModel

'''bug'''
class BugBase(BaseModel):
    id:Optional[int]

class BugSave(BugBase):
    pro_code:Optional[str]
    version_id:Optional[int]
    demand_id:Optional[int]
    plan_id:Optional[int]
    case_id:Optional[int]
    bug_num:Optional[str]
    bug_level:Optional[str]
    report_name:Optional[str]
    handle_name:Optional[str]
    bug_state:Optional[str]

    class Config:
        orm_mode = True


class issue(BaseModel):
    pro_code: Optional[str]
    token: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    issuetype: Optional[str]
    component: Optional[str]
    priority: Optional[str]
    assignee: Optional[str]
    version: Optional[str]
    is_online: Optional[str]
    level: Optional[str]
    files: Optional[list]
    plan_id: Optional[int]
    case_id: Optional[int]
    demand_id: Optional[int]
    reporter: Optional[str]
    belong: Optional[str]
    notice: Optional[int]
