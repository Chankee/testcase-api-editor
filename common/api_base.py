from fastapi import APIRouter
from qa_dal.models import ApiHost,Api,ApiData,Case,Global
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from fastapi import Depends
import json

router = APIRouter(
    prefix="/base",
    tags=["基础数据"]
)


@router.get("/host")
async def get_host_list(pro_code:str,db: Session = Depends(get_api_db)):
    '''
    host下拉框
    :param pro_code:
    :return:
    '''
    try:
        result=[{'label':ga.host_name,'value':ga.id} for ga in db.query(ApiHost.id,ApiHost.host_name).
            filter(ApiHost.pro_code==pro_code,ApiHost.isdelete==0).all()]

        return {'code':200,'msg':result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/tag")
async def get_tag_list(pro_code:str,db: Session = Depends(get_api_db)):
    '''
    标签列表
    :param pro_code:
    :param db:
    :return:
    '''
    try:
        result=[tag.tag for tag in db.query(Api.tag).filter(Api.pro_code==pro_code,Api.isdelete==0).group_by(Api.tag).all()]
        return {'code':200,'msg':result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/group_data")
async def business_base(business_id:int,db:Session=Depends(get_api_db)):
    try:

        group_name_info=db.query(ApiData.data_group_name,ApiData.data_group_num,ApiData.id).filter(ApiData.business_id==business_id,ApiData.isdelete==0).group_by(ApiData.data_group_name).all()
        return {'code':200,'msg':group_name_info}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/param_list")
async def param_list(pro_code:str,db:Session=Depends(get_api_db)):
    case_list=db.query(Case.extract_param).filter(Case.pro_code==pro_code,Case.isdelete==0,Case.extract_param!='[]').order_by(Case.id.desc()).all()
    global_list=db.query(Global).filter(Global.pro_code==pro_code,Global.isdelete==0).order_by(Global.id.desc()).all()

    par_list=[]
    return_list=[{
        'label':'用例提取参数',
        'options':[]
        },
        {
        'label': '全局变量参数',
        'options': []
        }]
    #合并提取参数
    for case in case_list:
        par_list+=json.loads(case.extract_param)

    for par in par_list:
        return_list[0]['options'].append({'label':'{} [{}]'.format(par['extract_param'],par['extract_name']),'value':par['extract_param']})

    for gl in global_list:
        return_list[1]['options'].append({'label':'{} [{}]'.format(gl.global_param,gl.global_name),'value':gl.global_param})
    return {'code':200,'msg':return_list}
