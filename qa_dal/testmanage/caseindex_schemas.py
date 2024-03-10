from typing import List, Optional
from pydantic import BaseModel

class SaveIndex(BaseModel):
    id: Optional[int]
    pro_code: Optional[str]
    name: Optional[str]
    parent_id_path: Optional[str]
    type: Optional[int]
    level: Optional[int]
    remark: Optional[str]

    class Config:
        orm_mode = True

class MoveIndex(BaseModel):
    pro_code:Optional[str]
    base_id:Optional[int]   #原始ID
    target_id:Optional[int] #目标ID

class DelIndex(BaseModel):
    pro_code:Optional[str]
    id_path:Optional[str]
    recovery_people:Optional[str]


