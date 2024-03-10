#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口配置

from fastapi import APIRouter
from qa_api_dal.api.api_conf_dal import ApiConf_Dal
from qa_api_dal.qasys.pm_dal import Module_Dal
from qa_dal import qa_uitls
from qa_dal.models import ApiConfig
from qa_dal.api import apiconfig_schemas
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from sqlalchemy import or_
from fastapi import Depends
from uitls.log import LOG
import requests
from lxml import etree
import json

router = APIRouter(
    prefix="/apiconf",
    tags=["系统设置"]
)


@router.get("/list",response_model=apiconfig_schemas.ApiConfListShow)
async def get_conflist(pro_code:str='',conf_type:int=0,key_value:str='',page_num:int=1,page_size:int=10,db:Session=Depends(get_api_db)):
    '''
    查询配置信息
    :param pro_code:
    :param conf_type:
    :param key_value:
    :param page_num:
    :param page_size:
    :return:
    '''
    try:
        sql_param = [ApiConfig.pro_code == pro_code, ApiConfig.isdelete == 0]

        # 追加sql条件
        if conf_type in (1, 2, 3): sql_param.append(ApiConfig.conf_type == conf_type)
        if key_value.__len__() > 0: sql_param.append(
            or_(ApiConfig.conf_name.like('%{}%'.format(key_value)), ApiConfig.conf_info.like('%{}%'.format(key_value))))

        return qa_uitls.page_info(db.query(ApiConfig).filter(*sql_param).order_by(ApiConfig.id.desc()).all(), page_num, page_size)
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def get_confinfo(id:int,db:Session=Depends(get_api_db)):
    '''
    读取配置信息
    :param id:
    :param db:
    :return:
    '''
    try:
        return {'code':200,'msg':db.query(ApiConfig).filter(ApiConfig.id==id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del")
async def del_confinfo(cf:apiconfig_schemas.ApiConfigBase,db:Session=Depends(get_api_db)):
    '''
    删除配置信息
    :param cf:
    :return:
    '''
    try:
        apiconf=db.query(ApiConfig).filter(ApiConfig.id==cf.id).first()
        if apiconf==None: return {'code':201,'msg':'无效ID！'}
        apiconf.isdelete=1
        db.commit()
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/save")
async def save_conf(cf:apiconfig_schemas.ApiConfigSave,db:Session=Depends(get_api_db)):
    '''
    添加或编辑配置
    :return:
    '''
    try:
        if cf.id==0:
            db_item = ApiConfig(**cf.dict())
            db.add(db_item)
            db.commit()  # 添加
        else:
            apiconf = db.query(ApiConfig).filter(ApiConfig.id == cf.id).first()
            if apiconf == None: return {'code': 201, 'msg': '无效ID！'}
            apiconf.conf_name=cf.conf_name
            apiconf.conf_type=cf.conf_type
            apiconf.conf_info=cf.conf_info
            apiconf.module_code=cf.module_code
            apiconf.host_id=cf.host_id
            apiconf.remark=cf.remark
            db.commit()   #编辑
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/module_conf/{pro_code}")
async def module_conf(pro_code:str):
    try:
        return_list = []
        result_info = ApiConf_Dal().get_module_conf(pro_code)
        module_list = list(set([ri['module_code'] for ri in result_info]))
        for ml in module_list:
            ml_item = {}
            ml_item['label'] = Module_Dal().get_modulename_by_code(ml)
            ml_item['value'] = ml
            ml_item['children'] = [{'label': ri['conf_name'], 'value': [ri['id'],ri['conf_info']]} for ri in result_info if
                                   ri['module_code'] == ml]
            return_list.append(ml_item)
        return {'code': 200, 'msg': return_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/conf_api")
async def conf_api(url:str):
    '''
    获取文件api
    :param url:
    :return:
    '''
    try:
        r = requests.get(url)
        html = r.content
        html_doc = str(html, 'utf-8')  # html_doc=html.decode("utf-8","ignore")

        html_info = etree.HTML(html_doc)
        h2_list = html_info.xpath("//code[contains(string(),'GET') or contains(string(),'POST')]")

        api_list = []
        for hl in h2_list:
            param_json = {}
            if hl.text.startswith(('GET ', 'POST ')) == False: continue  # 过滤不是POST或GET的信息

            # 获取table的参数
            tbody = hl.xpath('parent::pre/following-sibling::table/tbody')[0]  # 获取tody内容
            tbody_tr = tbody.xpath('tr')
            for tr in tbody_tr:
                if tr.xpath('td/text()') == []: continue  # 过滤td为空的
                param_json[tr.xpath('td/text()')[0]] = '{}({})'.format(tr.xpath('td/text()')[-1], tr.xpath('td/text()')[-2])

            api_list.append({
                'api_name': hl.xpath('parent::pre/preceding-sibling::h2/text()')[-1],  # 获取url同级上一个H2标签文本
                'host': '',
                'url': hl.text.partition(' ')[-1],
                'method': hl.text.partition(' ')[0],
                'request_body': json.dumps(param_json)
            })
        return {'code':200,'msg':api_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}

