from typing import List, Optional,Union
from pydantic import BaseModel

'''业务流'''
class BusinessBase(BaseModel):
    id:Optional[int]


class BusinessSave(BusinessBase):
    business_name:Optional[str]
    business_type: Optional[int]
    b_state: Optional[int]
    business_detail: Optional[Union[str,list]]
    create_name: Optional[str]
    pro_code: Optional[str]
    module_code:Optional[str]
    
    class Config:
        orm_mode = True

class DelBusiness(BusinessBase):
    business_id:Optional[int]

'''树形结构'''
class BusinessItem(BaseModel):
    business_name:str
    isdelete:int

    class Config:
        orm_mode = True

class BusinessModule(BaseModel):
    module_name:str
    module_code:str
    business_item:List[BusinessItem]=[]

    class Config:
        orm_mode = True

class TreeItem(BaseModel):
    id:str
    label:str
    total:int

class TreeList(TreeItem):
    children:List[TreeItem]=[]

class TreeListShow(BaseModel):
    code:int
    msg:Union[List[TreeList],str]



