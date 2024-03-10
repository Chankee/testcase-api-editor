#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口host
from uitls.sqldal import SqlDal

class ApiHost_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def search_apihost(self,pro_code):
        '''
        查询接口host
        :return:
        '''
        sql="select * from api_host where isdelete=0 and pro_code='{}' order by id desc".format(pro_code)
        return self.sq.select_data(sql)



    def get_apihost(self,id):
        '''
        接口配置信息
        :param id:
        :return:
        '''
        sql="select * from api_host where id={}".format(id)
        return self.sq.select_data(sql)[0]



    def add_apihost(self,host_info):
        '''
        添加接口host
        :param host_info:
        :return:
        '''
        sql = "insert into api_host(host_name,test_host,uat_host,prd_host,pro_code,remark) values(%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, host_info)


    def update_apihost(self,host_info):
        '''
        修改接口配置
        :param config_info:
        :return:
        '''
        sql = "update api_host set host_name=%s,test_host=%s,uat_host=%s,prd_host=%s,pro_code=%s,remark=%s where id=%s"
        self.sq.save_data(sql, host_info)


    def del_apihost(self,host_info):
        '''
        删除接口host
        :param id:
        :return:
        '''
        sql="update api_host set isdelete=1 where id=%s"
        self.sq.save_data(sql, host_info)


    def get_apihost_by_pro_code(self,pro_code):
        '''
        根据项目编码查询host
        :param pro_code:
        :return:
        '''
        sql="select id,host_name from api_host where isdelete=0 and pro_code='{}'".format(pro_code)
        return self.sq.select_data(sql)


