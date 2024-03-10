#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：项目信息与模块

from uitls.sqldal import SqlDal
from uitls.log import LOG

class Pm_Dal():
    def __init__(self):
        self.sq=SqlDal()

    def get_pmname(self,pro_code):
        '''
        获取项目名称
        :param pro_code:
        :return:
        '''
        sql="select pro_name from project where pro_code='{}'".format(pro_code)
        return self.sq.select_data(sql)[0]['pro_name']

    def get_pmlist(self,sql_param):
        '''
        获取项目列表
        :param sql_param:
        :return:
        '''
        sql="select * from project where isdelete=0{}".format(sql_param)
        return self.sq.select_data(sql)


    def get_fullpm(self):
        '''查询所有的项目'''
        sql="select pro_code,pro_name from project where isdelete=0"
        return self.sq.select_data(sql)


    def get_pminfo(self,id):
        '''
        读取单个项目信息
        :param id:
        :return:
        '''
        sql="select * from project where id={}".format(id)
        return self.sq.select_data(sql)


    def add_pm(self,pm_info):
        '''
        添加项目信息
        :return:返回查询信息
        '''
        sql="insert into project(pro_name,pro_code,tester,pro_type,remark) values(%s,%s,%s,%s,%s)"
        self.sq.save_data(sql,pm_info)



    def updata_pm(self,pm_info):
        '''
        修改项目信息
        :param pm_info:
        :return:
        '''
        sql="update project set pro_name=%s,pro_code=%s,tester=%s,pro_type=%s,remark=%s where id=%s"
        self.sq.save_data(sql, pm_info)


    def del_pm(self,id):
        '''
        删除项目
        :param id:
        :return:
        '''
        sql="update project set isdelete=1 where id=%s"
        self.sq.save_data(sql, id)




class Module_Dal():
    def __init__(self):
        self.sq=SqlDal()

    def get_modulelist(self, sql_param):
        '''
        获取模块列表
        :param sql_param:
        :return:
        '''
        sql = "select * from pro_module where isdelete=0{}".format(sql_param)
        return self.sq.select_data(sql)


    def get_module(self, id):
        '''
        读取单个模块信息
        :param id:
        :return:
        '''
        sql = "select * from pro_module where id={}".format(id)
        return self.sq.select_data(sql)


    def add_module(self, module_info):
        '''
        添加模块信息
        :return:返回查询信息
        '''
        sql = "insert into pro_module(module_name,module_code,pro_code,remark,user_name_list) values(%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, module_info)


    def updata_module(self, module_info):
        '''
        修改模块信息
        :param module_info:
        :return:
        '''
        sql = "update pro_module set module_name=%s,module_code=%s,pro_code=%s,remark=%s,user_name_list=%s where id=%s"
        self.sq.save_data(sql, module_info)


    def del_module(self, id):
        '''
        删除项目
        :param id:
        :return:
        '''
        sql = "update pro_module set isdelete=1 where id=%s"
        self.sq.save_data(sql, id)


    def get_module_by_procode(self,pro_code):
        '''
        根据项目code获取模块
        :param pro_code:
        :return:
        '''
        sql ="select module_name,module_code from pro_module where pro_code='{}' and isdelete=0".format(pro_code)
        return self.sq.select_data(sql)


    def get_modulename_by_code(self,module_code,pro_code):
        '''
        根据modulecode查询
        :param module_code:
        :return:
        '''
        sql ="select module_name from pro_module where module_code='{}' and pro_code='{}'".format(module_code,pro_code)
        return self.sq.select_data(sql)[0]['module_name']

if __name__ == '__main__':
    #Pm_Dal().updata_pm(['111','222','333',1,'444',23])
    Module_Dal().get_modulename_by_code('live')



