#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2019/4/10 14:06
# @Author：kee
# @Description：钉钉测试报告机器人

import requests

import time
import hmac
import hashlib
import base64
import urllib.parse

from uitls.log import LOG
from uitls.read_config import ReadConfig

class Send_Report:
    def __init__(self):
        self.timestamp = str(round(time.time() * 1000))


    '''发送钉钉'''
    def send_dingding(self,text_info,dingding_token,at_list):

        #测试环境
        # if dingding_type=="TEST":
            # secret = self.rc.read_config('dbconfig.conf', 'TESTDINGDING', 'secret')
            # secret_enc = secret.encode('utf-8')
            # string_to_sign = '{}\n{}'.format(self.timestamp, secret)
            # string_to_sign_enc = string_to_sign.encode('utf-8')
            # hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            # sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(dingding_token)

        headers = {'Content-Type': 'application/json'}

        json = {"msgtype": "text",
                "text": {
                    "content": text_info,
                },
                "at":
                    {
                        "atMobiles":at_list,
                        "isAtAll": False,
                    }
                }

        result=requests.post(url=url,headers=headers,json=json)
        # LOG().info(result.json())

        # else:
        #
        #     # secret = self.rc.read_config('dbconfig.conf', 'ONLINEDINGDING', 'secret')
        #     # secret_enc = secret.encode('utf-8')
        #     # string_to_sign = '{}\n{}'.format(self.timestamp, secret)
        #     # string_to_sign_enc = string_to_sign.encode('utf-8')
        #     # hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        #     # sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        #     url = 'https://oapi.dingtalk.com/robot/send?' \
        #           'access_token={}' \
        #         .format(self.rc.read_config('dbconfig', 'ONLINEDINGDING', 'access_token'))
        #
        #     headers = {'Content-Type': 'application/json'}
        #
        #     json = {"msgtype": "text",
        #             "text": {
        #                 "content": text_info
        #             },
        #             "at":
        #                 {
        #                     "atMobiles":at_list,
        #                     "isAtAll": False,
        #                 }
        #             }
        #
        #     requests.post(url=url, headers=headers, json=json)


if __name__ == '__main__':
    pass
    #Send_Report().send_dingding("测试生产环境","ONLINE")

