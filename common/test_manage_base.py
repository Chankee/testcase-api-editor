from fastapi import APIRouter
from fastapi import Depends
from qa_dal.database import get_case_db
from sqlalchemy.orm import Session
from qa_dal.models import Version,TestCase,Demand
from qa_dal.testmanage import version_schemas
from typing import List,Union

router = APIRouter(
    prefix="/base",
    tags=["基础数据"]
)


@router.get("/version")
async def get_full_version(pro_code:str,isrelease:int=-1,db: Session = Depends(get_case_db)):
    '''
    获取状态
    :param pro_code:
    :param version_state:0为版本用例，1为发布性用例
    :param db:
    :return:
    '''
    try:
        sql_param=[Version.pro_code==pro_code,Version.isdelete==0]
        if isrelease in (0,1): sql_param.append(Version.isrelease==isrelease)

        result=db.query(Version).filter(*sql_param).order_by(Version.id.desc()).all()
        return {'code':200,'msg':result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/version_cascader",response_model=Union[List[version_schemas.VersionCascader],version_schemas.VersionCascaderList])
async def get_version_cascader(pro_code:str,isrelease:int=-1,db: Session = Depends(get_case_db)):
    '''
    关联选择
    :param pro_code:
    :param isrelease:
    :param db:
    :return:
    '''
    try:
        sql_param=[Version.pro_code==pro_code,Version.isdelete==0]
        if isrelease in (0,1): sql_param.append(Version.isrelease==isrelease)
        version_list=db.query(Version).filter(*sql_param).order_by(Version.id.desc()).all()

        result_list=[]
        for version in version_list:
            if len(version.demand_item)==0: continue
            detail={}
            detail['label']=version.version_name
            detail['value']=version.id
            detail['children']=[{'label':demand.demand_name,'value':demand.id} for demand in version.demand_item]
            result_list.append(detail)

        return {'code': 200, 'msg': result_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/version_case_tag")
async def get_version_case_tag(version_id:int=0,pro_code:str='',db: Session = Depends(get_case_db)):
    '''
    版本用例标签
    :param version_id:
    :param db:
    :return:
    '''
    try:
        sql_param=[TestCase.isdelete==0,TestCase.isrecovery==0]
        if len(pro_code)>0:sql_param.append(TestCase.pro_code==pro_code)
        if version_id>0: sql_param.append(TestCase.version_id==version_id)
        result=db.query(TestCase.tag).filter(*sql_param).group_by(TestCase.tag).all()
        return {'code': 200, 'msg': result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/demand")
async def get_demand(version_id:int=-1,db: Session = Depends(get_case_db)):
    '''
    版本需求
    :param version_id:
    :param db:
    :return:
    '''
    sql_param=[Demand.isdelete==0]
    if version_id>0: sql_param.append(Demand.version_id==version_id)
    try:
        result=db.query(Demand).filter(*sql_param).order_by(Demand.id.desc()).all()
        return {'code': 200, 'msg': result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




