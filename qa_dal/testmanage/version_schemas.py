from typing import List, Optional,Union
from pydantic import BaseModel


class CaseItem(BaseModel):
    case_name:str
    version_id:int

    class Config:
        orm_mode = True


'''版本需求'''
class VersionBase(BaseModel):
    id:Optional[int]
    version_name: Optional[str]

class VersionSave(VersionBase):
    pro_code: str
    dingding_conf:Optional[str]
    remark:Optional[str]

    class Config:
        orm_mode = True

class VersionSelect(VersionBase):
    pass

    class Config:
        orm_mode = True

class VersionCase(BaseModel):
    id:int
    version_name:str
    case_item:List[CaseItem]=[]

    class Config:
        orm_mode = True


'''多级下拉'''
class DemandItem(BaseModel):
    id:int
    demand_name:str
    isdelete:int

    class Config:
        orm_mode = True


class VersionCascader(BaseModel):
    id:int
    version_name:str
    demand_item:List[DemandItem]=[]

    class Config:
        orm_mode = True

class CascaderItem(BaseModel):
    label:str
    value:int

    class Config:
        orm_mode = True

class CascaderList(CascaderItem):
    children:List[CascaderItem]=[]

    class Config:
        orm_mode = True

class VersionCascaderList(BaseModel):
    code:int
    msg:Union[List[CascaderList],str]