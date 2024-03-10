from typing import List, Optional,Union
from pydantic import BaseModel


'''用例列表树型结构'''
class DemandItem(BaseModel):
    id:int
    demand_name:str

    class Config:
        orm_mode = True

class VersionItem(BaseModel):
    id:int
    version_name:str
    isrelease:int
    demand_item:List[DemandItem]=[]

    class Config:
        orm_mode = True

class VersionModel(BaseModel):
    id:str
    name:str
    value:dict
    total:int
    children:list
    leaf:bool

    class Config:
        orm_mode = True

class VersionModelItem(BaseModel):
    id: str
    name: str
    value: dict
    total: int
    leaf:bool
    children: List[VersionModel]=[]

    class Config:
        orm_mode = True

class VersionTree(BaseModel):
    code:int
    msg:Union[List[VersionModelItem],str]



'''执行用例列表'''
class BugBase(BaseModel):
    bug_num:str
    bug_level:str
    report_name:str
    handle_name:str

    class Config:
        orm_mode = True

class RunTestBase(BaseModel):
    pass