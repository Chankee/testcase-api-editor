#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：定时任务
from uitls.sqldal import SqlDal

class RunJob_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def search_job(self,pro_code,sqlparam):
        '''
        查询定时任务
        :param sqlparam:
        :return:
        '''
        sql="select * from run_job where isdelete=0 and pro_code='{}'{}".format(pro_code,sqlparam)
        return self.sq.select_data(sql)



    def get_job_detail(self,id):
        '''
        定时任务明细
        :param id:
        :return:
        '''
        sql="select * from run_job where id={}".format(id)
        return self.sq.select_data(sql)[0]



    def add_job(self,job_info):
        '''
        添加定时任务
        :param config_info:
        :return:
        '''
        sql = "insert into run_job(job_name,business_list,notice,run_time,run_state,run_type,pro_code) values(%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, job_info)


    def update_job(self,job_info):
        '''
        修改job
        :param config_info:
        :return:
        '''
        sql = "update run_job set job_name=%s,business_list=%s,notice=%s,run_time=%s,run_state=%s,run_type=%s where id=%s"
        self.sq.save_data(sql, job_info)


    def del_job(self,job_info):
        '''
        删除job
        :param id:
        :return:
        '''
        sql="update run_job set isdelete=1 where id=%s"
        self.sq.save_data(sql, job_info)

