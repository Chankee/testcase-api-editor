#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：业务数据
from uitls.sqldal import SqlDal

class ApiData_Dal():
    def __init__(self):
        self.sq=SqlDal()

    def add_data(self,data_info):
        '''
        新增执行数据
        :param data_info:
        :return: ok
        '''
        sql="insert into api_data(data_group_name,business_id,request_body,case_id,data_group_num,data_name,assert_list,run_host) " \
            "values(%s,%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql,data_info)


    def update_df_data(self,data_info):
        '''
        修改默认参数
        :param data_info:
        :return:
        '''
        sql="update api_data set request_body=%s,assert_list=%s,run_host=%s where case_id=%s and data_group_num='df'"
        self.sq.save_data(sql, data_info)

    def get_df_data(self,case_id):
        '''
        获取默认数据
        :param case_id:
        :return:
        '''
        sql="select * from api_data where case_id={} and data_group_num='df'".format(case_id)
        return self.sq.select_data(sql)[0]


    def get_run_data(self,business_id,data_name):
        '''
        执行数据
        :param business_id:
        :return:
        '''
        sql="select data_group_num from api_data where isdelete=0 and business_id={} and data_group_name='{}' group by data_group_name".format(business_id,data_name)
        print(sql)
        return self.sq.select_data(sql)


    def get_datanum_info(self,case_id,data_group_num):
        '''
        根据分组num查询数据
        :param data_group_num:
        :return:
        '''
        sql="select case.id,detail.detail_name,detail.case_id,detail.wait_time,adata.assert_list as assert_param," \
            "adata.request_body from api_data as adata,business_detail as detail where adata.detail_id=detail.id" \
            " and adata.detail_id={} and adata.data_group_num='{}'".format(detail_id,data_group_num)
        return self.sq.select_data(sql)[0]


    def get_dataname_list(self,business_id):
        '''
        根据业务ID获取数据名称
        :param business_id:
        :return:
        '''
        sql="select data_group_name,run_host from api_data where business_id={} and isdelete=0 group by data_group_name".format(business_id)
        return self.sq.select_data(sql)





