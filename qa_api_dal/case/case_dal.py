#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口用例数据
from uitls.sqldal import SqlDal

class Case_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def get_extract(self,pro_code,extract_param):
        '''
        获取提取参数
        :return:
        '''
        sql="select count(id) as count from case_info where isdelete=0 and extract_param like '%{}%' and pro_code='{}'".format(extract_param,pro_code)
        return self.sq.select_data(sql)[0]['count']



    def get_case_data(self,id):
        '''
        获取用例数据
        :param id:
        :return:
        '''
        sql="select ca.*,ad.request_body from case_info as ca,api_data as ad where ca.id=ad.case_id and ad.data_group_num='df' and ca.id={}".format(id)
        return self.sq.select_data(sql)[0]


    def get_case_info(self,id):
        '''
        获取用例信息
        :param id:
        :return:
        '''
        sql='select ca.*,api.module_code,api.id as apiid,api.url,api.host_id,api.method from case_info as ca,api_info api where api.id=ca.api_id and ca.id={}'.format(id)
        return self.sq.select_data(sql)[0]


    def get_detail_case(self,id):
        '''
        明细信息
        :param id:
        :return:
        '''
        sql='select * from case_info where id={}'.format(id)
        return self.sq.select_data(sql)[0]

    def search_case(self,sqlparam):
        '''
        查询用例
        :param sqlparam:
        :return:
        '''
        sql="select ca.id as id,api.url,api.api_name,api.method,ca.case_name,ca.create_name from api_info as api,case_info as ca where ca.isdelete=0 and api.id=ca.api_id{}".format(sqlparam)
        return self.sq.select_data(sql)



    def get_runcase_info(self,id_list):
        '''
        获取运行用例信息
        :param id_list:
        :return:
        '''
        sql="select api.api_name,api.url,api.method,ca.id,ca.case_name,ca.url_param,ca.header,ca.header_param,ca.join_param,ca.wait_time,hs.test_host,hs.uat_host,hs.prd_host,ca.extract_param,ca.preconditions,ca.assert_param from api_info as api,case_info as ca,api_host as hs where hs.id=api.host_id and api.id=ca.api_id and ca.id in {}".format(id_list)
        return self.sq.select_data(sql)


    def runcase_info(self,id):
        '''
        获取单个用例信息
        :param id_list:
        :return:
        '''
        sql="select api.api_name,api.id as api_id,api.url,api.method,api.module_code,ca.id,ca.case_name,ca.url_param,ca.header,ca.header_param,ca.join_param,ca.wait_time,hs.test_host,hs.uat_host,hs.prd_host,ca.extract_param,ca.preconditions,ca.assert_param from api_info as api,case_info as ca,api_host as hs where hs.id=api.host_id and api.id=ca.api_id and ca.id={}".format(id)
        return self.sq.select_data(sql)[0]



    def add_case(self,case_info):
        '''
        添加用例
        :param case_info:
        :return:
        '''
        sql = "insert into case_info(api_id,case_name,url_param,header,extract_param,preconditions,assert_param,create_name,header_param,join_param,pro_code,wait_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        return self.sq.insert_data_retunid(sql, case_info)


    def update_case(self,case_info):
        '''
        修改用例
        :param api_info:
        :return:
        '''
        sql = "update case_info set case_name=%s,url_param=%s,header=%s,extract_param=%s,preconditions=%s,assert_param=%s,header_param=%s,join_param=%s,wait_time=%s where id=%s"
        self.sq.save_data(sql, case_info)


    def update_detail_case(self,case_info):
        '''
        修改步骤用例
        :param api_info:
        :return:
        '''
        sql = "update case_info set case_name=%s,url_param=%s,header=%s,request_body=%s,extract_param=%s,preconditions=%s,assert_param=%s where id=%s"
        self.sq.save_data(sql, case_info)



    def base_info(self,pro_code):
        '''
        基础数据
        :param pro_code:
        :return:
        '''
        module_sql="select module_name,module_code from pro_module where isdelete=0 and pro_code='{}'".format(pro_code)
        dev_name_sql="select user_name from user_info where isdelete=0 and user_state=0"
        tag_sql="select tag from api_info where isdelete=0 and pro_code='{}' group by tag".format(pro_code)
        host_sql="select id,host_name from api_host where isdelete=0 and pro_code='{}'".format(pro_code)
        return self.sq.select_datas([module_sql,dev_name_sql,tag_sql,host_sql])


    def delete_case(self,id):
        '''
        删除case
        :param id:
        :return:
        '''
        sql="update case_info set isdelete=1 where id=%s"
        self.sq.save_data(sql, id)


    def api_case_list(self,api_id):
        '''
        接口用例
        :param id:
        :return:
        '''
        sql="select case_name,id from case_info where api_id={}".format(api_id)
        return self.sq.select_data(sql)


