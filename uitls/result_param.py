#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：返回结果集

'''
200~299段 表示操作成功：

200 操作成功，正常返回

201 操作成功，已经正在处理该请求

300~399段 表示参数方面的异常

300 参数类型错误

301 参数格式错误

302 参数超出正常取值范围

303 token过期

304 token无效

400~499段 表示请求地址方面的异常：

400 找不到地址

500~599段 表示内部代码异常：

500 服务器代码异常'''


from fastapi import HTTPException

def code200():
    '''
    默认200
    :return:返回操作成功
    '''
    return {"code":200,"msg":"操作成功！"}


def data(code,data):
    '''
    data格式
    :param code:状态码
    :param msg:返回信息
    :return:返回值
    '''
    return {"code":code,"data":data}


def raise_msg(status_code,detail):
    '''
    返回异常
    :param status_code:状态码
    :param detail:返回信息
    :return:返回异常
    '''
    raise HTTPException(status_code=status_code, detail=detail)


