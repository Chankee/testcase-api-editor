#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：版本需求接口

from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import version_schemas
from qa_dal.database import get_case_db
from sqlalchemy.orm import Session
from qa_dal.models import Version,Demand
from qa_dal import qa_uitls

router = APIRouter(
    prefix="/tm/version",
    tags=["测试用例-版本需求"]
)


@router.get("/list")
async def search_version_list(pro_code:str='',version_name:str='',page_num:int=1,page_size:int=10,db:Session=Depends(get_case_db)):
    '''
    查询版本
    :param pro_code:
    :param version_name:
    :param page_num:
    :param page_size:
    :param db:
    :return:
    '''
    try:

        sql_param_list = [Version.pro_code == pro_code, Version.isdelete == 0, Version.isrelease == 0]  # 基础搜索条件
        if version_name.__len__() > 0: sql_param_list.append(
            Version.version_name.like('%{}%'.format(version_name)))  # 追加条件

        result=db.query(Version).filter(*sql_param_list).order_by(Version.id.desc()).all()
        return qa_uitls.page_info(result, page_num,page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/save")
async def add_version(version_items: version_schemas.VersionSave, db:Session=Depends(get_case_db)):
    '''
    创建版本
    :param version:
    :param db:
    :return:
    '''
    try:
        if version_items.id==0:
            db_item = Version(**version_items.dict())
            db.add(db_item)
            db.commit()

        else:
            version = db.query(Version).filter(Version.id == version_items.id).first()

            if version == None: return {'code': 201, 'msg': '无效ID!'}

            version.version_name = version_items.version_name
            version.dingding_conf = version_items.dingding_conf
            version.remark = version_items.remark
            db.commit()

        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/del")
async def del_version(version_items: version_schemas.VersionBase, db:Session=Depends(get_case_db)):
    '''
    删除版本
    :param version:
    :param db:
    :return:
    '''
    try:

        version = db.query(Version).filter(Version.id == version_items.id).first()

        if version == None: return {'code': 201, 'msg': '无效ID!'}
        if db.query(Demand).filter(Demand.version_id==version_items.id,Demand.isdelete==0).count()>0: return {'code':202,'msg':'该版本已存在需求模块，请先删除需求模块！'}

        version.isdelete = 1
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def get_version_detail(id:int,db:Session=Depends(get_case_db)):
    '''
    版本详情信息
    :param id:
    :param db:
    :return:
    '''
    try:

        return {'code': 200, 'msg': db.query(Version).filter(Version.id == id).first()}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



