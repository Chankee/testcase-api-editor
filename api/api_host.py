#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口host

from fastapi import APIRouter
from qa_dal.models import ApiHost
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from qa_dal.api import apihost_schemas
from fastapi import Depends

router = APIRouter(
    prefix="/apihost",
    tags=["接口环境"]
)


@router.get("/list")
async def get_hostlist(pro_code:str='',db:Session=Depends(get_api_db)):
    '''
    环境列表
    :param pro_code:
    :param db:
    :return:
    '''

    try:
        return {'code':200,'msg':db.query(ApiHost).filter(ApiHost.pro_code==pro_code,ApiHost.isdelete==0).order_by(ApiHost.id.desc()).all()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def get_hostinfo(id:int,db:Session=Depends(get_api_db)):
    '''
    读取环境信息
    :param id:
    :param db:
    :return:
    '''
    try:
        return {'code':200,'msg':db.query(ApiHost).filter(ApiHost.id==id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del")
async def del_hostinfo(item:apihost_schemas.ApiHostBase,db:Session=Depends(get_api_db)):
    '''
    删除环境信息
    :param item:
    :param db:
    :return:
    '''
    try:
        host=db.query(ApiHost).filter(ApiHost.id==item.id).first()
        if host==None: return {'code':201,'msg':'无效ID！'}
        host.isdelete=1
        db.commit()
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/save")
async def save_host(item:apihost_schemas.ApiHostSave,db:Session=Depends(get_api_db)):
    '''
    添加或编辑host
    :return:
    '''
    try:
        if item.id==0:
            db_item = ApiHost(**item.dict())
            db.add(db_item)
            db.commit() #添加
        else:
            host=db.query(ApiHost).filter(ApiHost.id==item.id).first()
            if host==None: return {'code':201,'msg':'无效ID！'}

            host.host_name = item.host_name
            host.test_host = item.test_host
            host.uat_host = item.uat_host
            host.prd_host = item.prd_host
            host.pro_code = item.pro_code
            host.remark = item.remark
            db.commit()
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



