#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2019/5/15 10:17
# @Author：kee
# @Description：日志操作类

from loguru import logger
import os

class LOG:
    def __init__(self,logname='qasys'):
        self.logfile=os.path.abspath(os.path.dirname(__file__)).replace('\\','/').replace('/uitls','')     #获取当前路径

        #初始化日志配置
        self.log_conf = {'qasys': 'qasys.log', 'api': 'api.log', 'qasys': 'qasys.log', 'qasys': 'qasys.log', 'jira': 'jira.log'}
        self.logger=logger
        if logname not in self.log_conf.keys():
            logname='qasys'
        self.logger.add('{}/log/{}'.format(self.logfile,self.log_conf[logname]),rotation='500 MB')


    def info(self,msg):
        '''
        info信息
        :param msg:日志信息
        :return:
        '''
        self.logger.info(msg)


    def error(self,msg):
        '''
        错误信息
        :param msg:日志信息
        :return:
        '''
        self.logger.error(msg)


    def debug(self,msg):
        '''
        调试信息
        :param msg:日志信息
        :return:
        '''
        self.logger.debug(msg)

    def ex_position(self,msg):
        """
        打印异常的位置
        """
        self.logger.exception(msg)


if __name__ == '__main__':
    LOG().info('999')
    LOG().error('888')
    LOG().debug('777')

