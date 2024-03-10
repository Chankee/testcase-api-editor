#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口host
import json
from distutils.log import Log

from fastapi import APIRouter,File, UploadFile
from pydantic import BaseModel

from qa_dal.models import ApiData,Business,Case

from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from qa_dal.api import apidata_schemas
from fastapi import Depends
from fastapi import File, UploadFile
from uitls.log import LOG
from qa_dal import qa_uitls
import os
import math
import random
import xlrd


router = APIRouter(
    prefix="/api/data",
    tags=["接口环境"]
)

@router.post("/set_assert")
async def set_assert(dataitem:apidata_schemas.DataAsset,db:Session=Depends(get_api_db)):
    '''
    设置检查点
    :param dataitem:
    :param db:
    :return:
    '''
    try:
        if dataitem.type == 1:
            case_info=db.query(Case).filter(Case.id==dataitem.case_id).first()
            if case_info==None: return {'code':201,'msg':'无效ID！'}
            case_info.assert_param= json.dumps(dataitem.assert_param)
            db.commit()
        else:
            case_info = db.query(Case).filter(Case.id == dataitem.case_id).first()
            if case_info == None: return {'code': 201, 'msg': '无效ID！'}
            case_info.assert_param = json.dumps(dataitem.assert_param)
            db.commit()

            data_info=db.query(ApiData).filter(ApiData.id==dataitem.id).first()
            if data_info == None: return {'code': 201, 'msg': '无效ID！'}
            data_info.assert_list=json.dumps(dataitem.assert_list)
            db.commit()
        return  {'code':200,'msg':'操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/list")
async def data_list(business_id:int,data_name:str,data_group_num:str,page_num:int=1,page_size:int=10,db:Session=Depends(get_api_db)):
    '''
    查询数据列表
    :param business_id:
    :param data_name:
    :param data_group_num:
    :param page_num:
    :param page_size:
    :param db:
    :return:
    '''
    try:
        sql_param = [ApiData.isdelete == 0]
        business_detail = db.query(Business.business_detail).filter(Business.id == business_id).first().business_detail
        sql_param.append(ApiData.case_id.in_(eval(business_detail)))
        if data_name.__len__()>0: sql_param.append(ApiData.data_name.like('%{}%'.format(data_name)))
        if data_group_num=='df':
            sql_param.append(ApiData.data_group_num=='df')

        if data_group_num not in ('','df'):
            sql_param.append(ApiData.business_id == business_id)
            sql_param.append(ApiData.data_group_num==data_group_num)

        result_list=db.query(ApiData,Case.case_name,Case.assert_param).filter(ApiData.case_id==Case.id,*sql_param).order_by(ApiData.id.desc()).all()
        return qa_uitls.page_info(result_list, page_num, page_size)
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/upload")
async def recv_file(file: UploadFile = File(...)):
    '''
    上传文档
    :param file:
    :return:
    '''
    try:
        file_name =str(math.floor(1e6 * random.random()))
        base_path=os.path.abspath(os.path.dirname(__file__)).replace('\\','/').replace('/api','')
        file_data = await file.read()

        #获取文件后缀
        path=file.filename.split(".")[1]
        if path not in ('xlsx','csv','xls'): return {'code':201,'msg':'请上传xlsx、csv、xls格式文件!','aa':path}
        file_path='{}/upload/api/{}'.format(base_path,'{}.{}'.format(file_name,path))

        #读取文件
        with open(file_path,"wb+") as fp:
            fp.write(file_data)
        fp.close()

        #获取列表
        wb = xlrd.open_workbook(filename=file_path)  # 读取excel文件
        sheetname = wb.sheet_names()

        return {'code':200,'msg':'操作成功！','return_file_name':file_path,'sheet_list':sheetname,'excel_info':read_excel(wb,sheetname[0])}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


def read_excel(wb,name):
    tb = wb.sheet_by_name(name)  # 读取excel文件

    rowNum = tb.nrows
    colNum = tb.ncols

    load_txt = "<table style='width:100%;' border='0' cellspacing='0' cellpadding='0'>"
    if rowNum > 0:
        for i in range(rowNum):
            load_txt += "<tr>"
            for j in range(colNum):
                if j == 0:
                    load_txt += "<td style='border:solid 1px #eee;line-height:30px;height:30px;padding-left:10px'>{}</td>".format(tb.cell_value(i, j))
                else:
                    load_txt += "<td style='border:solid 1px #eee;line-height:30px;height:30px;padding-left:10px'>{}</td>".format(tb.cell_value(i, j))
            load_txt += "</tr>"
    load_txt += "</table>"
    return load_txt



class ReadItem(BaseModel):
    file_name:str
    sheet_name:str

@router.post('/get_work_sheet_content')
def get_work_sheet_content(item:ReadItem):
    try:
        wb = xlrd.open_workbook(filename=item.file_name)

        return {'code':200,'msg':read_excel(wb,item.sheet_name)}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



class DataItem(BaseModel):
    business_id:int
    file_path:str
    sheet_name:str
    data_name:str

@router.post('/sync_workbook_data')
def sync_workbook_data(dataitem:DataItem,db:Session=Depends(get_api_db)):
    try:

        business=db.query(Business).filter(Business.id==dataitem.business_id).first()
        case_list= eval(business.business_detail)
        if case_list == []: return {'code':202,'msg':'该业务流没有步骤！'}
        wb = xlrd.open_workbook(filename=dataitem.file_path)  # 读取excel文件
        tb = wb.sheet_by_name(dataitem.sheet_name)  # 读取excel文件

        #数据格式化
        rowNum = tb.nrows
        colNum = tb.ncols
        if rowNum==0: return {'code':201,'msg':'Excel表格没有数据!'}

        #普通用例导入
        if business.business_type == 1:
            for i in range(rowNum):
                data_num = 'data_' + str(math.floor(1e6 * random.random()))
                row_data = tb.row_values(i)
                if i>len(case_list): continue  #行数大于步骤数就跳过

                case_info = db.query(Case).filter(Case.id == case_list[i]).first()
                for item in range(1,len(row_data)):
                    if row_data[item]=='': continue
                    detail={}
                    detail['data_group_name'] = dataitem.data_name
                    detail['business_id']=dataitem.business_id
                    detail['case_id']=case_list[i]
                    detail['request_body']=row_data[item]
                    detail['data_group_num']=data_num
                    detail['data_name']=case_info.case_name
                    detail['assert_list']='[]'
                    detail['run_host']=row_data[0]
                    db_item=ApiData(**detail)
                    db.add(db_item)
            db.commit()

        else:
            for i in range(rowNum):
                data_num = 'data_' + str(math.floor(1e6 * random.random()))
                for j in range(colNum):
                    if j>len(case_list)-1: continue
                    if tb.cell_value(i, j + 1) == '': continue
                    case_info = db.query(Case).filter(Case.id == case_list[j]).first()
                    detail = {}
                    detail['data_group_name'] = dataitem.data_name
                    detail['business_id'] = dataitem.business_id
                    detail['case_id'] = case_list[j]
                    detail['request_body'] = tb.cell_value(i, j+1)
                    detail['data_group_num'] = data_num
                    detail['data_name'] = case_info.case_name
                    detail['assert_list'] = '[]'
                    detail['run_host'] = tb.cell_value(i, 0)
                    db_item = ApiData(**detail)
                    db.add(db_item)

            db.commit()

        return {'code': 200, 'msg': '同步成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post('/del')
def del_data(dataitem:apidata_schemas.DataBase,db:Session=Depends(get_api_db)):
    try:
        result=db.query(ApiData).filter(ApiData.id==dataitem.id).first()
        if result==None: return {'code':201,'msg':'无效ID！'}
        result.isdelete=1
        db.commit()
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get('/detail')
def get_detail(id:int,db:Session=Depends(get_api_db)):
    try:
        result=db.query(ApiData).filter(ApiData.id==id).first()
        if result==None: return {'code':201,'msg':'无效ID！'}
        return {'code':200,'msg':result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post('/save')
def save_detail(item:apidata_schemas.SaveData,db:Session=Depends(get_api_db)):
    try:
        result = db.query(ApiData).filter(ApiData.id == item.id).first()
        if result == None: return {'code': 201, 'msg': '无效ID！'}
        result.data_name = item.data_name
        result.request_body = json.dumps(item.request_body)
        result.run_host = item.run_host
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}
