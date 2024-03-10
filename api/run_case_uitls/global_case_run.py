from api.run_case_uitls.case_plugin import Case_Plugin
from qa_dal.models import GlobalCase,Global,Case,Api,ApiHost,ApiData
from sqlalchemy.orm import Session
import json

class GET_Value():
    '''
    获取全局变量代码参数
    '''
    def __init__(self):
        self.result=object

    def global_fun(self,code_info):
        try:
            code = compile(code_info, "", mode="exec")
            exec(code)
            return {'code':200,'msg':self.result}
        except Exception as ex:
            error_line = ex.__traceback__.tb_lineno
            error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
            return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


def Global_value(pro_code, db:Session):
    '''
    获取全局变量
    :return:
    '''
    global_res = {}
    global_list = db.query(Global).filter(Global.pro_code == pro_code, Global.isdelete == 0).order_by(Global.id.desc()).all()

    for gl in global_list:
        if gl.global_type == 1:  # 固定参数
            global_res[gl.global_param] = gl.param_value
        else:
            #代码参数
            gl_result = GET_Value().global_fun(gl.code_info)

            if gl_result['code'] == 200: global_res[gl.global_param] = gl_result['msg']

    return global_res


from uitls.log import LOG
def Global_case(pro_code,db: Session):
    '''
    全局用例
    :return:
    '''
    gl_value=Global_value(pro_code,db)  #全局变量
    gl_case_list=db.query(GlobalCase).filter(GlobalCase.pro_code==pro_code,GlobalCase.isdelete==0).all()    #所有全局用例
    # for i in gl_case_list:
    #     LOG().info(i)
    sql_param=[Case.api_id == Api.id,ApiData.data_group_num=='df',ApiData.case_id==Case.id]

    for gl_case in gl_case_list:
        # LOG().info(f'test{gl_case.join_case_id}')
        # LOG().info(f'test{gl_case.param_value}')

        #校验保存的sid
        assert_case = db.query(Case, Api, ApiData).filter(Case.id==gl_case.assert_case_id).filter(*sql_param).first()

        param_value=eval(gl_case.param_value)
        gl_value=dict(gl_value,**param_value)

        assert_host_json=db.query(ApiHost).filter(ApiHost.id==assert_case.Api.host_id).first()
        assert_host_json=assert_host_json.to_json()

        assert_case_info={
            'assert_list':json.loads(assert_case.ApiData.assert_list),
            'case_name':assert_case.Case.case_name,
            'extract_param':json.loads(assert_case.Case.extract_param),
            'header':json.loads(assert_case.Case.header),
            'header_param':json.loads(assert_case.Case.header_param),
            'host':assert_host_json[assert_case.ApiData.run_host],
            'host_json':assert_host_json,
            'join_param':json.loads(assert_case.Case.join_param),
            'method':assert_case.Api.method,
            'preconditions':assert_case.Case.preconditions,
            'pro_code':pro_code,
            'request_body':json.loads(assert_case.ApiData.request_body),
            'url':assert_case.Api.url,
            'url_param':assert_case.Case.url_param,
            'wait_time':assert_case.Case.wait_time
                          }
        assert_cp=dict(Case_Plugin(assert_case_info,gl_value))  #执行校验接口


        #断言失败则重新获取
        if assert_cp['assert_info']['isok']==False:
            join_case = db.query(Case, Api, ApiData).filter(Case.id==gl_case.join_case_id).filter(*sql_param).first()
            join_host_json = db.query(ApiHost).filter(ApiHost.id == join_case.Api.host_id).first()
            join_host_json = join_host_json.to_json()

            join_case_info = {
                'assert_list': json.loads(join_case.ApiData.assert_list),
                'case_name': join_case.Case.case_name,
                'extract_param': json.loads(join_case.Case.extract_param),
                'header': json.loads(join_case.Case.header),
                'header_param': json.loads(join_case.Case.header_param),
                'host': assert_host_json[join_case.ApiData.run_host],
                'host_json': join_host_json,
                'join_param': json.loads(join_case.Case.join_param),
                'method': join_case.Api.method,
                'preconditions': join_case.Case.preconditions,
                'pro_code': pro_code,
                'request_body': json.loads(join_case.ApiData.request_body),
                'url': join_case.Api.url,
                'url_param': join_case.Case.url_param,
                'wait_time': join_case.Case.wait_time
            }
            join_cp = dict(Case_Plugin(join_case_info, gl_value))  # 执行关联接口
            new_param_value= {}
            for extract in join_cp['extract_info']:
                new_param_value[extract['extract_param']]=extract['jsonresult']
            gl_case.param_value=json.dumps(new_param_value)
            db.commit()

            gl_value = dict(gl_value, **new_param_value)
            # LOG().ex_position('test')
    return gl_value



