#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口信息数据
from uitls.sqldal import SqlDal
from uitls.log import LOG

class Api_Dal():
    def __init__(self):
        self.sq=SqlDal()


    def get_api_menus(self,procode):
        '''
        获取接口菜单信息
        :return:返回查询信息
        '''
        pro_sql="select count(id) as api_sum,pro_code from api_info where isdelete=0 and pro_code='{}'".format(procode)
        module_sql = "select module_name,module_code from pro_module where pro_code='{}' and isdelete=0".format(procode)
        return self.sq.select_datas([pro_sql,module_sql])



    def search_api(self,pro_code,sqlparam):
        '''
        查询接口
        :param sqlparam:
        :return:
        '''
        sql="select * from api_info where pro_code='{}' and isdelete=0{}".format(pro_code,sqlparam)
        return self.sq.select_data(sql)



    def get_api_sum(self,procode,module_code):
        '''
        接口汇总数
        :param procode:
        :param module_code:
        :return:
        '''
        api_sum_sql = "select count(id) as api_sum from api_info where pro_code='{}' and isdelete=0 and module_code='{}' group by module_code".format(procode,module_code)
        api_tag_sql="select count(id) as api_sum,tag from api_info where pro_code='{}' and module_code='{}' and tag<>'' and isdelete=0 group by tag".format(procode,module_code)
        return self.sq.select_datas([api_sum_sql, api_tag_sql])



    def add_api(self,api_info):
        '''
        添加接口
        :param api_info:
        :return:
        '''
        sql = "insert into api_info(api_name,method,header,url,host,request_body,response_body,dbsource,pro_code,module_code,tag,remark,host_id,dev_name) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, api_info)


    def add_api_id(self,api_info):
        '''
        添加接口返回ID
        :param api_info:
        :return:
        '''
        sql = "insert into api_info(api_name,method,header,url,host,request_body,response_body,dbsource,pro_code,module_code,tag,remark,host_id,dev_name) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        return self.sq.insert_data_retunid(sql,api_info)


    def check_api(self,api_url,pro_code):
        '''
        检查接口是否存在
        :param api_url:
        :param pro_code:
        :return:
        '''
        sql="select id from api_info where isdelete=0 and url='{}' and pro_code='{}'".format(api_url,pro_code)
        return self.sq.select_data(sql)


    def update_api(self,api_info):
        '''
        修改接口
        :param api_info:
        :return:
        '''
        sql = "update api_info set api_name=%s,method=%s,header=%s,url=%s,host=%s,request_body=%s,response_body=%s,pro_code=%s,module_code=%s,tag=%s,remark=%s,update_time=%s where id=%s"
        self.sq.save_data(sql, api_info)


    def module_api(self,pro_code):
        '''模型多级接口'''
        sql="select api.id,api.api_name,api.module_code from api_info as api,pro_module as module where api.module_code=module.module_code and api.isdelete=0 and api.pro_code='{}' group by api.id".format(pro_code)
        return self.sq.select_data(sql)


    def get_api_info(self,id):
        '''
        获取接口数据
        :param id:
        :return:
        '''
        sql="select api.*,hs.test_host,hs.prd_host,hs.uat_host from api_info as api,api_host as hs where api.id={} and api.host_id=hs.id".format(id)
        return self.sq.select_data(sql)[0]


    def check_case(self,id):
        '''
        检查接口是否有用例
        :param id:
        :return:
        '''
        sql="select count(*) as count from case_info where isdelete=0 and api_id={}".format(id)
        return self.sq.select_data(sql)[0]


    def del_api(self,api_info):
        '''
        删除接口
        :param api_info:
        :return:
        '''
        sql="update api_info set isdelete=1 where id=%s"
        self.sq.save_data(sql, api_info)



    def get_api_detail(self,id):
        '''
        接口详情信息
        :param id:
        :return:
        '''
        sql="select * from api_info where id={}".format(id)
        return self.sq.select_data(sql)[0]

if __name__ == '__main__':
    result_info=Api_Dal().module_api('77')
    module_list=list(set([ri['module_code'] for ri in result_info]))
    print(result_info)


