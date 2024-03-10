from typing import List, Optional,Union
from pydantic import BaseModel

class DataAsset(BaseModel):
    id:int
    case_id:int
    assert_param:Optional[Union[list,str]]
    assert_list:Optional[Union[list,str]]
    type:Optional[int] # 1为修改所有断言，2为修改选择断言

class DataBase(BaseModel):
    id:int

class SaveData(DataBase):
    data_name:str
    request_body:Union[str,list,dict]
    run_host: str