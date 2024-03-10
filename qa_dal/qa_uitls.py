#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：数据层通用方法


def page_info(apis,page_num,page_size):
    '''
    分页逻辑
    :param apis:
    :param page_num:
    :param page_size:
    :return:
    '''
    total = len(apis)
    try:
        page_num = int(page_num) - 1
        page_size = int(page_size)
    except:
        return {"code":201,"data":[]}
    if page_num < 0 or page_size < 0:
        return {"code":201,"data":[]}
    start = 0
    if page_size:
        start = page_num * page_size
        apis = apis[start:start + page_size]

    return {'code':200,'msg':apis,'total':total}





