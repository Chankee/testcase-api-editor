from typing import List, Optional
from pydantic import BaseModel

'''plan'''
class DevRunName(BaseModel):
    plan_id:Optional[int]
    case_id_list:Optional[list]
    name_list:Optional[list]
    pro_code:Optional[str]
    plan_version_id:Optional[int]

    class Config:
        orm_mode = True


class TesterRunName(BaseModel):
    plancase_id_list:Optional[list]
    tester:Optional[str]
    case_id_list:Optional[list]
    plan_id: Optional[int]

    class Config:
        orm_mode = True

class JoinTesterRunName(BaseModel):
    plan_id: Optional[int]
    join_plan_id:Optional[list]
    join_case_json:Optional[dict]
    pro_code:Optional[str]
    tester:Optional[str]

    class Config:
        orm_mode = True




class TesterRun(BaseModel):
    plancase_id_list:Optional[list]
    tester:Optional[str]
    result:Optional[str]

    class Config:
        orm_mode = True

class TesterRunOne(BaseModel):
    plan_id:Optional[int]
    result: Optional[str]
    result_remark: Optional[str]
    case_id:Optional[int]
    bug: Optional[str]

    class Config:
        orm_mode = True


class DelPlanCase(BaseModel):
    plan_id:Optional[int]
    case_id_list:Optional[list]

    class Config:
        orm_mode = True


class JoinDelPlanCase(BaseModel):
    plan_id: Optional[int]
    join_plan_id: Optional[list]
    join_case_json: Optional[dict]

    class Config:
        orm_mode = True


class DevRun(BaseModel):
    run_name:Optional[str]
    case_id_list:Optional[list]
    plan_id:Optional[int]
    result:Optional[str]

    class Config:
        orm_mode = True

class RunOneMySelf(BaseModel):
    plan_id:Optional[int]
    case_id:Optional[int]
    result:Optional[str]
    run_name:Optional[str]
    result_remark:Optional[str]

    class Config:
        orm_mode = True

class TestRunMyself(BaseModel):
    plan_id:Optional[int]
    case_id:Optional[int]
    run_json:Optional[dict]
    tester:Optional[str]
    bug: Optional[str]
    resut_remark: Optional[str]

    class Config:
        orm_mode = True


class TesterMyselfRun(BaseModel):
    run_name:Optional[str]
    pro_fun:Optional[str]
    plan_id:Optional[int]
    result:Optional[str]
    case_id_list: Optional[list]
    pro_code:Optional[str]

    class Config:
        orm_mode = True


class JoinTesterMyselfRun(BaseModel):
    plan_id: Optional[int]
    join_plan_id:Optional[list]
    run_name:Optional[str]
    pro_fun:Optional[str]
    result:Optional[str]
    join_case_json:Optional[dict]
    pro_code:Optional[str]

    class Config:
        orm_mode = True



class AddCase(BaseModel):
    plan_id:Optional[int]
    case_id_list:Optional[list]
    pro_code:Optional[str]
    plan_type:Optional[str]
    plan_version_id:Optional[int]
    tester: Optional[str]

    class Config:
        orm_mode = True


#计划版本
class SavePlanVersion(BaseModel):
    id:Optional[int]
    pro_code:Optional[str]
    version_name:Optional[str]

class DelPlanVersion(BaseModel):
    id:Optional[int]


#计划
class SavePlan(BaseModel):
    id:Optional[int]
    pro_code:Optional[str]
    name:Optional[str]
    type:Optional[str]
    plan_version_id:Optional[int]
    join_plan_id: Optional[list]

    class Config:
        orm_mode = True


#更换开发
class UpdateDev(BaseModel):
    plan_id:Optional[int]
    case_id_list:Optional[list]
    updev_name:Optional[str]
    run_name:Optional[str]











