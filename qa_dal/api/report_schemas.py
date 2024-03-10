from typing import List, Optional
from pydantic import BaseModel

'''测试报告'''
class ReportBase(BaseModel):
    id:Optional[int]


class ReportSave(ReportBase):
    report_num:Optional[str]
    total_count: Optional[int]
    ok_count: Optional[int]
    fail_count: Optional[int]
    error_count: Optional[int]
    skip_count: Optional[int]
    business_id:Optional[int]
    summary_num:Optional[str]
    summary_time:Optional[str]
    report_type:Optional[int]
    run_total:Optional[str]
    
    class Config:
        orm_mode = True

