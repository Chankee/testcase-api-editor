from typing import List, Optional,Union
from pydantic import BaseModel

'''roles'''
class RolesBase(BaseModel):
    id:Optional[int]

class RolesSave(RolesBase):
    roles_name: Optional[str]
    pro_code:Optional[str]
    pro_code_list: Optional[Union[str,list]]
    menus_json: Optional[str]
    check_key: Optional[str]
    remark: Optional[str]

    class Config:
        orm_mode = True

