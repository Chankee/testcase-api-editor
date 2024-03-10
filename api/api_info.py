#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口信息库

from fastapi import APIRouter
from typing import List,Union
from qa_dal import qa_uitls
from qa_dal.models import Api,ProModule,Case,ApiHost
from qa_dal.api import api_schemas
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from sqlalchemy import func
from fastapi import Depends
import time
import json

router = APIRouter(
    prefix="/api",
    tags=["接口信息库[/api]"]
)

@router.get('/tree')
async def tree_api_list(pro_code:str,db:Session=Depends(get_api_db)):
    '''
    接口树形菜单
    :param pro_code:
    :param db:
    :return:
    '''

    try:
        # 获取项目模块和接口总数
        api_total=db.query(Api.id).filter(Api.pro_code==pro_code,Api.isdelete==0).count()
        module_info=db.query(ProModule.module_code,ProModule.module_name).filter(ProModule.pro_code==pro_code,ProModule.isdelete==0).all()
        menus_list = [{'id': '0,{}'.format(pro_code), 'label': '全部接口','total': api_total, 'children': []}]

        #拼接接口菜单
        for mi in module_info:
            module_code=mi.module_code
            api_sum=db.query(func.count(Api.id).label('count')).filter(Api.pro_code==pro_code,Api.module_code==module_code,Api.isdelete==0).group_by(Api.module_code).first()
            tag_sum=db.query(func.count(Api.id).label('api_sum'),Api.tag).\
                filter(Api.pro_code==pro_code,Api.tag!='',Api.module_code==module_code,Api.isdelete==0).group_by(Api.tag).all()
            if api_sum!=None:
                menus_list[0]['children'].append({'id':'1,{}'.format(module_code),'label':mi.module_name,'total':api_sum.count,'children':[{'id':'2,{},{}'.format(ts.tag,module_code),'label':ts.tag,'total':ts.api_sum} for ts in tag_sum]})

        return {'code':200,'msg':menus_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get('/list',response_model=api_schemas.ApiListShow)
async def search_api(pro_code:str='',param:str='{}',api_name:str='',url:str='',dbsource:int=0,page_num:int=1,page_size:int=10,db:Session=Depends(get_api_db)):
    '''
    搜索接口
    :param pro_code:
    :param param:
    :param api_name:
    :param url:
    :param dbsource:
    :param page_num:
    :param page_size:
    :return:
    '''
    try:
        sql_param=[Api.pro_code==pro_code,Api.isdelete==0] #基础搜索条件

        param_list = param.split(',')

        #追加搜索条件
        if param_list[0] == '1': sql_param.append(Api.module_code==param_list[1])
        if param_list[0] == '2':
            sql_param.append(Api.tag == param_list[1])
            sql_param.append(Api.module_code == param_list[2])
        if url.__len__()!=0: sql_param.append(Api.url.like('%{}%'.format(url)))
        if api_name.__len__()!=0: sql_param.append(Api.api_name.like('%{}%'.format(api_name)))
        if dbsource in (1, 2, 3, 4): sql_param.append(Api.dbsource==dbsource)

        result=db.query(Api).filter(*sql_param).order_by(Api.id.desc()).all()
        return qa_uitls.page_info(result, page_num, page_size)
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post('/save_api')
async def save_api(item:api_schemas.ApiSave,db:Session=Depends(get_api_db)):
    '''
    保存接口
    :param api:
    :return:
    '''
    try:
        if item.id==0:
            db_item = Api(**item.dict())
            db.add(db_item)
            db.commit()
            return {'code': 200, 'msg': '操作成功！'} #添加
        else:
            api = db.query(Api).filter(Api.id == item.id).first()
            if api == None: return {'code': 201, 'msg': '无效ID！'}
            api.api_name=item.api_name
            api.method=item.method
            api.header=json.dumps(item.header)
            api.url=item.url
            api.host=item.host
            api.request_body=json.dumps(item.request_body)
            api.module_code=item.module_code
            api.tag=item.tag
            api.remark=item.remark
            api.update_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            db.commit()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get('/module_api',response_model=Union[List[api_schemas.ModuleItem],api_schemas.ApiModule])
async def module_api_list(pro_code:str,db:Session=Depends(get_api_db)):
    '''
    模块多级选项
    :param pro_code:
    :return:
    '''
    try:
        result=db.query(ProModule).filter(ProModule.pro_code==pro_code,ProModule.isdelete==0).all() #获取一对多数据结构

        #清洗数据
        result_list=[]
        for rl in result:
            result_item={'label':rl.module_name,'value':rl.module_code}
            if rl.api_item!=[]: result_item['children']=[{'label':api.api_name,'value':api.id} for api in rl.api_item if api.isdelete==0]
            result_list.append(result_item)

        return {'code':200,'msg':result_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get('/api_detail')
async def get_api_info(id:int,db:Session=Depends(get_api_db)):
    '''
    获取接口信息
    :param id:
    :return:
    '''
    try:
        api_info=db.query(Api).filter(Api.id==id).first()
        if api_info==None: return {'code':201,'msg':'无效ID！'}
        host_info=db.query(ApiHost).filter(ApiHost.id==api_info.host_id).first()
        return {'code':200,'msg':db.query(Api).filter(Api.id==id).first(),'host':host_info}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post('/del')
async def delete_api(item:api_schemas.ApiBase,db:Session=Depends(get_api_db)):
    try:
        if db.query(Case).filter(Case.api_id==item.id,Case.isdelete==0).count()>0: return {'code': 202, 'msg':'当前接口存在用例，不能删除！'}
        api=db.query(Api).filter(Api.id==item.id).first()
        if api==None: return {'code': 201, 'msg':'无效ID！'}

        api.isdelete=1
        db.commit()
        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}

