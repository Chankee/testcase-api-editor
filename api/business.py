#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：业务流

from fastapi import APIRouter
from typing import Optional,List,Union
from qa_dal import qa_uitls
from qa_api_dal.api.business_dal import Business_Dal
from qa_api_dal.qasys.pm_dal import Module_Dal
from pydantic import BaseModel
from api.run_case_uitls.run_business import Run_Business

from qa_dal.models import Business,ProModule,Case,ApiData
from sqlalchemy.orm import Session
from sqlalchemy import func
from qa_dal.database import get_api_db
from qa_dal.api import business_schemas
from fastapi import Depends
import json

router = APIRouter(
    prefix="/api/business",
    tags=["系统设置"]
)


@router.get("/list")
async def search_businesslist(pro_code:str='',business_name:str='',create_name:str='',
                              module_code:str='',b_state:int=-1,page_num:int=1,page_size:int=10,
                              db:Session=Depends(get_api_db)):
    '''
    查询业务流
    :param pro_code:
    :param business_name:
    :param create_name:
    :param module_code:
    :param page_num:
    :param page_size:
    :return:
    '''

    try:
        sql_param = [Business.pro_code == pro_code, Business.isdelete == 0]

        # 追加sql条件
        if business_name.__len__() != 0: sql_param.append(Business.business_name.like('%{}%'.format(business_name)))
        if create_name.__len__() != 0: sql_param.append(Business.create_name==create_name)
        if module_code.__len__() != 0: sql_param.append(Business.module_code==module_code)
        if b_state in (0, 1): sql_param.append(Business.b_state==b_state)

        result=db.query(Business).filter(*sql_param).order_by(Business.id.desc()).all()

        result_list=[]
        for rl in result:
            result_detail=rl.to_json()
            # 获取步骤信息
            setp_item = []
            if rl.business_detail != '[]':
                for setp in eval(rl.business_detail):
                    case_info=db.query(Case.case_name).filter(Case.id==setp).first()
                    if case_info==None: continue
                    setp_item.append(case_info.case_name)
            result_detail['setp_item']=setp_item
            result_detail['detail_sum']=[0,eval(rl.business_detail).__len__()][rl.business_detail != '[]']
            result_list.append(result_detail)

        return qa_uitls.page_info(result_list, page_num, page_size)
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/detail")
async def get_businessinfo(id:int,db:Session=Depends(get_api_db)):
    '''
    读取业务流
    :param id:
    :return:
    '''
    try:
        return {'code':200,'msg':db.query(Business).filter(Business.id==id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del")
async def del_businessinfo(bi:business_schemas.BusinessBase,db:Session=Depends(get_api_db)):
    '''
    删除业务流
    :param gl:
    :return:
    '''
    try:
        business=db.query(Business).filter(Business.id==bi.id).first()
        if business==None: return {'code':201,'msg':'无效ID！'}
        if business.business_detail not in ('[]',''): return {'code':202,'msg':'业务流里存在步骤，请先清空再删除！'}
        business.isdelete=1
        db.commit()
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/save")
async def save_business(bi:business_schemas.BusinessSave,db:Session=Depends(get_api_db)):
    '''
    保存业务流
    :param bi:
    :return:
    '''
    try:
        if bi.id==0:
            db_item=Business(**bi.dict())
            db.add(db_item)
            db.commit() #添加

        else:
            business = db.query(Business).filter(Business.id == bi.id).first()
            if business == None: return {'code': 201, 'msg': '无效ID！'}
            business.business_name=bi.business_name
            business.module_code = bi.module_code
            business.business_type = bi.business_type
            db.commit() #编辑

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.get("/tree",response_model=Union[List[business_schemas.BusinessModule],business_schemas.TreeListShow])
async def get_business_tree(pro_code:str,db:Session=Depends(get_api_db)):
    '''
    获取业务流树
    :param pro_code:
    :return:
    '''
    try:
        total_count=0
        tree_list = [{'id': '', 'label':'全部业务流',
                       'total': 0, 'children': []}]

        result=db.query(ProModule).filter(ProModule.pro_code==pro_code,ProModule.isdelete==0).all()

        tree_detail=[]
        for rl in result:
            detail_count=len(rl.business_item)
            if detail_count==0: continue
            total_count+=detail_count
            tree_detail.append({'id':rl.module_code,'label':rl.module_name,'total':detail_count})
        tree_list[0]['children']=tree_detail
        tree_list[0]['total']=total_count

        return {'code':200,'msg':tree_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}






#业务明细调试
class RunDetailItem(BaseModel):
    id:int
    detail_id_list:list
    pro_code:str




#业务明细保存
class SaveDetailItem(BaseModel):
    id:int
    case_id: Optional[int]
    case_name: Optional[str]
    detail_name: Optional[str]
    wait_time: Optional[int]
    request_body: Optional[dict]
    url_param: Optional[str]
    header: Optional[str]
    preconditions: Optional[str]
    extract_param: Optional[str]
    assert_param: Optional[str]
    api_id: Optional[int]



# @router.get("/detail_data_list")
# async def detail_data_list(id:int):
#     try:
#         business_info = Business_Dal().get_business_info(id)
#         result={'business_name':'','detail':[]}
#         result['business_name']=business_info['business_name']
#         for detail_id in eval(business_info['business_detail']):
#             case=Case_Dal().get_case_data(detail_id)
#             result['detail'].append({'case_name':case['case_name'],'request_body':case['request_body']})
#         return {'code':200,'msg':result}
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}

@router.get("/detail_data_list")
async def detail_data_list(id:int,db:Session=Depends(get_api_db)):
    try:
        business_info = db.query(Business).filter(Business.id==id).first()
        result={'business_name':'','detail':[]}
        result['business_name']=business_info.business_name
        for case_id in eval(business_info.business_detail):
            case=db.query(Case,ApiData.request_body).filter(Case.id==ApiData.case_id,ApiData.data_group_num=='df',Case.id==case_id).first()
            result['detail'].append({'case_name':case.Case.case_name,'request_body':case.ApiData.request_body})
        return {'code':200,'msg':result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


class RunBusiness(BaseModel):
    pro_code:str
    business_id:int
    select_data:str


@router.post("/run_business")
def run_business(rb:RunBusiness,db:Session=Depends(get_api_db)):
    '''
    执行业务流
    :param rb:
    :param db:
    :return:
    '''
    try:
        Run_Business(rb.pro_code).run_business(rb.pro_code,rb.business_id,rb.select_data,db)
        return {'code':200,'msg':'执行完毕！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/module_business")
async def module_business(pro_code:str):
    '''
    项目模块业务流
    :param pro_code:
    :return:
    '''
    try:
        return_list = []
        result_info = Business_Dal().get_module_business(pro_code)
        module_list = list(set([ri['module_code'] for ri in result_info]))
        for ml in module_list:
            ml_item = {}
            ml_item['label'] = Module_Dal().get_modulename_by_code(ml)
            ml_item['value'] = ml
            ml_item['children'] = [{'label': ri['business_name'], 'value': ri['id']} for ri in result_info if
                                   ri['module_code'] == ml]
            return_list.append(ml_item)
        return {'code': 200, 'msg': return_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}

