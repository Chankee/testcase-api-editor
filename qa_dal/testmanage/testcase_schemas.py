from typing import List, Optional,Union
from pydantic import BaseModel

'''测试用例'''
class TestCaseBase(BaseModel):
    id:Optional[int]

class TestCaseCreate(BaseModel):
    pro_code:Optional[str]
    case_name: Optional[str]
    case_level: Optional[str]
    tester_remark:Optional[str]
    front_info: Optional[str]
    case_step: Optional[str]
    case_result: Optional[str]
    create_name: Optional[str]
    version_demand:Optional[list]
    sort_id:Optional[int]


class TestCaseSave(TestCaseBase):
    pro_code: Optional[str]
    case_name: Optional[str]
    case_level: Optional[str]
    tester: Optional[str]
    front_info: Optional[str]
    case_step: Optional[str]
    case_result: Optional[str]
    version_demand:Optional[list]
    tester_remark: Optional[str]
    case_type: Optional[int]

    class Config:
        orm_mode = True

class TestSort(BaseModel):
    '''修改排序号'''
    sort_num:Optional[dict]

    class Config:
        orm_mode = True


class TestCaseReview(TestCaseBase):
    '''修改审核状态'''
    ids:Optional[list]
    review_state:Optional[int]

    class Config:
        orm_mode = True


class TestCaseUser(BaseModel):
    '''用例人员分配'''
    case_id_list:list=[]
    android_name:Optional[str]
    ios_name:Optional[str]
    manage_name:Optional[str]
    h5_name:Optional[str]
    applet_name:Optional[str]
    server_name:Optional[str]
    tester:Optional[str]

    class Config:
        orm_mode = True


class TestCaseRecovery(BaseModel):
    '''回收站'''
    pro_code:Optional[str]
    id:list=[]
    type:int    #1为回收，0为恢复
    recovery_people:Optional[str] #操作人员

    class Config:
        orm_mode = True


class TestCaseDel(BaseModel):
    '''删除用例'''
    pro_code:Optional[str]
    id:list=[]

class TestCaseMove(BaseModel):
    '''移动版本用例和发布性用例'''
    pro_code:Optional[str]
    case_id_list:list=[]
    version_demain:Optional[list]   #[0]版本ID  [1]模块ID

    class Config:
        orm_mode = True


class TestCaseRun(TestCaseBase):
    '''执行用例'''
    run_name:str
    run_result:str
    run_remark:str
    pro_fun:str #项目职责

    class Config:
        orm_mode = True

class ReleaseCaseUser(BaseModel):
    '''发布性用例测试人员分配'''
    case_id_list: list = []
    tester: str

    class Config:
        orm_mode = True



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



'''发布性用例计划显示'''
class PlanCaseItem(BaseModel):
    id: int
    case_name:str

    class Config:
        orm_mode = True


class PlanDemand(BaseModel):
    id:int
    demand_name:str
    case_item:List[PlanCaseItem]=[]

    class Config:
        orm_mode = True

class PlanBase(BaseModel):
    label:str
    value:int

    class Config:
        orm_mode = True

class PlanDetail(PlanBase):
    children:List[PlanBase]=[]

    class Config:
        orm_mode = True

class PlanReturn(BaseModel):
    code:int
    msg:Union[List[PlanDetail],str]


'''切换sheet表单'''
class SwitchSheet(BaseModel):
    file_path:str
    sheet_name:str

'''导入数据'''
class ImportCaseItem(BaseModel):
    pro_code:str
    version_demand:Optional[list]
    create_name:str
    case_table: Optional[list]

class CopyCaseItem(BaseModel):
    pro_code:Optional[str]
    case_id_list:list
    id_path:list
    create_name:str
