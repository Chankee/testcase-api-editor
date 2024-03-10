from typing import List, Optional,Union
from pydantic import BaseModel

'''用例信息'''
class CaseBase(BaseModel):
    id:Optional[int]

class CaseData(BaseModel):
    data_group_name: Optional[str]
    business_id: Optional[int]

    case_id: Optional[int]
    data_group_num: Optional[str]
    data_name: Optional[str]
    assert_list: Optional[str]


class CaseCreate(CaseBase):
    api_id:Optional[Union[list,int]]
    case_name:Optional[str]
    url_param: Optional[str]
    header: Union[dict,str]
    extract_param: Optional[Union[list,str]]
    preconditions: Optional[str]
    header_param: Optional[Union[list,str]]
    join_param: Optional[Union[list,str]]
    business_list: Optional[int]
    create_name: Optional[str]
    assert_param: Optional[Union[list,str]]
    wait_time: Optional[int]
    pro_code: Optional[str]
    request_body: Optional[Union[dict, str]]
    run_host: Optional[str]
    assert_list: Optional[Union[list,str]]


    class Config:
        orm_mode = True


class CaseUpdate(CaseBase):
    case_name:Optional[str]
    url_param: Optional[str]
    header: Union[dict,str]
    extract_param: Optional[Union[list,str]]
    preconditions: Optional[str]
    header_param: Optional[Union[list,str]]
    join_param: Optional[Union[list,str]]
    business_list: Optional[int]
    assert_param: Optional[Union[list,str]]
    wait_time: Optional[int]
    request_body: Optional[Union[dict, str]]
    run_host: Optional[str]
    assert_list: Optional[Union[list,str]]


    class Config:
        orm_mode = True

'''用例列表'''
class ApiItem(BaseModel):
    api_name:str
    method:str
    url:str

    class Config:
        orm_mode = True

class CaseList(BaseModel):
    id:int
    case_name:str
    create_name:str
    api_item:ApiItem

    class Config:
        orm_mode = True

class CaseListShow(BaseModel):
    code:int
    msg:Union[List[CaseList],str]
    total:int

    class Config:
        orm_mode = True



















