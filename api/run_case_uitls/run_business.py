import math
import random

from api.run_case_uitls.run_single_api import RunSingleApi
from uitls.http_request import HTTPRequest
from qa_api_dal.case.case_dal import Case_Dal
from api.run_case_uitls.case_plugin import Case_Plugin
from qa_api_dal.report.report_dal import Report_Dal,Report_Detai_Dal
from qa_api_dal.api.business_dal import Business_Dal
from qa_api_dal.api.api_data_dal import ApiData_Dal
from api.run_case_uitls.global_case_run import Global_case
from sqlalchemy.orm import Session
from qa_dal.models import Report,ReportDetail,Case,Api,ApiData,ApiHost,Business
from time import sleep
import datetime
import json
from uitls.log import LOG
import time


class Run_Business():
    def __init__(self,pro_code):
        self.report_num="{}_{}".format(pro_code,str(math.floor(1e6 * random.random())))
        self.pro_code=pro_code


    def run_detail(self,pro_code,business_id,detail_list,db:Session):
        '''
        执行明细
        :return:
        '''
        #结果统计
        total_count =detail_list.__len__()
        fail_count = 0
        error_count = 0
        skip_count=0
        # time.sleep(2)

        #初始化
        report_info={'report_num':self.report_num,'business_id':business_id,'report_type':0}
        report_item=Report(**report_info)
        db.add(report_item)
        db.commit() #创建测试报告

        global_value=Global_case(self.pro_code,db)       #获取全局变量

        for dl in detail_list:
            # 第一步获取步骤用例信息
            # 查询执行用例
            caseinfo = db.query(Case, Api, ApiData).filter(Case.id==dl, Case.api_id == Api.id,
                                                                ApiData.data_group_num == 'df',
                                                                ApiData.case_id == Case.id).first()

            case_host_json = db.query(ApiHost).filter(ApiHost.id == caseinfo.Api.host_id).first()
            case_host_json = case_host_json.to_json()

            detail_info = {
                'case_id':caseinfo.Case.id,
                'api_name': caseinfo.Api.api_name,
                'assert_list': json.loads(caseinfo.ApiData.assert_list),
                'case_name': caseinfo.Case.case_name,
                'extract_param': json.loads(caseinfo.Case.extract_param),
                'header': json.loads(caseinfo.Case.header),
                'header_param': json.loads(caseinfo.Case.header_param),
                'host': case_host_json[caseinfo.ApiData.run_host],
                'host_json': case_host_json,
                'join_param': json.loads(caseinfo.Case.join_param),
                'method': caseinfo.Api.method,
                'preconditions': caseinfo.Case.preconditions,
                'pro_code': pro_code,
                'request_body': json.loads(caseinfo.ApiData.request_body),
                'url': caseinfo.Api.url,
                'url_param': caseinfo.Case.url_param,
                'wait_time': caseinfo.Case.wait_time
            }

            cp = dict(Case_Plugin(detail_info, global_value))

            detail_info['error_tag'] = cp['error_tag']
            detail_info['api_url'] = cp['url']
            detail_info['header'] = cp['header']['result']
            detail_info['request_body'] = cp['request_body']
            detail_info['response_body'] = cp['response_body']
            detail_info['reponse_tab'] = 'reponse_tab{}'.format(caseinfo.Case.id)
            detail_info['run_time']=cp['run_time']

            # 前置条件判断
            if cp['precond']['result']!=True:
                detail_info['result']='skip'
                detail_info['preconditions']=cp['preconditions']['msg']
                skip_count+=1

                #报告详情
                pre_report_detail_item={
                    'case_name':detail_info['case_name'],
                    'api_name':detail_info['api_name'],
                    'case_id':detail_info['case_id'],
                    'url':cp['url'],
                    'method':detail_info['method'],
                    'header':json.dumps(cp['header']['result']),
                    'preconditions':detail_info['preconditions'],
                    'request_body':cp['request_body']['result'],
                    'business_id':business_id,
                    'result_info':detail_info['result'],
                    'report_num':self.report_num,
                    'response_body':[json.dumps(cp['response_body']),cp['response_body']][type(cp['response_body'])==str],
                    'assert_param':json.dumps(detail_info['assert_list']),
                    'extract_param':json.dumps(detail_info['extract_param']),
                    'data_group_num':'df',
                    'data_id':0,
                    'run_time':detail_info['run_time'],
                    'run_host': detail_info['host']
                }
                pre_db_item=ReportDetail(**pre_report_detail_item)
                db.add(pre_db_item)
                db.commit()
                continue

            if cp['assert_info']['isok'] == False:
                fail_count += 1
                detail_info['result'] = 'fail'
            else:
                detail_info['result'] = 'ok'

            if '请求接口' in cp['error_tag']:
                detail_info['result'] = 'error'
                error_count += 1

            global_value = cp['global_param']

            report_detail_item = {
                'case_name': detail_info['case_name'],
                'api_name': detail_info['api_name'],
                'case_id': detail_info['case_id'],
                'url': cp['url'],
                'method': detail_info['method'],
                'header': json.dumps(cp['header']['result']),
                'preconditions': cp['precond']['msg'],
                'request_body': json.dumps(cp['request_body']['result']),
                'business_id': business_id,
                'result_info': detail_info['result'],
                'report_num': self.report_num,
                'response_body': [json.dumps(cp['response_body']),cp['response_body']][type(cp['response_body'])==str],
                'assert_param': json.dumps(detail_info['assert_list']),
                'extract_param': json.dumps(detail_info['extract_param']),
                'data_group_num': 'df',
                'data_id': 0,
                'run_time': detail_info['run_time'],
                'run_host':detail_info['host']
            }
            detail_db_item = ReportDetail(**report_detail_item)
            db.add(detail_db_item)
            db.commit()


        ok_count = total_count - fail_count - error_count-skip_count

        report=db.query(Report).filter(Report.report_num==self.report_num).first()
        report.total_count=total_count
        report.fail_count=fail_count
        report.error_count=error_count
        report.skip_count=skip_count
        report.ok_count=ok_count
        db.commit()

        return {'code': 200, 'msg': '执行完毕！'}



    def run_business(self,pro_code,business_id, data_name,db:Session,summary_report_num=''):
        '''
        执行业务
        :return:
        '''

        #准备数据
        run_group_num=['df']  #执行分组编号

        # 获取步骤
        business_info=db.query(Business.business_detail).filter(Business.id==business_id).first()
        detail_list=json.loads(business_info.business_detail)
        # LOG().info(f"detail_list{detail_list}")



        if data_name!='默认参数':
            run_group_num.clear()

            data_group_list=db.query(ApiData).filter(ApiData.business_id==business_id,
                                                     ApiData.data_group_name==data_name,
                                                     ApiData.isdelete==0).group_by(ApiData.data_group_num).all()

            run_group_num=[dg.data_group_num for dg in data_group_list]
            #LOG().info(f'业务流:{run_group_num}')

        # LOG().info(business_info)
        # 判断执行用例的类型
        tmp_business_info = db.query(Business).filter(Business.id == business_id).first()
        # LOG().info(type(tmp_business_info.business_type))
        # count=0
        if tmp_business_info.business_type==1:
            #LOG().info('进入单接口用例逻辑')
            RunSingleApi(pro_code).run_single_api(pro_code,business_id,data_name,db,summary_report_num)
            return {'code': 200, 'msg': '执行完毕！'}

        # 结果统计
        total_count = detail_list.__len__()
        fail_count = 0
        error_count = 0
        skip_count = 0

        times_count=0
        # 初始化
        if summary_report_num=='':
            summary_report_num=data_name

        report_info = {'report_num': self.report_num,
                       'business_id': business_id,
                       'summary_num': summary_report_num,
                       'summary_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'report_type': 1}
        report_item = Report(**report_info)
        db.add(report_item)
        db.commit()  # 创建测试报告

        global_value = Global_case(self.pro_code, db)

        #LOG().info(f"{len(run_group_num)},内容：{run_group_num}")
        for group_num in run_group_num:     #遍历测试数据
            times_count+=1


            for dl in detail_list:
                # 第一步获取步骤用例信息
                # 查询执行用例
                caseinfo = db.query(Case, Api, ApiData).filter(Case.id == dl, Case.api_id == Api.id,
                                                               ApiData.data_group_num == group_num,
                                                               ApiData.case_id == Case.id).first()
                #LOG().info(f"dl:{dl}")
                case_host_json = db.query(ApiHost).filter(ApiHost.id == caseinfo.Api.host_id).first()
                case_host_json = case_host_json.to_json()

                detail_info = {
                    'case_id': caseinfo.Case.id,
                    'api_name': caseinfo.Api.api_name,
                    'assert_list': json.loads(caseinfo.ApiData.assert_list),
                    'case_name': caseinfo.Case.case_name,
                    'extract_param': json.loads(caseinfo.Case.extract_param),
                    'header': json.loads(caseinfo.Case.header),
                    'header_param': json.loads(caseinfo.Case.header_param),
                    'host': case_host_json[caseinfo.ApiData.run_host],
                    'host_json': case_host_json,
                    'join_param': json.loads(caseinfo.Case.join_param),
                    'method': caseinfo.Api.method,
                    'preconditions': caseinfo.Case.preconditions,
                    'pro_code': pro_code,
                    'request_body': json.loads(caseinfo.ApiData.request_body),
                    'url': caseinfo.Api.url,
                    'url_param': caseinfo.Case.url_param,
                    'wait_time': caseinfo.Case.wait_time
                }

                cp = dict(Case_Plugin(detail_info, global_value))

                detail_info['error_tag'] = cp['error_tag']
                detail_info['api_url'] = cp['url']
                detail_info['header'] = cp['header']['result']
                detail_info['request_body'] = cp['request_body']
                detail_info['response_body'] = cp['response_body']
                detail_info['reponse_tab'] = 'reponse_tab{}'.format(caseinfo.Case.id)
                detail_info['run_time'] = cp['run_time']

                # 前置条件判断
                if cp['precond']['result'] != True:
                    detail_info['result'] = 'skip'
                    detail_info['preconditions'] = cp['preconditions']['msg']
                    skip_count += 1

                    # 报告详情
                    pre_report_detail_item = {
                        'case_name': detail_info['case_name'],
                        'api_name': detail_info['api_name'],
                        'case_id': detail_info['case_id'],
                        'url': cp['url'],
                        'method': detail_info['method'],
                        'header': json.dumps(cp['header']['result']),
                        'preconditions': detail_info['preconditions'],
                        'request_body': cp['request_body']['result'],
                        'business_id': business_id,
                        'result_info': detail_info['result'],
                        'report_num': self.report_num,
                        'response_body': [json.dumps(cp['response_body']), cp['response_body']][
                            type(cp['response_body']) == str],
                        'assert_param': json.dumps(detail_info['assert_list']),
                        'extract_param': json.dumps(detail_info['extract_param']),
                        'data_group_num': 'df',
                        'data_id': 0,
                        'run_time': detail_info['run_time'],
                        'run_host': detail_info['host']
                    }
                    pre_db_item = ReportDetail(**pre_report_detail_item)
                    db.add(pre_db_item)
                    db.commit()
                    continue

                if cp['assert_info']['isok'] == False:
                    fail_count += 1
                    detail_info['result'] = 'fail'
                else:
                    detail_info['result'] = 'ok'

                if '请求接口' in cp['error_tag']:
                    detail_info['result'] = 'error'
                    error_count += 1

                global_value = cp['global_param']

                report_detail_item = {
                    'case_name': detail_info['case_name'],
                    'api_name': detail_info['api_name'],
                    'case_id': detail_info['case_id'],
                    'url': cp['url'],
                    'method': detail_info['method'],
                    'header': json.dumps(cp['header']['result']),
                    'preconditions': cp['precond']['msg'],
                    'request_body': json.dumps(cp['request_body']['result']),
                    'business_id': business_id,
                    'result_info': detail_info['result'],
                    'report_num': self.report_num,
                    'response_body': [json.dumps(cp['response_body']), cp['response_body']][
                        type(cp['response_body']) == str],
                    'assert_param': json.dumps(detail_info['assert_list']),
                    'extract_param': json.dumps(detail_info['extract_param']),
                    'data_group_num': 'df',
                    'data_id': 0,
                    'run_time': detail_info['run_time'],
                    'run_host': detail_info['host']
                }
                detail_db_item = ReportDetail(**report_detail_item)
                db.add(detail_db_item)
                db.commit()

            ok_count = total_count - fail_count - error_count - skip_count

            report = db.query(Report).filter(Report.report_num == self.report_num).first()
            report.total_count = total_count
            report.fail_count = fail_count
            report.error_count = error_count
            report.skip_count = skip_count
            report.ok_count = ok_count
            db.commit()

        return {'code': 200, 'msg': '执行完毕！'}


if __name__ == '__main__':
    #business_id, data_name, run_host,type=0):
    print(Run_Business('Azizi').Global_value())


