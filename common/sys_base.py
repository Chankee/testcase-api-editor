#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：基础数据
from fastapi import APIRouter
from fastapi import Depends
from qa_dal.database import get_api_db,get_sso_db
from sqlalchemy.orm import Session
from qa_dal.models import Project,ProModule,User

router = APIRouter(
    prefix="/base",
    tags=["基础数据"]
)

@router.get("/project")
async def get_fullpm(db: Session = Depends(get_sso_db)):
    '''
    所有项目的名称和ID，下拉专用
    :param db:
    :return:
    '''
    try:
        result=db.query(Project).filter(Project.isdelete==0,Project.pro_code!='hashbox').order_by(Project.id.desc()).all()
        return {'code':200,'msg':result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/promodule")
async def get_fullpm(pro_code:str='',db: Session = Depends(get_api_db)):
    try:
        module_list=db.query(ProModule.module_name,ProModule.module_code).filter(ProModule.pro_code==pro_code,ProModule.isdelete==0).order_by(ProModule.id.desc()).all()
        return {'code':200,'msg':[{'label':ml.module_name,'value':ml.module_code} for ml in module_list]}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/users")
def get_users(pro_code:str='',pro_fun:str='',db: Session = Depends(get_sso_db)):
    try:
        sql_param_list = [User.isdelete == 0]  # 基础搜索条件
        if pro_code.__len__()>0: sql_param_list.append(User.pro_code_list.like('%{}%'.format(pro_code)))
        if pro_fun.__len__() > 0: sql_param_list.append(User.pro_fun.like('%{}%'.format(pro_fun)))
        return {'code':200,'msg':db.query(User).filter(*sql_param_list).order_by(User.id.desc()).all()}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}








