from typing import List, Optional
from pydantic import BaseModel

class ModuleItem(BaseModel):
    module_name:str
    module_code:str

'''项目信息'''
class ProjectBase(BaseModel):
    id:Optional[int]

class ProjectSave(ProjectBase):
    pro_name:Optional[str]
    pro_code:Optional[str]
    pro_type:Optional[int]
    remark:Optional[str]

    class Config:
        orm_mode = True



