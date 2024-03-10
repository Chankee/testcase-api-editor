import requests
# import json
import base64
# aa='1,live'.split(',')
# print(aa)
# url = "https://sso.inkept.cn/api/v1/user/ticket/{}/check2".format('STXkewPzJGXOETrtHyhoUADmHWcyFFhBVBv')
# r = requests.get(url)
# print(r.json())
# print(r.cookies.get_dict())

# url='https://sso.inkept.cn/login?service=http://gz-qa.inkept.cn/'
# password=str(base64.b64encode(str("test@123").encode())).replace("b'",'').replace("'",'')
# login_data = {
#             "username": 'fengsihua',
#             "password": password,
#             "token":""
#         }
#
# login_url = "https://sso.inkept.cn/login?service=http://127.0.0.1:8000/api"
# resp = requests.post(login_url, data=json.dumps(login_data), allow_redirects=False, verify=False)
# cookies = resp.cookies.get_dict()
# print(cookies)
#STXhCrVouzmnyHpryIADWrGeFNmZHWnzZhK

import socket

# def get_host_ip():
#     """
#     查询本机ip地址
#     :return:
#     """
#     try:
#         s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
#         s.connect(('8.8.8.8',80))
#         ip=s.getsockname()[0]
#     finally:
#         s.close()
#
#     return ip
#
# print(get_host_ip())
# print("and tester like '%{}%'".format(123))
#
# a=[]
# a.remove(0)

# from urllib.parse import urlparse
# print(urlparse('https://www.jb51.net:80/faq.cgi?src=fie'))
#
# print(urlparse('123'))

# dd={'77':123}
# dd['77']=456
# print(dd)

# print(int(1/3*100))
#
# aa='a,b,c,'
# print(aa[:-1])

# import time
# print(int(time.time()))
#
# aa=[1,2,3]
# print(str(aa))
# import jsonpath


# import json
# aa=[{"code":2}]
# print(type(json.dumps(aa)))

# from qa_api_dal.case.case_dal import Case_Dal
# extract_list=Case_Dal().get_extract('77')    #所有提取参数
# print(extract_list)

# case_info={'code':200}
# print(case_info['cod2'])

# def dd():
#     import json
#     aa={'a':111}
#     print(type(json.dumps(aa)))
# dd()

# aa={}
# print(len(aa.keys()))

# import pandas as pd
# df=pd.DataFrame
# json_info1=[{'aa':111,'bb':222},{'aa':333,'bb':444}]
# json_info2=[{'aa':111,'dd':666},{'cc':777,'dd':888}]
# df_info=df(json_info1)
# df_info2=df(json_info2)
# aa=pd.merge(df_info,df_info2,on='aa')
# print(aa.to_json(orient='records'))


# aa=[1,2,3]
# bb=[3,4,5]
# print(aa+bb)


# class A(object):
#     name = 'wukt'
#     age = 18
#
#     def __init__(self):
#         self.gender = 'male'
#         self.ee=''
#
#     def aa(self):
#         return '777'
#
#     def keys(self):
#         '''当对实例化对象使用dict(obj)的时候, 会调用这个方法,这里定义了字典的键, 其对应的值将以obj['name']的形式取,
#         但是对象是不可以以这种方式取值的, 为了支持这种取值, 可以为类增加一个方法'''
#         self.ee=self.aa()
#         return ('name', 'age', 'gender','ee')
#
#     def __getitem__(self, item):
#         '''内置方法, 当使用obj['name']的形式的时候, 将调用这个方法, 这里返回的结果就是值'''
#         return getattr(self, item)
#
# a = A()
# r = dict(a)
# print(r)
# aa={'@aa':123}
# bb={'@aa':444}
# print(dict(aa,**bb))
aa={1:2}

