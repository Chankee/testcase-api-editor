#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2019/7/22 10:17
# @Author：kee
# @Description：接口请求类


import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class HTTPRequest:
    # 每次完成一次请求

    def __init__(self,method='', url='', data=None, cookies=None, headers={"Content-Type":"application/json"}):

        method = method.upper()  # 强制转成大写
        if method == "POST":
            self.resp = requests.post(url=url, json=data,headers=headers,verify=False)
        elif method == "GET":
            self.resp = requests.get(url=url, json=data, cookies=cookies, headers=headers,verify=False)
        else:
            print('不支持该请求类型，请查看你的得请求方式是否正确！！！')

    def get_status_code(self):
        return self.resp.status_code

    def get_json(self):
        return self.resp.json()

    def get_text(self):
        return self.resp.text

    def get_cookies(self):
        return self.resp.cookies

    def get_time(self):
        return self.resp.elapsed.total_seconds()




if __name__ == '__main__':
    url="https://testservicebl2.9zhenge.com/api/v1/address/list?uid=100212"
    hp=HTTPRequest(method="GET",url=url,data='{}',headers='{"Content-Type":"application/json"}')
    print(hp.get_json())
