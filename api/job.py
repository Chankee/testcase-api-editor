#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：定时任务
from typing import Union, List

from fastapi import APIRouter
from qa_dal import qa_uitls
import json

from qa_dal.models import Job, ProModule, ApiData
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from qa_dal.api import job_schemas,jenkinsrecord_schemas
from fastapi import Depends
from .runjenkins import update_jenkins_job, get_run_result, save_result, del_jenkins_job
from uitls.log import LOG

router = APIRouter(
    prefix="/api/job",
    tags=["系统设置"]
)


@router.get("/job_business")
async def get_job_business(pro_code:str='',db:Session=Depends(get_api_db)):
    '''
    多联
    :param pro_code:
    :param db:
    :return:
    '''
    result=db.query(ProModule).filter(ProModule.pro_code==pro_code,ProModule.isdelete==0).order_by(ProModule.id.desc()).all()

    return_list=[]
    for rl in result:
        if len(rl.business_item) == 0: continue
        detail={}
        detail['label']=rl.module_name
        detail['value']=rl.id
        detail['children']=[{'label':bs.business_name,'value':bs.id,'children':get_data(bs.id,db)} for bs in rl.business_item]
        return_list.append(detail)
    return {'code':200,'msg':return_list}

def get_data(business_id,db:Session):
    data_list=db.query(ApiData.data_group_name).filter(ApiData.business_id == business_id, ApiData.isdelete == 0).group_by(
        ApiData.data_group_name).all()
    data_info=[{'label':'默认参数','value':'默认参数'}]
    for data in data_list:
        detail={}
        detail['label']=data.data_group_name
        detail['value'] = data.data_group_name
        data_info.append(detail)
    return data_info


@router.get("/list")
async def get_job(pro_code:str='',job_name:str='',run_type:int=-1,run_state:int=-1,page_num:int=1,page_size:int=10,db:Session=Depends(get_api_db)):
    '''
    查询job
    :param pro_code:
    :param job_name:
    :param run_type:
    :param run_state:
    :param page_num:
    :param page_size:
    :return:
    '''

    try:
        sql_param = [Job.pro_code == pro_code, Job.isdelete == 0]

        # 追加sql条件
        if job_name.__len__() != 0: sql_param.append(Job.job_name.like('%{}%'.format(job_name)))
        if run_type in (1, 2): sql_param.append(Job.run_type == run_type)
        if run_state in (0, 1): sql_param.append(Job.run_state == run_state)

        job_list=qa_uitls.page_info(db.query(Job).filter(*sql_param).order_by(Job.id.desc()).all(), page_num, page_size)
        # job_list=json.loads(job_list)
        # LOG().info(job_list)
        # return qa_uitls.page_info(db.query(Job).filter(*sql_param).order_by(Job.id.desc()).all(), page_num, page_size)
        return job_list
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def job_detail(id:int,db:Session=Depends(get_api_db)):
    '''
    读取job信息
    :param id:
    :return:
    '''
    try:
        job_info=db.query(Job).filter(Job.id == id).first()
        job_info=job_info.to_json()
        job_info['notice']= job_info['notice'].split(',')
        return {'code':200,'msg':job_info}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del")
async def def_job(item:job_schemas.JobBase,db:Session=Depends(get_api_db)):
    '''
    删除定时任务
    :param cf:
    :return:
    '''
    try:
        job=db.query(Job).filter(Job.id==item.id).first()
        if job==None: return {'code':201,'msg':'无效ID！'}
        job.isdelete =1
        db.commit()
        result=del_jenkins_job(job.job_name)
        LOG().info(result)
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


def format_business(select_business):
    '''
    格式化业务
    :return:
    '''
    business_id_list=[sb[1] for sb in select_business]
    new_list=list(set(business_id_list))

    return_list=[]
    for b_id in new_list:
        detail = {'business_id': b_id, 'data_name': []}
        for b_list in select_business:
            if b_id==b_list[1]:
                detail['data_name'].append(b_list[2])
        return_list.append(detail)
    return return_list


@router.post("/savejob")
async def save_job(item:job_schemas.JobSave,db:Session=Depends(get_api_db)):
    '''
    添加或编辑job
    :return:
    '''
    try:
        if item.id==0:
            # item.business_list = json.dumps(item.business_list)
            # item.select_business = json.dumps(item.select_business)
            # tmp_item = Job(**item.dict())
            #
            # del tmp_item.id
            # db_item = tmp_item
            # is_jname_repeat=db.query(Job.job_name).filter(Job.job_name==item.job_name,Job.isdelete==0).first()
            # if is_jname_repeat: return {'code':201,'msg':'job_name重复'}
            # db.add(db_item)
            # db.commit()  # 添加
            # job_id=db.query(Job.id).filter(Job.job_name==item.job_name,Job.isdelete==0).first()[0]
            # result=update_jenkins_job(job_id˚=job_id,job_name=item.job_name,business_list=item.business_list,run_type=item.run_type,run_state=item.run_state,run_time=item.run_time)
            # LOG().info(result)

            item.business_list = json.dumps(item.business_list)
            job_item = {'pro_code': item.pro_code,
                        'job_name': item.job_name,
                        'business_list': json.dumps(format_business(item.select_business)),
                        'select_business': json.dumps(item.select_business),
                        'notice': ",".join(item.notice),
                        'run_time': item.run_time,
                        'run_type': item.run_type,
                        'run_state': item.run_state,
                        'dingding_token': item.dingding_token,
                        }
            db_item = Job(**job_item)
            is_jname_repeat=db.query(Job.job_name).filter(Job.job_name==item.job_name,Job.isdelete==0).first()
            if is_jname_repeat: return {'code':201,'msg':'job_name重复'}
            db.add(db_item)
            db.commit()  # 添加
            db.refresh(db_item)

            result = update_jenkins_job(job_name=item.job_name, job_id=db_item.id, run_type=item.run_type,
                                        run_state=item.run_state, run_time=item.run_time)
            LOG().info(result)


        else:
            job = db.query(Job).filter(Job.id == item.id).first()
            if job == None: return {'code': 201, 'msg': '无效ID！'}
            job.job_name=item.job_name
            job.business_list=json.dumps(format_business(item.select_business))
            job.select_business = json.dumps(item.select_business)
            job.notice = ",".join(item.notice)
            job.run_time = item.run_time
            job.run_state = item.run_state
            job.run_type = item.run_type
            job.dingding_token = item.dingding_token
            db.commit()
            pro_code=item.pro_code
            job_id=item.id
            business_list=json.dumps(item.business_list)


            # 新建/更新一个job
            result=update_jenkins_job(job_name=job.job_name,run_type=job.run_type,
                                      run_state=job.run_state,run_time=item.run_time,pro_code=pro_code,
                                      job_id=job_id,business_list=business_list,data_name="非默认")
            # LOG().info(result)
        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





