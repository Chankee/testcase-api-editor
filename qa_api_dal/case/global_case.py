from uitls.sqldal import SqlDal

class Global_Case_Dal():
    def __init__(self):
        self.sq=SqlDal()

    def add_global_case(self,add_info):
        '''
        添加全局用例
        :param add_info:
        :return:
        '''
        sql="insert into global_case(global_case_name,join_case_id,assert_case_id,param_value,remark,pro_code) values(%s,%s,%s,%s,%s,%s)"
        self.sq.save_data(sql, add_info)


    def get_global_case_list(self,pro_code):
        '''
        根据项目代码查询全局用例
        :param pro_code:
        :return:
        '''
        sql="select * from global_case where isdelete=0 and pro_code='{}'".format(pro_code)
        return self.sq.select_data(sql)

    def get_global_case_detail(self,id):
        '''
        读取单个全局用例
        :param id:
        :return:
        '''
        sql="select * from global_case where id={}".format(id)
        return self.sq.select_data(sql)[0]


