#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：测试报告
from uitls.sqldal import SqlDal

class Report_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def add_report(self,report_info):
        '''
        添加测试报告
        :param report_info:
        :return:
        '''
        sql="insert into report_info(report_num,business_id,summary_num,summary_time,report_type) values(%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, report_info)



    def summary_report(self,sqlparam):
        '''
        汇总测试报告
        :param sqlparam:
        :return:
        '''
        sql="select summary_num,summary_time from report_info where business_id={} group by summary_num order by summary_time desc".format(sqlparam)
        return self.sq.select_data(sql)



    def summary_sum(self,summary_num):
        '''
        汇总统计数
        :param summary_num:
        :return:
        '''
        sql="select sum(total_count) as total,sum(ok_count) as ok,sum(fail_count) as fail,sum(error_count) as error from report_info where summary_num='{}'".format(summary_num)
        return self.sq.select_data(sql)



    def get_report_list(self,business_id,report_type):
        '''
        获取报告列表
        :param business_id:
        :return:
        '''
        sql="select report_num,DATE_FORMAT(runtime,'%m-%d %H:%i:%s') as runtime,summary_num,DATE_FORMAT(summary_time,'%m-%d %H:%i:%s') as summary_time from report_info where business_id={} and report_type={} order by id desc LIMIT 10".format(business_id,report_type)
        return self.sq.select_data(sql)



    def update_report_sum(self,report_info):
        '''
        更新测试报告汇总
        :param report_info:
        :return:
        '''
        sql = "update report_info set total_count=%s,fail_count=%s,error_count=%s,skip_count=%s,ok_count=%s where report_num=%s"
        self.sq.save_data(sql, report_info)


    def get_detial_repot(self,report_num):
        '''
        业务详情报告内容
        :param report_num:
        :return:
        '''
        report_sql="select * from report_info where report_num='{}'".format(report_num)
        repor_detail_sql="select * from report_detail where report_num='{}' order by id".format(report_num)
        return self.sq.select_datas([report_sql,repor_detail_sql])

class Report_Detai_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def get_detail_info(self,id):
        '''
        报告明细
        :param id:
        :return:
        '''
        sql="select * from report_detail where id={}".format(id)
        return self.sq.select_data(sql)


    def get_detail_list(self,report_num):
        '''
        明细列表
        :param report_num:
        :return:
        '''
        sql="select * from report_detail where report_num='{}'".format(report_num)
        return self.sq.select_data(sql)


    def add_report_detail(self,detail_info):
        '''
        添加明细
        :param detail_info:
        :return:
        '''
        sql="insert into report_detail(case_name,api_name,case_id,url,method,header,preconditions,request_body,business_id,result_info,report_num,response_body,assert_param,extract_param,data_group_num,data_id,run_time) " \
            "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, detail_info)


