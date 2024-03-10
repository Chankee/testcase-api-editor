#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：业务流
from uitls.sqldal import SqlDal
from uitls.log import LOG

class Business_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def search_business(self,procode,sqlparam):
        '''
        查询业务流
        :param procode:
        :param sqlparam:
        :return:
        '''
        sql="select * from business_info where isdelete=0 and pro_code='{}'{}".format(procode,sqlparam)
        return self.sq.select_data(sql)



    def add_business(self,business_info):
        '''
        添加业务流
        :param business_info:
        :return:
        '''
        sql = "insert into business_info(business_name,b_state,business_detail,create_name,pro_code,module_code) values(%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, business_info)


    def update_detail(self,bi):
        '''
        修改业务明细
        :param business_info:
        :return:
        '''
        sql ="update business_info set business_detail=%s where id=%s"
        self.sq.save_data(sql, bi)


    def update_business(self,business_info):
        '''
        修改业务流
        :param business_info:
        :return:
        '''
        sql = "update business_info set business_name=%s,module_code=%s where id=%s"
        self.sq.save_data(sql, business_info)


    def del_business(self,business_info):
        '''
        删除业务流
        :param business_info:
        :return:
        '''
        sql="update business_info set isdelete=1 where id=%s"
        self.sq.save_data(sql, business_info)



    def get_business_info(self,id):
        '''
        业务流详情
        :param id:
        :return:
        '''
        sql="select * from business_info where id={}".format(id)
        return self.sq.select_data(sql)[0]


    def get_module_business(self,pro_code):
        '''
        模块业务流
        :param id:
        :return:
        '''
        sql="select * from business_info where pro_code={}".format(pro_code)
        return self.sq.select_data(sql)


    def get_tree_info(self,procode):
        '''
        项目树结构
        :param procode:
        :param module_code:
        :return:
        '''
        pro_sql = "select count(id) as business_sum,pro_code from business_info where isdelete=0 and pro_code='{}'".format(procode)
        module_sql = "select module_name,module_code from pro_module where pro_code='{}' and isdelete=0".format(procode)
        return self.sq.select_datas([pro_sql, module_sql])


    def get_module_sum(self,pro_code,module_code):
        '''
        模块汇总
        :param pro_code:
        :param module_code:
        :return:
        '''
        sql = "select count(id) as module_sum from business_info where pro_code='{}' and isdelete=0 and module_code='{}' group by module_code".format(pro_code, module_code)
        return self.sq.select_data(sql)

    def update_job(self,id_list,isadd=1):
        if isadd==1:
            sql="update business_info set b_state=1 where id=%s".format(id_list)
        else:
            sql = "update business_info set b_state=0 where id=%s".format(id_list)
        self.sq.save_data(sql, id_list)



if __name__ == '__main__':
    Business_Dal().update_job(1)
