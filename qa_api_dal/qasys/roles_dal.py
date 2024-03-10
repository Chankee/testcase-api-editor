#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：角色权限

from uitls.sqldal import SqlDal
from uitls.log import LOG

class Roles_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def get_roleslist(self,sql_param):
        '''
        获取权限列表
        :param sql_param:
        :return:
        '''
        sql="select * from roles_info where isdelete=0{}".format(sql_param)
        return self.sq.select_data(sql)


    def get_rolesinfo(self,id):
        '''
        读取单个权限信息
        :param id:
        :return:
        '''
        sql="select * from roles_info where id={}".format(id)
        return self.sq.select_data(sql)[0]


    def add_roles(self,roles_info):
        '''
        添加项目信息
        :return:返回查询信息
        '''
        sql="insert into roles_info(roles_name,pro_code_list,menus_json,check_key,remark) values(%s,%s,%s,%s,%s)"
        self.sq.save_data(sql,roles_info)



    def updata_roles(self,roles_info,isbase=1):
        '''
        修改权限信息
        :param roles_info:
        :return:
        '''
        if isbase==1:
            sql="update roles_info set roles_name=%s,remark=%s where id=%s"
        else:
            sql = "update roles_info set pro_code_list=%s,menus_json=%s,check_key=%s where id=%s"
        self.sq.save_data(sql, roles_info)


    def del_roles(self,id):
        '''
        删除权限
        :param id:
        :return:
        '''
        sql="update roles_info set isdelete=1 where id=%s"
        self.sq.save_data(sql, id)


    def get_menus_roles(self):
        '''
        获取项目、一级菜单、二级菜单
        :return:
        '''
        sql1="select * from menus_info where parent_id=0 and isdelete=0 and menus_state=0 order by sort_num"
        sql2="select * from menus_info where parent_id>0 and isdelete=0 and menus_state=0 order by sort_num"
        return self.sq.select_datas([sql1,sql2])


    def get_select_roles(self):
        '''
        获取下拉框角色
        :return:
        '''
        sql="select roles_name,id from roles_info where isdelete=0"
        return self.sq.select_data(sql)

import json
if __name__ == '__main__':
    res=Roles_Dal().get_rolesinfo(1)
    print(json.loads(res['check_key']))