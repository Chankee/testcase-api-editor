from typing import List, Optional
from pydantic import BaseModel

'''全局变量'''
class GlobalParamBase(BaseModel):
    id:Optional[int]


class GlobalParamSave(GlobalParamBase):
    global_name:Optional[str]
    global_param: Optional[str]
    param_value: Optional[str]
    module_code: Optional[str]
    pro_code: Optional[str]
    global_type: Optional[int]
    code_info:Optional[str]
    create_name:Optional[str]
    param_type:Optional[str]

    class Config:
        orm_mode = True

