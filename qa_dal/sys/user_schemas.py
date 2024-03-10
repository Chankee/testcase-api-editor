from typing import List, Optional,Union
from pydantic import BaseModel

'''用户表'''
class UserBase(BaseModel):
    id:int

class UserSave(UserBase):
    user_name:Optional[str]
    tel:Optional[str]
    email:Optional[str]
    pro_fun:Optional[str]
    user_state:Optional[int]
    remark:Optional[str]
    roles_id:Optional[int]
    pro_code_list:Optional[Union[str,list]]

    class Config:
        orm_mode = True



