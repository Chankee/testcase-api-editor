from typing import List, Optional,Dict,Union
from pydantic import BaseModel,Field

'''接口信息'''
class ApiBase(BaseModel):
    id:Optional[int]


class ApiSave(ApiBase):
    api_name:Optional[str]
    method: Optional[str]
    header: Optional[Union[str,dict]]
    url: Optional[str]
    host: Optional[str]
    request_body: Optional[Union[str,dict]]
    response_body: Optional[Union[str,dict]]
    dbsource: Optional[int]
    update_time: Optional[str]
    pro_code: Optional[str]
    module_code: Optional[str]
    tag: Optional[str]
    remark: Optional[str]
    host_id: Optional[int]
    dev_name: Optional[str]

    class Config:
        orm_mode = True



'''接口列表模型'''
class CaseItem(BaseModel):
    id:int
    case_name:str
    isdelete:int

    class Config:
        orm_mode = True


class ApiItem(ApiBase):
    api_name: Optional[str]
    method: Optional[str]
    url: Optional[str]
    tag: Optional[str]
    host_id: Optional[int]
    dbsource: Optional[int]
    module_code:Optional[str]
    case_item: List[CaseItem]=[]

    class Config:
        orm_mode = True


class ApiListShow(BaseModel):
    code:int
    msg:Union[List[ApiItem],str]
    total:int


'''项目模块接口'''
class ApiBaseItem(BaseModel):
    id:int
    api_name:str
    isdelete:int

    class Config:
        orm_mode = True


class ModuleItem(BaseModel):
    module_code: str
    module_name: str
    api_item: List[ApiBaseItem] = []

    class Config:
        orm_mode = True


class LabelBase(BaseModel):
    label: str
    value: Union[str, int]

    class Config:
        orm_mode = True

class LabelItem(LabelBase):
    children:List[LabelBase]=[]

    class Config:
        orm_mode = True

class ApiModule(BaseModel):
    '''根据模型显示接口信息'''
    code:int
    msg:Union[List[LabelItem],str]

    class Config:
        orm_mode = True