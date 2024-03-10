#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：用户模块数据

from uitls.sqldal import SqlDal

class User_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def add_user(self,user_info):
        '''
        添加用户
        :param user_info:
        :return:
        '''
        sql="insert into user_info(user_name,tel,email,user_type,user_state,remark,roles_id,pro_code) " \
            "values(%s,%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, user_info)


    def update_user(self,user_info):
        '''
        编辑用户
        :param user_info:
        :return:
        '''
        sql="update user_info set user_name=%s,tel=%s,email=%s,user_type=%s,user_state=%s,remark=%s,roles_id=%s,pro_code=%s where id=%s"
        self.sq.save_data(sql, user_info)


    def get_userlist(self, sql_param):
        '''
        获取模块列表
        :param sql_param:
        :return:
        '''
        sql = "select * from user_info where isdelete=0{}".format(sql_param)
        return self.sq.select_data(sql)


    def get_user(self,user_name):
        '''
        获取用户信息
        :return:返回查询信息
        '''
        sql="select ui.*,ri.pro_code_list as pro_code from user_info as ui,roles_info as ri where ui.user_name='{}' and ui.roles_id=ri.id and ui.isdelete=0".format(user_name)
        return self.sq.select_data(sql)[0]


    def get_user_info(self,id):
        '''
        获取用户信息
        :return:返回查询信息
        '''
        return self.sq.select_data("select * from user_info where id={}".format(id))


    def get_user_role(self,user_name):
        '''
        获取用户权限和负责项目
        :param user_name:
        :return:
        '''
        sql="select u.*,r.menus_json,r.pro_code_list as pro_menus from user_info as u,roles_info as r where u.user_name='{}' and u.roles_id=r.id".format(user_name)
        return self.sq.select_data(sql)[0]


    def del_user(self,id):
        '''
        删除用户
        :param id:
        :return:
        '''
        sql="update user_info set isdelete=1 where id=%s"
        self.sq.save_data(sql, id)



    def get_def_user(self):
        '''
        获取默认用户
        :return:
        '''
        sql="select user_name from user_info where isdelete=0 and user_state=0 order by id desc"
        return self.sq.select_data(sql)

