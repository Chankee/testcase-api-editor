#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口配置数据
from uitls.sqldal import SqlDal

class ApiConf_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def search_apiconf(self,sqlparam):
        '''
        查询接口配置
        :param sqlparam:
        :return:
        '''
        sql="select * from api_config where isdelete=0{}".format(sqlparam)
        return self.sq.select_data(sql)



    def get_apiconf(self,id):
        '''
        接口配置信息
        :param id:
        :return:
        '''
        sql="select * from api_config where id={}".format(id)
        return self.sq.select_data(sql)[0]



    def add_apiconf(self,config_info):
        '''
        添加接口配置信息
        :param config_info:
        :return:
        '''
        sql = "insert into api_config(conf_name,conf_type,conf_info,module_code,host_id,pro_code,remark) values(%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, config_info)


    def update_apiconf(self,config_info):
        '''
        修改接口配置
        :param config_info:
        :return:
        '''
        sql = "update api_config set conf_name=%s,conf_type=%s,conf_info=%s,module_code=%s,host_id=%s,remark=%s where id=%s"
        self.sq.save_data(sql, config_info)


    def del_apiconf(self,config_info):
        '''
        删除接口配置
        :param id:
        :return:
        '''
        sql="update api_config set isdelete=1 where id=%s"
        self.sq.save_data(sql, config_info)


    def get_module_conf(self,pro_code):
        '''
        获取模块配置
        :param pro_code:
        :return:
        '''
        sql="select * from api_config where isdelete=0 and conf_type=3 and pro_code='{}'".format(pro_code)
        return self.sq.select_data(sql)
