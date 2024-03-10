#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：数据库模型

from sqlalchemy import Boolean,Column,Integer,String,ForeignKey,DateTime,Float
from sqlalchemy.orm import relationship,declarative_base
from qa_dal.database import ApiBASE,CaseBASE,JIRABASE,ONLINEBASE,QASSO
import datetime
import time

'''--------------------------------------------系统设置-------------------------------------------------------'''
class Project(QASSO):
    '''项目表'''
    __tablename__ = "project"
    id = Column(Integer, primary_key=True, index=True)
    pro_name=Column(String(50))
    pro_code = Column(String(50))
    remark=Column(String(255),nullable=True)
    jira_id = Column(String(50), default='')
    isdelete=Column(Integer,default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class ProModule(ApiBASE):
    '''项目模块表'''
    __tablename__ = "pro_module"
    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String(50))
    module_code = Column(String(100))
    pro_code = Column(String(50))
    remark = Column(String(50),default='')
    isdelete = Column(Integer,default=0)

    confitem = relationship("ApiConfig", uselist=False, back_populates="module_item")

    api_item = relationship("Api",back_populates="module_item",primaryjoin="and_(ProModule.pro_code==Api.pro_code,ProModule.module_code==Api.module_code,Api.isdelete==0)")

    business_item = relationship("Business",back_populates="module_item",primaryjoin="and_(ProModule.pro_code==Business.pro_code,ProModule.module_code==Business.module_code,Business.isdelete==0)")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict



class User(QASSO):
    '''
    用户表
    '''
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(50))
    tel = Column(String(20), default='')
    email = Column(String(150), default='')
    pro_fun = Column(String(20), default='unknow')  # 安卓端:android  IOS端:ios  平台后台:manage  服务端:server H5端:h5 小程序端：applet
    remark = Column(String(255), default='')
    roles_id = Column(String, default='{"test":11,"summary":0}')
    pro_code_list = Column(String, default='[]')
    group_name = Column(String, default='')
    isdelete = Column(Integer, default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict



'''--------------------------------------------接口-------------------------------------------------------'''
class ApiHost(ApiBASE):
    '''接口环境'''
    __tablename__ = "api_host"
    id = Column(Integer, primary_key=True, index=True)
    host_name = Column(String(10))
    test_host = Column(String(255))
    uat_host = Column(String(255))
    prd_host = Column(String(255))
    pro_code = Column(String(50))
    remark = Column(String(255))
    isdelete = Column(Integer,default=0)

    confitem = relationship("ApiConfig", uselist=False, back_populates="host_item")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class ApiConfig(ApiBASE):
    '''接口配置'''
    __tablename__ = "api_config"
    id = Column(Integer, primary_key=True, index=True)
    conf_name = Column(String(50))
    conf_type = Column(Integer)
    conf_info = Column(String)
    module_code = Column(String,ForeignKey("pro_module.module_code"))
    host_id = Column(Integer,ForeignKey("api_host.id"))
    pro_code = Column(String)
    remark = Column(String,default=0)
    isdelete = Column(Integer,default=0)

    host_item = relationship("ApiHost", back_populates="confitem")
    module_item = relationship("ProModule", back_populates="confitem")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Api(ApiBASE):
    '''接口信息'''
    __tablename__ = "api_info"
    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String)
    method = Column(String)
    header = Column(String,default={})
    url = Column(String)
    host = Column(String)
    request_body = Column(String)
    response_body = Column(String,default='{}')
    dbsource = Column(Integer,default=1)
    update_time = Column(String,default='')
    pro_code = Column(String)
    module_code = Column(String,ForeignKey("pro_module.module_code"))
    tag = Column(String,default='')
    remark = Column(String,default='')
    host_id = Column(Integer)
    dev_name = Column(String,default='')
    isdelete = Column(Integer,default=0)

    case_item = relationship("Case", back_populates="api_item",primaryjoin="and_(Api.id==Case.api_id,Case.isdelete==0)")

    module_item = relationship("ProModule", back_populates="api_item")


    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Case(ApiBASE):
    '''用例'''
    __tablename__ = "case_info"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer,ForeignKey("api_info.id"))
    case_name = Column(String)
    url_param = Column(String,default='')
    header = Column(String,default='{}')
    extract_param = Column(String,default='[]')
    preconditions = Column(String,default='')
    header_param = Column(String,default='[]')
    join_param = Column(String,default='[]')
    business_list = Column(String,default='')
    create_name = Column(String)
    assert_param = Column(String,default='[]')
    wait_time = Column(Integer,default=0)
    pro_code =Column(String)
    isdelete = Column(Integer,default=0)

    api_item = relationship("Api", back_populates="case_item")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class ApiData(ApiBASE):
    '''接口数据'''
    __tablename__ = "api_data"
    id = Column(Integer, primary_key=True, index=True)
    data_group_name = Column(String,default='默认参数')
    business_id = Column(Integer,default=0)
    case_id = Column(Integer)
    request_body = Column(String)
    data_group_num = Column(String,default='df')
    data_name = Column(String)
    assert_list = Column(String)
    run_host = Column(String)
    isdelete = Column(Integer,default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Global(ApiBASE):
    '''全局变量'''
    __tablename__ = "global_value"
    id = Column(Integer, primary_key=True, index=True)
    global_name = Column(String)
    global_param = Column(String)
    param_value = Column(String)
    module_code = Column(String)
    pro_code = Column(String)
    global_type = Column(Integer)
    code_info = Column(String)
    create_name = Column(String)
    param_type = Column(String)
    isdelete = Column(Integer,default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Business(ApiBASE):
    '''业务流'''
    __tablename__ = "business_info"
    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String)
    business_type = Column(Integer)
    b_state = Column(Integer,default=0)
    business_detail = Column(String,default='[]')
    create_name = Column(String)
    pro_code = Column(String)
    module_code = Column(String,ForeignKey("pro_module.module_code"))
    isdelete = Column(Integer,default=0)

    module_item = relationship("ProModule", back_populates="business_item")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Report(ApiBASE):
    '''测试报告'''
    __tablename__ = "report_info"
    id = Column(Integer, primary_key=True, index=True)
    report_num = Column(String)
    total_count = Column(Integer,default=0)
    ok_count = Column(Integer,default=0)
    fail_count = Column(Integer,default=0)
    error_count = Column(Integer,default=0)
    skip_count = Column(Integer,default=0)
    business_id = Column(Integer,default=0)
    summary_num = Column(String,default='')
    summary_time = Column(String,default='')
    report_type = Column(Integer,default=0)
    run_total = Column(Integer,default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict



class ReportDetail(ApiBASE):
    '''测试明细'''
    __tablename__ = "report_detail"
    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(String)
    api_name = Column(String)
    case_id = Column(String)
    url = Column(String)
    method = Column(String)
    header = Column(String)
    preconditions = Column(String)
    request_body = Column(String)
    business_id = Column(Integer)
    result_info = Column(String)
    report_num = Column(String)
    response_body = Column(String)
    assert_param = Column(String)
    extract_param = Column(String)
    data_group_num = Column(String)
    data_id = Column(Integer)
    run_time = Column(String)
    run_host = Column(String)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

class Job(ApiBASE):
    '''定时任务'''
    __tablename__ = "run_job"
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String)
    business_list = Column(String)
    notice = Column(String)
    run_time = Column(String)
    run_state = Column(Integer)
    run_type = Column(Integer)
    pro_code = Column(String)
    isdelete = Column(Integer,default=0)
    select_business = Column(String)
    dingding_token = Column(String)


    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class GlobalCase(ApiBASE):
    '''全局用例'''
    __tablename__ = "global_case"
    id = Column(Integer, primary_key=True, index=True)
    global_case_name = Column(String)
    join_case_id = Column(Integer)
    assert_case_id= Column(Integer)
    param_value = Column(String)
    remark = Column(String)
    pro_code = Column(String)
    isdelete = Column(Integer,default=0)
    join_case_info = Column(String)
    assert_case_info = Column(String)
    # select_business = Column(String)



    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


'''--------------------------------------------测试用例工具-------------------------------------------------------'''
class Version(CaseBASE):
    '''
    版本需求表
    '''
    __tablename__ = "version"
    id = Column(Integer, primary_key=True, index=True)
    pro_code = Column(String(50))
    version_name=Column(String(50))
    dingding_conf=Column(String(500),nullable=True)
    remark=Column(String(255),nullable=True)
    isrelease=Column(Integer,default=0)
    isdelete=Column(Integer,default=0)

    case_item=relationship("TestCase", back_populates="version")
    demand_item = relationship("Demand", back_populates="version_item",
                               primaryjoin="and_(Version.id==Demand.version_id,Demand.isdelete==0)")

class Demand(CaseBASE):
    '''
    需求模块表
    '''
    __tablename__ = "demand"
    id = Column(Integer, primary_key=True, index=True)
    pro_code = Column(String(50))
    module_code = Column(String(50))
    demand_name = Column(String(50))
    tester = Column(String(50))
    issuspend = Column(Integer,default=0)   #0为正常  1为暂停
    plan_start = Column(String(50))
    plan_end = Column(String(50))
    reality_start = Column(String(50),default='')
    reality_end = Column(String(50),default='')
    version_id = Column(Integer,ForeignKey("version.id"))
    jira_num = Column(String(50))
    jira_state = Column(String(50),default='')
    remark = Column(String(500))
    isdelete = Column(Integer, default=0)

    version_item = relationship("Version", back_populates="demand_item")
    case_item = relationship("TestCase", back_populates="demand_item",
                             primaryjoin="and_(Demand.id==TestCase.demand_id,TestCase.isrecovery==0,TestCase.isdelete==0)")


class TestCase(CaseBASE):
    '''
    测试用例表
    '''
    __tablename__ = "testcase"
    id = Column(Integer, primary_key=True, index=True)
    pro_code = Column(String(50))
    case_name = Column(String(150))
    case_type = Column(Integer,default=1)
    version_id = Column(Integer,ForeignKey("version.id"),default=0)
    demand_id = Column(Integer,ForeignKey("demand.id"),default=0)
    tag = Column(String(150),default='')
    case_level = Column(String)
    front_info = Column(String)
    case_step = Column(String)
    case_result = Column(String)
    review_state = Column(Integer,default=0)
    create_name = Column(String)
    isrecovery = Column(Integer,default=0)
    recovery_people = Column(String, default='')
    isdelete = Column(Integer,default=0)
    sort_num = Column(Integer,default=0)
    tester_remark = Column(String,default='')
    sort_id = Column(Integer,default=0)
    index_id = Column(String,default='')

    version = relationship("Version", back_populates="case_item")
    demand_item = relationship("Demand", back_populates="case_item")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Delay(CaseBASE):
    '''发布性用例执行记录'''
    __tablename__ = "delay"
    id = Column(Integer, primary_key=True, index=True)
    pro_code=Column(String)
    version_name=Column(String)
    user_name=Column(String)
    delay_demand=Column(String)
    delay_time=Column(String)
    isdelete=Column(Integer,default=0)


class PlanVersion(CaseBASE):
    '''测试计划'''
    __tablename__ = "planversion"
    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String,default='')
    pro_code = Column(String)
    isdelete = Column(Integer,default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class TestPlan(CaseBASE):
    '''测试计划'''
    __tablename__ = "testplan"
    id = Column(Integer, primary_key=True, index=True)
    pro_code = Column(String)
    plan_version_id = Column(Integer)
    name = Column(String)
    type = Column(String)
    create_name = Column(String)
    join_plan_id = Column(String,default='[]')
    isdelete = Column(Integer,default=0)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class MySelfRecord(CaseBASE):
    '''执行自测记录'''
    __tablename__ = "myself_record"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer)
    plan_version_id = Column(Integer)
    plan_id = Column(Integer)
    name = Column(String)
    result = Column(String,default='未自测')
    result_remark = Column(String,default='')
    pro_code = Column(String)
    isdelete = Column(Integer,default=0)
    run_time = Column(DateTime,default='')
    check_name = Column(String,default='')
    check_result = Column(String,default='未验收')
    check_time = Column(DateTime)
    check_remark = Column(String,default='')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

class PlanCase(CaseBASE):
    '''计划里的用例'''
    __tablename__ = "plancase"
    id = Column(Integer, primary_key=True, index=True)
    plan_version_id=Column(String)
    case_id = Column(Integer)
    plan_id = Column(Integer)
    plan_type = Column(String)
    pro_code = Column(String)
    result = Column(String,default='未执行')
    tester = Column(String,default='')
    run_time = Column(DateTime)
    isdelete = Column(Integer,default=0)
    result_remark = Column(String,default='')
    bug = Column(String)


class JenkinsRecord(ApiBASE):
    __tablename__="jenkins_record"
    id =Column(Integer,primary_key=True)
    job_id=Column(Integer)
    build_id=Column(Integer)
    run_time=Column(String,default='')
    run_result=Column(String,default='')
    report_id=Column(Integer)


class DingDing(CaseBASE):
    '''钉钉配置'''
    __tablename__ = "dingding"
    id = Column(Integer, primary_key=True, index=True)
    pro_code=Column(String,default='')
    token=Column(String,default='')
    type=Column(Integer,default=1)
    daytoken=Column(String,default='')
    jira_panel_url=Column(String,default='')


class DingDingRecord(CaseBASE):
    '''钉钉记录表'''
    __tablename__ = "dingding_record"
    id = Column(Integer, primary_key=True, index=True)
    pro_code=Column(String)
    content=Column(String)
    send_name=Column(String)
    version_name=Column(String)
    type=Column(Integer)



class CaseIndex(CaseBASE):
    '''用例目录'''
    __tablename__ = "caseindex"
    id = Column(Integer, primary_key=True, index=True)
    id_path=Column(String,default='')
    parent_id_path=Column(String,default='')
    sort=Column(Integer,default=0)
    type=Column(Integer,default=0)
    pro_code=Column(String,default='')
    name=Column(String,default='')
    level=Column(Integer,default=0)
    isdelete = Column(Integer, default=0)
    remark = Column(String,default='')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


'''--------------------------------------------jira表-------------------------------------------------------'''
def jira_model(_BOOKNAME):
    Model = declarative_base()
    class jira_tabel(Model):
        __tablename__ = _BOOKNAME
        id = Column(Integer, primary_key=True, index=True)
        issuetype = Column(String)     #类型
        status = Column(String)        #状态
        summary = Column(String)       #标题
        description = Column(String)   #描述
        created = Column(String)       #创建时间
        resolved = Column(String)      #解决时间
        reporter = Column(String)      #报告人
        assignee = Column(String)      #经办人
        priority = Column(String)      #优先级
        component = Column(String)     #模块（端）
        affectedVersion = Column(String)   #影响版本
        reopen = Column(Integer)        #重开
        isonline = Column(Integer)      #线上问题
        case_id = Column(Integer)       #用例ID
        demand_id = Column(Integer)     #需求ID
        belong = Column(String)         #Bug归属
        plan_id = Column(Integer)       #计划ID
    return jira_tabel


class QaProOnline(ONLINEBASE):
    __tablename__="qa_pro_online"
    id = Column(Integer, primary_key=True, index=True)
    pro_name = Column(String,default='')
    online_count = Column(Integer,default=0)
    online_res_percen = Column(Float,default=0)
    online_solve_percen = Column(Float,default=0)
    summary_date=Column(DateTime)
    same_day_total = Column(Integer,default=0)
    same_day_solve_percen = Column(Float,default=0)
    same_day_res_percen = Column(Float,default=0)


class MailConf(CaseBASE):
    __tablename__ = "mail_conf"
    id = Column(Integer, primary_key=True, index=True)
    to_mail = Column(String,default='')
    cc_mail = Column(String,default='')
    jira_id = Column(String, default='')
    pro_code = Column(String, default='')
    mail_type = Column(Integer, default=1)


class MailRecord(CaseBASE):
    __tablename__ = "mail_record"
    id = Column(Integer, primary_key=True, index=True)
    to_mail =Column(String,default='')
    cc_mail=Column(String,default='')
    jira_id=Column(String,default='')
    title = Column(String, default='')
    content = Column(String, default='')
    sendname = Column(String, default='')
    mail_type = Column(Integer, default=1)


from sqlalchemy.orm import Session as db
if __name__ == '__main__':
    db=db.query(Case).filter(Case.id==170).all()

    #db=Session.query(Case,Api,ApiHost,ApiData).filter(Case.id==170,Case.api_id==Api.id,ApiHost.id==Api.host_id,ApiData.data_group_num=='df',ApiData.case_id==Case.id).all()
    print(db)





