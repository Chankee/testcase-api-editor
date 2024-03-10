from typing import List, Optional,Union
from pydantic import BaseModel

class HostItem(BaseModel):
    id:int
    host_name:str

    class Config:
        orm_mode = True

class ModuleItem(BaseModel):
    module_code:str
    module_name:str

    class Config:
        orm_mode = True

'''接口配置'''
class ApiConfigBase(BaseModel):
    id:Optional[int]


class ApiConfigSave(ApiConfigBase):
    conf_name:Optional[str]
    conf_type: Optional[int]
    conf_info: Optional[str]
    module_code: Optional[str]
    host_id: Optional[int]
    pro_code: Optional[str]
    remark:Optional[str]

    class Config:
        orm_mode = True

class ApiConfItem(ApiConfigBase):
    conf_name: str
    conf_type: int
    conf_info: str
    module_code: str
    host_id: int
    pro_code: str
    remark: str
    host_item: HostItem
    module_item:ModuleItem

    class Config:
        orm_mode = True

class ApiConfListShow(BaseModel):
    code:int
    msg:Union[List[ApiConfItem],str]
    total:int

    class Config:
        orm_mode = True
