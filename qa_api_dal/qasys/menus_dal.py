#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：菜单

from uitls.sqldal import SqlDal
from uitls.log import LOG

class Menus_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def get_menuslist(self):
        '''
        获取菜单列表
        :param sql_param:
        :return:
        '''
        sql="select * from menus_info where isdelete=0 order by sort_num"
        return self.sq.select_data(sql)


    def get_menusinfo(self,id):
        '''
        读取单个菜单信息
        :param id:
        :return:
        '''
        sql="select * from menus_info where id={}".format(id)
        return self.sq.select_data(sql)[0]


    def add_menus(self,menus_info):
        '''
        添加项目信息
        :return:返回查询信息
        '''
        sql="insert into menus_info(menus_name,level,parent_id,url,remark,sort_num,tag,ico) values(%s,%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql,menus_info)



    def updata_menus(self,menus_info):
        '''
        修改菜单信息
        :param pm_info:
        :return:
        '''
        sql="update menus_info set menus_name=%s,level=%s,parent_id=%s,url=%s,remark=%s,sort_num=%s,tag=%s,ico=%s where id=%s"
        self.sq.save_data(sql, menus_info)


    def del_menus(self,id):
        '''
        删除菜单
        :param id:
        :return:
        '''
        sql="update menus_info set isdelete=1 where id=%s"
        self.sq.save_data(sql, id)
