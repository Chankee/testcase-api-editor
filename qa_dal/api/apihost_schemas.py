from typing import List, Optional
from pydantic import BaseModel

'''接口环境'''
class ApiHostBase(BaseModel):
    id:Optional[int]

class ApiHostSave(ApiHostBase):
    host_name:Optional[str]
    test_host: Optional[str]
    uat_host: Optional[str]
    prd_host: Optional[str]
    pro_code: Optional[str]
    remark: Optional[str]

    class Config:
        orm_mode = True



