#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2019/4/10 14:06
# @Author：kee 
# @Description：读取配置信息
import configparser
import os

class ReadConfig:
    def __init__(self):
        self.base_file_url=os.path.abspath(os.path.dirname(__file__)).replace('\\','/').replace('/uitls','')     #获取当前路径
        self.cf=configparser.ConfigParser()         #初始化conf


    def get_file_path(self,file_name):
        '''
        获取文件路径
        :param file_name:文件名称
        :return:返回文件路径
        '''
        return '{}/conf/{}.conf'.format(self.base_file_url,file_name)



    def read_config(self,file_name,section_name,key,encoding='utf-8'):
        '''
        读取配置文件
        :param file_name:文件名
        :param section_name:标签名
        :param key:标签值
        :return:返回conf内容
        '''
        self.cf.read(self.get_file_path(file_name),encoding=encoding)
        return self.cf.get(section_name,key)



    def write_config(self,file_name,section_name,key_list):
        '''
        读取配置文件
        :param file_name:文件名
        :param section_name:标签名
        :param key:标签值
        :return:返回conf内容
        '''
        file_path = self.get_file_path(file_name)  # 获取文件路径

        self.cf.add_section(section_name)
        for item in key_list:
            self.cf.set(section_name,item['key'],item['value'])

        #如果存在就写入，不存在就创建
        if os.path.exists(file_path):
            with open(file_path, 'a',encoding='utf-8') as file:
                self.cf.write(file)
        else:
            with open(file_path, 'w',encoding='utf-8') as file:
                self.cf.write(file)



if __name__ == '__main__':
    print(ReadConfig().get_file_path('db'))


    #ct=ReadConfig().write_config('dd','2020',[{'key':'123','value':'456'},{'key':'789','value':'101112'}])
