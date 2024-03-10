class GetVarValueReplace:

    def __init__(self,params,global_var):
        self.result = object
        self.params=params # 接收jsonpath的结果
        self.global_var=global_var

    def var_value_replace(self,code_info:object):
        # try:
        code = compile(code_info, "", mode="exec")
        exec(code)
        return self.result

        # except Exception as ex:
        #     error_line = ex.__traceback__.tb_lineno
        #     error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line+1, e=str(ex))
        #     return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}