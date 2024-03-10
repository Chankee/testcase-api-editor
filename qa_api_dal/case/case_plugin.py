#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口用例执行逻辑

from uitls.log import LOG
from qa_api_dal.api.global_dal import Global_Dal
from jsonpath import jsonpath
from jsonpath_ng import parse
import json

class Case_Plugin():

    def __init__(self,run_info,global_param):
        self.run_info = run_info
        self.global_param=global_param  #全局变量
        self.error_tag = []  # 查看执行错误标签
        self.precond={}
        self.url_param={}
        self.request_body={}
        self.header={}

    def keys(self):
        self.precond=self.Preconditions()
        self.url_param=self.Url_param()
        self.request_body=self.Join_replace()
        self.header=self.Header_replace()
        return ('precond','url_param','request_body','header','error_tag','run_info','global_param')

    def Preconditions(self):
        '''
        前置条件判断
        :param param:
        :param public_param:
        :return:
        '''
        result_par = self.run_info['preconditions']
        try:
            if result_par.__len__() == 0:
                return {'result': True, 'msg': '没有前置条件'}

            # 拼接公共参数
            for pp in self.global_param.keys():
                result_par = result_par.replace(pp, str(self.global_param[pp]))

            #进行判断
            if eval(result_par):
                return {'result':True,'msg':'通过，前置条件替换前：{}，替换后：{},结果成立'.format(self.run_info['preconditions'],result_par)}
            else:
                return {'result':False,'msg':'不通过，前置条件替换前：{}，替换后：{},结果不成立'.format(self.run_info['preconditions'],result_par)}


        except Exception as ex:
            error_line = ex.__traceback__.tb_lineno
            error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
            self.error_tag.append('前置条件')
            return {'result':False,'msg':'前置条件判断报错,前置条件替换前：{}，替换后：{},报错信息：{}'.format(self.run_info['preconditions'],result_par,str(error_info))}


    def Url_param(self):
        '''
        url参数
        :return:
        '''
        result_par=self.run_info['url_param']
        if self.run_info['url_param'].__len__()>0:
            for pp in self.global_param.keys(): result_par = result_par.replace(pp, str(self.global_param[pp]))
        return {'result':result_par,'msg':'url参数替换，替换前：{}，替换后：{}'.format(self.run_info['url_param'],result_par)}



    def Header_replace(self):
        '''
        请求头替换
        :param param: jp['import_data']→全局变量参数名
        :return:
        '''
        error_msg=[]
        if type(self.run_info['header'])==str:
            data = json.loads(self.run_info['header'])
        else:
            data = self.run_info['header']

        if type(self.run_info['header_param'])==str:
            header_param = eval(self.run_info['header_param'])
        else:
            header_param = self.run_info['header_param']

        if header_param.__len__()==0: return {'result':data,'msg':'请求头无需替换','error_msg':error_msg}

        for hp in header_param:
            try:

                if hp['import_param'] in self.global_param.keys():    #判断取的值是否在全局变量
                    jsonpath_expr = parse(hp['jsonpath'])
                    jsonpath_expr.find(data)
                    jsonpath_expr.update(data,self.global_param[hp['import_param']])

                else:
                    error_msg.append('获取不到全局变量的值,替换名称：{},jsonpath：{},引用参数：{}'
                                     .format(hp['plugin_name'],hp['jsonpath'],hp['import_param']))

            except Exception as ex:
                error_line = ex.__traceback__.tb_lineno
                error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
                error_msg.append('请求头替换参数拨错,替换名称：{},jsonpath：{},引用参数：{},报错信息：{}'
                                 .format(hp['plugin_name'], hp['jsonpath'], hp['import_param'],str(error_info)))

        if error_msg!=[]: self.error_tag.append('请求头替换')
        return {'result':data,'msg':'请求头替换完毕！','error_msg':error_msg}




    def Join_replace(self):
        '''
        替换入参
        :param param: jp['import_data']→全局变量参数名
        :return:
        '''
        error_msg=[]
        if type(self.run_info['request_body'])==str:
            data = json.loads(self.run_info['request_body'])
        else:
            data = self.run_info['request_body']

        if type(self.run_info['join_param'])==str:
            join_param = eval(self.run_info['join_param'])
        else:
            join_param =self.run_info['join_param']
        if join_param.__len__()==0: return {'result':data,'msg':'无需替换入参','error_msg':error_msg}

        for jp in join_param:
            try:

                if jp['import_param'] in self.global_param.keys():    #判断取的值是否在全局变量
                    jsonpath_expr = parse(jp['jsonpath'])
                    jsonpath_expr.find(data)
                    jsonpath_expr.update(data,self.global_param[jp['import_param']])

                else:
                    error_msg.append('获取不到全局变量的值,替换名称：{},jsonpath：{},引用参数：{}'
                                     .format(jp['plugin_name'],jp['jsonpath'],jp['import_param']))

            except Exception as ex:
                error_line = ex.__traceback__.tb_lineno
                error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
                error_msg.append('替换入参拨错,替换名称：{},jsonpath：{},引用参数：{},报错信息：{}'
                                 .format(jp['plugin_name'], jp['jsonpath'], jp['import_param'],str(error_info)))

        if error_msg!=[]: self.error_tag.append('替换入参')
        return {'result':data,'msg':'替换完毕！','error_msg':error_msg}



    def Extract_param(self, response_body):
        '''
        提取参数
        :param extract_par:
        :param public_param:
        :param response_body:
        :return:
        '''
        if type(self.run_info['extract_param'])==str:
            extract_par = json.loads(self.run_info['extract_param'])
        else:
            extract_par = self.run_info['extract_param']

        for ep in extract_par:

            # 替换公共参数
            for pp in self.global_param: ep['jsonpath'] = ep['jsonpath'].replace(pp, str(self.global_param[pp]))

            try:
                # jsonpath提取参数
                jsonpath_result = jsonpath(json.loads(response_body), ep['jsonpath'])
                if jsonpath_result != False:
                    self.global_param[ep['extract_param']] = jsonpath_result[0]
                    # 保存提取结果
                    ep['jsonresult'] = jsonpath_result[0]
                else:
                    ep['jsonresult'] = '没找到匹配的参数'

            except TypeError:
                ep['jsonresult'] = '提取参数时报错，错误信息:传入结果不是json格式'
            except Exception as ex:
                error_line = ex.__traceback__.tb_lineno
                error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
                ep['jsonresult'] = '提取参数时报错，错误信息:{}'.format(error_info)

        return extract_par



    def Assert_response(self, response_body):
        '''
        断言
        :param assert_type:
        :param assert_info: [{'assert_name':'判断是否为真','type':'eq','jsonpath':'$..code','assert_value':'200','param':'200'}]
        :return:
        '''
        isok = True
        if type(self.run_info['assert_param'])==str:
            assert_info = json.loads(self.run_info['assert_param'])
        else:
            assert_info = self.run_info['assert_param']

        for ai in assert_info:

            # 替换公共参数
            for pp in self.global_param:
                ai['assert_value'] = ai['assert_value'].replace(pp, str(self.global_param[pp]))

            try:
                jsonpath_result = jsonpath(json.loads(response_body), ai['jsonpath'])
                if ai['param'] not in ('','0'): ai['assert_value'] = int(ai['assert_value']) + int(ai['param'])  # 判断是否有增量值

                # 相等断言
                if ai['type'] == 'eq':
                    if jsonpath_result == False:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = False
                    elif str(ai['assert_value']) == str(jsonpath_result[0]):
                        ai['assert_result'] = True
                        ai['jsonpath_result'] = str(jsonpath_result[0])
                    else:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = str(jsonpath_result[0])

                # 不等于断言
                if ai['type'] == 'noteq':
                    if jsonpath_result == False:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = False
                    elif str(ai['assert_value']) != str(jsonpath_result[0]):
                        ai['assert_result'] = True
                        ai['jsonpath_result'] = str(jsonpath_result[0])
                    else:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = str(jsonpath_result[0])

                # 包含断言
                if ai['type'] == 'contain':
                    if jsonpath_result != False: jsonpath_result = [str(jr) for jr in jsonpath_result]
                    if jsonpath_result == False:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = False
                    elif str(ai['assert_value']) in jsonpath_result:
                        ai['assert_result'] = True
                        ai['jsonpath_result'] = jsonpath_result
                    else:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = jsonpath_result

                # 不包含断言
                if ai['type'] == 'notcontain':
                    if jsonpath_result != False: jsonpath_result = [str(jr) for jr in jsonpath_result]
                    if jsonpath_result == False:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = False
                    elif str(ai['assert_value']) not in jsonpath_result:
                        ai['assert_result'] = True
                        ai['jsonpath_result'] = jsonpath_result
                    else:
                        ai['assert_result'] = False
                        ai['jsonpath_result'] = jsonpath_result

            except TypeError:
                ai['assert_result'] = False
                ai['jsonpath_result'] = '断言时报错，错误信息:传入结果不是json格式或变量值不是数字'
            except Exception as ex:
                ai['assert_result'] = False
                error_line = ex.__traceback__.tb_lineno
                self.error_tag.append("断言")
                error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
                ai['jsonpath_result'] = '断言时报错，错误信息：{}'.format(str(error_info))

            if ai['assert_result'] == False: isok = False

        return {'isok': isok, 'msg': assert_info}


    def __getitem__(self, item):
        '''内置方法, 当使用obj['name']的形式的时候, 将调用这个方法, 这里返回的结果就是值'''
        return getattr(self, item)


if __name__ == '__main__':
    pass
    # aa=['','999!=1','999=999']
    # for bb in aa:
    #     print(Preconditions(bb,{'@token':123,'@size':1}))

    # ex=[{'extract_name':'提取token','param_name':'@token','json_path':'$..token'},{'extract_name':'提取msg','param_name':'@msg','json_path':'$..msg'}]
    # print(Case_Plugin({'@token':123,'@size':1}).extract_param(ex,{'token':998,'msg':111}))


    # ai=[{'assert_name':'判断是否为真','type':'eq','jsonpath':'$..code','assert_value':'@token','param':'200'},
    #     {'assert_name':'判断是否为真2','type':'noteq','jsonpath':'$..123','assert_value':'@token','param':'200'}]
    # result={'code':200,'msg':'操作成功！'}
    # print(Case_Plugin({'@token':123,'@size':1}).assert_json(ai,result))

    #print(Case_Plugin({}).extract_param([{"extract_name":"提取has_more","extract_param":"@has_more","jsonpath":"999"},{"extract_name":"提取owner_id","extract_param":"@owner_id","jsonpath":"$..owner_id"}],123))

    case_info={"id":189,"api_name":"用户登录","api_id":190,"case_name":"测试环境登录","wait_time":0,"url_param":"country=CN&sid=&uid=0&lang=zh_CN&cv=AZIZI3.2.00_Android&lc=326608c214ecaf60","preconditions":"","url":"/user/account/phone_login","method":"POST","module_code":"user","test_host":"https://testservicevins.hnyapu.cn","uat_host":"","prd_host":"","api_select":["user",190],"request_body":{"phone":"","secret":"","code":"1234","dev_name":"HUAWEIJKM-LX1","request_id":"8612345678101"},"host_json":{"test_host":"https://testservicevins.hnyapu.cn","uat_host":"","prd_host":""},"run_host":"test_host","header":{},"header_param":[],"join_param":[{"id":1,"plugin_name":"替换phone","jsonpath":"$..phone","import_param":"@phone_code"},{"id":2,"plugin_name":"替换secret","jsonpath":"$..secret","import_param":"@secret"}],"extract_param":[{"id":1,"extract_name":"提取dm_error","extract_param":"dm_error","jsonpath":"$..dm_error"}],"assert_param":[],"host":"https://testservicevins.hnyapu.cn"}
    gl={'@phone_code': '7d4ac2f48b9a215826340fe7fd42f485dfe74c118ae42f23260e10e8d3b299b77d9ef624dea3da7f89741768c9847dc64f58407c5db3f0b8c61e24c5d19c16cf6ddc9d64625cccece9cdf928d835bf0987b36bbf235ad30dd2b6108837a1f17810c2ca5a61a0dd41214bd00b25bf0bcf23d5a9c0b8b3b3b78b74704ff6b243af8fd57198e1af71600f3d483fbc6db230cc772f1f23da0ae8b9f2581558bc66cbd75410373b744b8e5699fc7982e9bca151e18ea7c29b5c08ec366844581ef7c9fe6b8d68ec05825cced5af726d6d6c10da49b80f66ff51b2fd51e729fc125f24566a550919732b4811b90a632d08718b11f6a1c4a9c0b7add58ef797d544ecd3', '@secret': '26a88d99152b8436ad1227b68e65b409'}
    dd=Case_Plugin(case_info,gl)
    r=dict(dd)
    print(r)

