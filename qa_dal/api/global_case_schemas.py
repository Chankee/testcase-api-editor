from typing import List, Optional, Union
from pydantic import BaseModel

'''全局用例'''
class GlobalCaseBase(BaseModel):
    id:Optional[int]


class GlobalCaseSave(GlobalCaseBase):
    global_case_name:Optional[str]
    join_case_id:Optional[Union[list,int]]
    assert_case_id: Optional[Union[list,int]]
    param_value: Optional[str]
    remark: Optional[str]
    pro_code: Optional[str]
    isdelete: Optional[int]
    join_case_info:Optional[Union[list,str]]
    assert_case_info: Optional[Union[list,str]]

    class Config:
        orm_mode = True

