#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：数据库配置

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from uitls.read_config import ReadConfig as rc



def conf_data(data_name):
    '''配置数据库'''
    conf_name = rc().read_config('dbconfig', 'DBSELECT', 'dbname')
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(
                rc().read_config('dbconfig', conf_name, 'user'),
                rc().read_config('dbconfig', conf_name, 'passwd'),
                rc().read_config('dbconfig', conf_name, 'host'),
                rc().read_config('dbconfig', conf_name, 'port'),
                data_name,
                rc().read_config('dbconfig', conf_name, 'charset'))

    # echo=True表示引擎将用repr()函数记录所有语句及其参数列表到日志
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, encoding='utf8', echo=False
    )

    # SQLAlchemy中，CRUD是通过会话进行管理的，所以需要先创建会话，
    # 每一个SessionLocal实例就是一个数据库session
    # flush指发送到数据库语句到数据库，但数据库不一定执行写入磁盘
    # commit是指提交事务，将变更保存到数据库文件中
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建基本映射类
    Base = declarative_base()
    return {'base':Base,'session':SessionLocal()}


ApiBASE=conf_data('qa_api_test')['base']        #接口自动化
CaseBASE=conf_data('test_manage_test')['base']    #测试用例
JIRABASE=conf_data('jira')['base']  #jira统计表
QASSO = conf_data('qa_sso')['base']


# Dependency
def get_db(func):
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接
    :return:
    """
    def conf_db():
        SessionLocal=func
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    return conf_db


@get_db
def get_api_db():
    '''
    接口库库连接
    :return:
    '''
    return conf_data('qa_api_test')['session']

@get_db
def get_sso_db():
    '''
    接口库库连接
    :return:
    '''
    return conf_data('qa_sso')['session']

@get_db
def get_case_db():
    '''
    测试用例库连接
    :return:
    '''
    return conf_data('test_manage_test')['session']

@get_db
def get_jira_db():
    '''
    jira库连接
    '''
    return conf_data('jira')['session']



def jira_data(data_name):
    '''配置数据库'''
    SQLALCHEMY_DATABASE_URL2 = "mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(
                rc().read_config('dbconfig', 'JIRAONLINE', 'user'),
                rc().read_config('dbconfig', 'JIRAONLINE', 'passwd'),
                rc().read_config('dbconfig', 'JIRAONLINE', 'host'),
                rc().read_config('dbconfig', 'JIRAONLINE', 'port'),
                data_name,
                rc().read_config('dbconfig', 'JIRAONLINE', 'charset'))

    # echo=True表示引擎将用repr()函数记录所有语句及其参数列表到日志
    engine2 = create_engine(
        SQLALCHEMY_DATABASE_URL2, encoding='utf8', echo=False
    )

    # SQLAlchemy中，CRUD是通过会话进行管理的，所以需要先创建会话，
    # 每一个SessionLocal实例就是一个数据库session
    # flush指发送到数据库语句到数据库，但数据库不一定执行写入磁盘
    # commit是指提交事务，将变更保存到数据库文件中
    SessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)

    # 创建基本映射类
    Base2 = declarative_base()
    return {'base':Base2,'session':SessionLocal2()}


# Dependency
def get_db2(func):
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接
    :return:
    """
    def conf_db2():
        SessionLocal2=func
        db = SessionLocal2()
        try:
            yield db
        finally:
            db.close()
    return conf_db2

@get_db2
def get_online_db():
    '''
    线上连接
    '''
    return jira_data('qa_summary')['session']

ONLINEBASE=jira_data('qa_summary')['base']        #同步数仓

