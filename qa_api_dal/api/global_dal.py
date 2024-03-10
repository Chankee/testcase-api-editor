#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：全局变量数据
from uitls.sqldal import SqlDal
from uitls.log import LOG

class Global_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def search_global(self,procode,sqlparam):
        '''
        查询全局变量
        :return:返回查询信息
        '''
        sql="select * from global_value where isdelete=0 and pro_code='{}'{}".format(procode,sqlparam)
        return self.sq.select_data(sql)



    def add_global(self,global_info):
        '''
        添加全局变量
        :param global_info:
        :return:
        '''
        sql = "insert into global_value(global_name,global_param,param_value,module_code,pro_code,global_type,code_info,create_name) values(%s,%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, global_info)


    def check_global(self,global_param,pro_code):
        '''
        检查全局变量
        :param global_param:
        :param pro_code:
        :return:
        '''
        sql="select count(id) as count from global_value where isdelete=0 and global_param like '{}%' and pro_code='{}'".format(global_param,pro_code)
        return self.sq.select_data(sql)[0]['count']


    def update_global(self,global_info):
        '''
        修改全局变量
        :param global_info:
        :return:
        '''
        sql = "update global_value set global_name=%s,global_param=%s,param_value=%s,module_code=%s,global_type=%s,code_info=%s where id=%s"
        self.sq.save_data(sql, global_info)


    def del_global(self,global_info):
        '''
        删除全局变量
        :param global_info:
        :return:
        '''
        sql="update global_value set isdelete=1 where id=%s"
        self.sq.save_data(sql, global_info)



    def get_global_detail(self,id):
        '''
        全局变量明细
        :param id:
        :return:
        '''
        sql="select * from global_value where id={}".format(id)
        return self.sq.select_data(sql)[0]


    def get_run_global(self,pro_code):
        '''
        运行的全局变量
        :param pro_code:
        :return:
        '''
        sql="select * from global_value where isdelete=0 and pro_code='{}'".format(pro_code)
        return self.sq.select_data(sql)


