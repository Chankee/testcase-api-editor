from typing import List, Optional
from pydantic import BaseModel

'''菜单表'''
class MenusBase(BaseModel):
    id:Optional[int]

class MenusSave(MenusBase):
    menus_name:Optional[str]
    tag: Optional[str]
    ico: Optional[str]
    level: Optional[int]
    parent_id: Optional[int]
    url: Optional[str]
    remark: Optional[str]
    sort_num: Optional[int]
    issys: Optional[int]

    class Config:
        orm_mode = True



