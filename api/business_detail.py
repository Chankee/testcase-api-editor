#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：业务流明细

from fastapi import APIRouter
from typing import Optional,List,Union
from qa_api_dal.api.business_dal import Business_Dal
from qa_api_dal.qasys.pm_dal import Module_Dal
from qa_api_dal.api.api_dal import Api_Dal
from qa_api_dal.case.case_dal import Case_Dal
from pydantic import BaseModel
from api.run_case_uitls.run_business import Run_Business

from qa_dal.models import Business,Case
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from qa_dal.api import business_schemas
from fastapi import Depends
import json
from uitls.log import LOG

router = APIRouter(
    prefix="/api/business",
    tags=["业务流明细"]
)

### 业务流模型
class BusinessItem(BaseModel):
    id: int
    business_name: Optional[str]
    b_state: Optional[int]
    business_detail: Optional[str]
    create_name: Optional[str]
    pro_code: Optional[str]
    module_code:Optional[str]


@router.get("/business_detail")
async def get_business_detail(business_id:int,db:Session=Depends(get_api_db)):
    '''
    获取业务明细
    :param business_id:
    :return:
    '''
    try:

        business = db.query(Business).filter(Business.id == business_id).first()
        if business == None: return {'code': 200, 'msg': '无效ID！'}

        result = {'business_name': '', 'business_detail': []}
        result['business_name']=business.business_name
        if business.business_detail in (None,'[]',''): return {'code':200,'msg':result} #没有步骤则返回空

        result['business_detail']=format_detail(1,eval(business.business_detail),db)

        return {'code':200,'msg':result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


def format_detail(type,detail_list,db:Session):
    '''
    格式化详情
    :param type: 1为加载，非1为解格式
    :param detail_list:
    :return:
    '''
    result=[]
    if type==1:
        for dl in detail_list:
            case_info=db.query(Case.case_name,Case.id).filter(Case.id==dl).first()
            if case_info==None: continue
            result.append({"case_id":case_info.id,"case_name":case_info.case_name})
    else:
        result=[dl['case_id'] for dl in detail_list]

    return result


@router.post("/change_detail_order")
async def change_detail(bi:business_schemas.BusinessSave,db:Session=Depends(get_api_db)):
    '''
    修改业务步骤顺序
    :param bi:
    :return:
    '''
    try:
        business = db.query(Business).filter(Business.id == bi.id).first()
        if business == None: return {'code': 200, 'msg': '无效ID！'}
        business.business_detail=json.dumps(format_detail(2,bi.business_detail,db))
        db.commit()
        return {'code': 200,'msg':'业务明细顺序更新成功!'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.post("/run_detail")
async def rundetail(rd:business_schemas.BusinessSave,db:Session=Depends(get_api_db)):
    '''
    批量运行业务明细
    :param rd:
    :return:
    '''
    try:
        Run_Business(rd.pro_code).run_detail(rd.pro_code,rd.id,rd.business_detail,db)
        return {'code': 200, 'msg': True}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




from uitls.log import LOG
@router.post("/del_detail")
async def del_detail(item:business_schemas.DelBusiness,db:Session=Depends(get_api_db)):
    try:
        business_info=db.query(Business).filter(Business.id==item.business_id).first()
        detail_list=eval(business_info.business_detail)
        detail_list.remove(item.id)  #删除步骤
        business_info.business_detail=json.dumps(detail_list)   #保存步骤
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/get_treecase")
async def tree_case(pro_code:str):
    '''
    导入用例
    :param pro_code:
    :return:
    '''
    try:
        return_list = []
        result_info = Api_Dal().module_api(pro_code)
        # LOG().info(result_info)
        module_list = list(set([ri['module_code'] for ri in result_info]))
        for ml in module_list:
            ml_item = {}
            ml_item['label'] = Module_Dal().get_modulename_by_code(ml,pro_code)
            ml_item['value'] = ml
            #第二层
            ml_item['children'] = [{'label': ri['api_name'], 'value': ri['id']} for ri in result_info if
                                   ri['module_code'] == ml]
            #第三层
            for child in ml_item['children']:
                child['children']=[{'label':cl['case_name'],'value':cl['id']} for cl in Case_Dal().api_case_list(child['value'])]
            return_list.append(ml_item)
        return {'code': 200, 'msg':return_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


class InsertDetail(BaseModel):
    business_id:int
    case_list:list


@router.post("/add_detail")
async def add_detail(id:InsertDetail):
    try:
        detail_list=eval(Business_Dal().get_business_info(id.business_id)['business_detail'])
        for cl in id.case_list:
            detail_list.append(cl[2])   #添加到业务里
        Business_Dal().update_detail([str(detail_list),id.business_id])  #保存步骤
        return {'code': 200, 'msg':"操作成功！"}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





