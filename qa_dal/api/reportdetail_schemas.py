from typing import List, Optional
from pydantic import BaseModel

'''测试明细'''
class ReportDetailBase(BaseModel):
    id:Optional[int]


class ReportDetailSave(ReportDetailBase):
    case_name:Optional[str]
    api_name: Optional[str]
    case_id: Optional[int]
    url: Optional[str]
    method: Optional[str]
    header: Optional[str]
    preconditions:Optional[str]
    request_body:Optional[str]
    business_id:Optional[int]
    result_info:Optional[str]
    report_num:Optional[str]
    response_body:Optional[str]
    assert_param:Optional[str]
    extract_param:Optional[str]
    data_group_num:Optional[str]
    data_id:Optional[int]
    run_time:Optional[str]
    run_host:Optional[str]
    
    class Config:
        orm_mode = True

