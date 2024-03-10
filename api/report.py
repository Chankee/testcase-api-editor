#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口host

from fastapi import APIRouter
from qa_api_dal.report.report_dal import Report_Dal
from uitls.log import LOG

from qa_dal.models import Report,Business,ReportDetail
from sqlalchemy.orm import Session
from sqlalchemy import func
from qa_dal.database import get_api_db
from fastapi import Depends

router = APIRouter(
    prefix="/api",
    tags=["接口信息库[/api]"]
)


@router.get("/job_report")
async def get_job_report(summary_num:str='',db:Session=Depends(get_api_db)):

    #汇总
    result=db.query(func.sum(Report.total_count).label('total'),func.sum(Report.ok_count).label('ok_count'),
             func.sum(Report.fail_count).label('fail_count'),func.sum(Report.error_count).label('error_count'),
             func.sum(Report.skip_count).label('skip_count')).filter(Report.summary_num==summary_num).first()

    summary_total={'total':0,'ok_count':0,'fail_count':0,'error_count':0,'skip_count':0,'pass_percen':0}
    if result!=None:
        if result.total not in (None,0):
            summary_total['total']=result.total
            summary_total['ok_count'] = result.ok_count
            summary_total['fail_count'] = result.fail_count
            summary_total['error_count'] = result.error_count
            summary_total['skip_count'] = result.skip_count
            summary_total['pass_percen']=round(result.ok_count/result.total*100,2)

    #报告列表
    report_list=db.query(Report.ok_count,Report.fail_count,Report.error_count,Report.skip_count,Report.total_count,Report.business_id,Report.report_num,Report.summary_time,Business.business_name)\
        .join(Business,Business.id==Report.business_id).filter(Report.summary_num==summary_num).all()


    return {'code':200,'summary_total':summary_total,'report_list':report_list}


@router.get("/job_report_detail")
async def job_report_detail(report_num:str,db:Session=Depends(get_api_db)):
    '''
    报告详情
    :param report_num:
    :return:
    '''

    try:
        group_num=db.query(ReportDetail.data_group_num).filter(ReportDetail.report_num==report_num).group_by(ReportDetail.data_group_num).all()

        result=db.query(ReportDetail).filter(ReportDetail.report_num==report_num).all()
        return {'code':200,'msg':result,'gg':group_num}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/report_list")
async def get_report_list(business_id:int,business_type:int):
    '''
    前10条报告列表
    :param business_id:
    :param business_type:
    :return:
    '''

    try:
        return {'code':200,'msg':Report_Dal().get_report_list(business_id,business_type)}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/report_detail_info/{report_num}")
async def report_detail_info(report_num:str):
    '''
    业务步骤测试报告详情
    :param report_num:
    :return:
    '''

    try:
        report_list,detail_list=Report_Dal().get_detial_repot(report_num)
        report_list[0]['detail']=detail_list    #报告详情
        if report_list[0]['total_count']>0:
            report_list[0]['pass_percent']=round(report_list[0]['ok_count']/report_list[0]['total_count']*100,2)  #百分比
        return {'code':200,'msg':report_list[0]}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


