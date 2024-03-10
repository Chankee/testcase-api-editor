from typing import List, Optional
from pydantic import BaseModel

'''项目模块信息'''
class ProModuleBase(BaseModel):
    id:Optional[int]

class ProModuleSave(ProModuleBase):
    module_name:Optional[str]
    module_code:Optional[str]
    pro_code:Optional[str]
    remark:Optional[str]

    class Config:
        orm_mode = True




