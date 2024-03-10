#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：全局变量

from fastapi import APIRouter
from qa_dal import qa_uitls

from qa_dal.models import Global,Case
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from qa_dal.api import global_schemas
from fastapi import Depends

router = APIRouter(
    prefix="/api/global",
    tags=["系统设置"]
)


@router.get("/list")
async def search_globallist(pro_code:str='',module_code:str='0',global_name:str='',global_param:str='',global_type:int=0,page_num:int=1,page_size:int=10,db:Session=Depends(get_api_db)):
    '''
    查询全局变量
    :param pro_code:
    :param module_code:
    :param global_name:
    :param global_param:
    :param global_type:
    :param create_name:
    :param page_num:
    :param page_size:
    :return:
    '''
    try:
        sql_param=[Global.pro_code==pro_code,Global.isdelete==0]

        #追加sql条件
        if module_code.__len__()!=0: sql_param.append(Global.module_code==module_code)
        if global_name.__len__()!=0: sql_param.append(Global.global_name.like('%{}%'.format(global_name)))
        if global_param.__len__()!= 0: sql_param.append(Global.global_param==global_param)
        if global_type in (1,2): sql_param.append(Global.global_type==global_type)

        return qa_uitls.page_info(db.query(Global).filter(*sql_param).order_by(Global.id.desc()).all(), page_num, page_size)
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def get_globalinfo(id:int,db:Session=Depends(get_api_db)):
    '''
    读取全局变量
    :param id:
    :return:
    '''
    try:
        return {'code':200,'msg':db.query(Global).filter(Global.id==id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del")
async def del_globalinfo(gl:global_schemas.GlobalParamBase,db:Session=Depends(get_api_db)):
    '''
    删除全局变量
    :param gl:
    :return:
    '''
    try:
        global_info=db.query(Global).filter(Global.id==gl.id).first()
        if global_info==None: return {'code':201,'msg':'无效ID！'}
        global_info.isdelete=1
        db.commit()
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/save")
async def save_global(gl:global_schemas.GlobalParamSave,db:Session=Depends(get_api_db)):
    '''
    添加或编辑全局变量
    :param gl:
    :return:
    '''
    try:

        if db.query(Case).filter(Case.extract_param.like('%{}%'.format(gl.global_name)),Case.pro_code==gl.pro_code,Case.isdelete==0).count()>0:
            return {'code': 201, 'msg': '变量名称已存在类似名称，请重新输入!'}

        if db.query(Global).filter(Global.global_param.like('%{}%'.format(gl.global_name)),Global.pro_code==gl.pro_code,Global.isdelete==0).count()>0:
            return {'code': 201, 'msg': '变量名称已存在类似名称，请重新输入!'}

        if gl.id==0:
            db_item = Global(**gl.dict())
            db.add(db_item)
            db.commit()  # 添加

        else:

            global_info = db.query(Global).filter(Global.id == gl.id).first()
            if global_info == None: return {'code': 201, 'msg': '无效ID！'}
            global_info.global_name=gl.global_name
            global_info.global_param=gl.global_param
            global_info.param_value=gl.param_value
            global_info.module_code=gl.module_code
            global_info.global_type = gl.global_type
            global_info.code_info = gl.code_info #编辑
            db.commit()

        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



