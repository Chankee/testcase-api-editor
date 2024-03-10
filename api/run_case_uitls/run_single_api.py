from sqlalchemy.orm import Session
from api.run_case_uitls.case_plugin import Case_Plugin
from api.run_case_uitls.global_case_run import Global_case
from qa_dal.models import Business, ApiData,Report,ReportDetail,Case,Api,ApiHost

import datetime
import json
import math
import random

from uitls.log import LOG




class RunSingleApi():

    def __init__(self,pro_code):
        self.report_num="{}_{}".format(pro_code,str(math.floor(1e6 * random.random())))
        self.pro_code=pro_code

    def run_single_api_loop(self,detail_list,business_id,data_name,pro_code,total_count,fail_count,error_count,skip_count,db,df=False):

        for step in detail_list:
            # count+=1
            # LOG().info(count)
            LOG().info(f'步骤{step}')
            if df:
                LOG().info(f'进入默认数据逻辑')

                data_group_list = db.query(ApiData).filter(ApiData.data_group_num == 'df',
                                                           ApiData.case_id == step,
                                                           ApiData.isdelete == 0).group_by(ApiData.data_group_num).all()
            else:
                LOG().info(f'进入非默认数据逻辑')

                data_group_list = db.query(ApiData).filter(ApiData.business_id == business_id,
                                                           ApiData.data_group_name == data_name,
                                                           ApiData.case_id == step,
                                                           ApiData.isdelete == 0).group_by(ApiData.data_group_num).all()
            LOG().info(data_group_list)
            LOG().info(len(data_group_list))

            run_group_num = [dg.data_group_num for dg in data_group_list]
            LOG().info(f"数据名称：{run_group_num}")

            if run_group_num == []: continue

            global_value = Global_case(pro_code, db)  # 获取全局变量

            caseinfo = db.query(Case, Api, ApiData).filter(Case.id == step, Case.api_id == Api.id,
                                                           ApiData.data_group_num.in_(run_group_num),
                                                           ApiData.case_id == Case.id, ApiData.isdelete == 0,
                                                           ).all()
            LOG().info(len(caseinfo))

            for case in caseinfo:
                LOG().info(f"{step}执行{case}")

                # 第一步获取步骤用例信息
                # 查询执行用例
                # caseinfo = db.query(Case, Api, ApiData).filter(Case.id == step, Case.api_id == Api.id,
                #                                                ApiData.data_group_num == group_num,
                #                                                ApiData.case_id == Case.id).first()

                case_host_json = db.query(ApiHost).filter(ApiHost.id == case.Api.host_id).first()
                case_host_json = case_host_json.to_json()

                detail_info = {
                    'case_id': case.Case.id,
                    'api_name': case.Api.api_name,
                    'assert_list': json.loads(case.ApiData.assert_list),
                    'case_name': case.Case.case_name,
                    'extract_param': json.loads(case.Case.extract_param),
                    'header': json.loads(case.Case.header),
                    'header_param': json.loads(case.Case.header_param),
                    'host': case_host_json[case.ApiData.run_host],
                    'host_json': case_host_json,
                    'join_param': json.loads(case.Case.join_param),
                    'method': case.Api.method,
                    'preconditions': case.Case.preconditions,
                    'pro_code': pro_code,
                    'request_body': json.loads(case.ApiData.request_body),
                    'url': case.Api.url,
                    'url_param': case.Case.url_param,
                    'wait_time': case.Case.wait_time
                }

                cp = dict(Case_Plugin(detail_info, global_value))

                detail_info['error_tag'] = cp['error_tag']
                detail_info['api_url'] = cp['url']
                detail_info['header'] = cp['header']['result']
                detail_info['request_body'] = cp['request_body']
                detail_info['response_body'] = cp['response_body']
                detail_info['reponse_tab'] = 'reponse_tab{}'.format(case.Case.id)
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
                    'data_group_num': case.ApiData.data_group_num,
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
            LOG().info('数据库提交')
        return {'code': 200, 'msg': '单接口参数化执行完毕！'}

    def run_single_api(self,pro_code,business_id, data_name,db:Session,summary_report_num):
        '''
        执行单接口
        :return:
        '''

        #准备数据
        run_group_num=['df']  #执行分组编号

        # 获取步骤
        business_info=db.query(Business.business_detail).filter(Business.id==business_id).first()
        detail_list=json.loads(business_info.business_detail)
        LOG().info(business_id)
        # count=0
        if data_name!='默认参数':
            run_group_num.clear()

            # 结果统计
            total_count = detail_list.__len__()
            fail_count = 0
            error_count = 0
            skip_count = 0

            # 初始化
            report_info = {'report_num': self.report_num,
                           'business_id': business_id,
                           'summary_num': data_name,
                           'summary_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'report_type': 1}
            report_item = Report(**report_info)
            db.add(report_item)
            db.commit()  # 创建测试报告
            self.run_single_api_loop(detail_list,business_id,data_name,pro_code,total_count,
                                     fail_count,error_count,skip_count,db)
            return {'code': 200, 'msg': '数据参数化执行完毕！'}
        else:
            # 结果统计
            total_count = detail_list.__len__()
            fail_count = 0
            error_count = 0
            skip_count = 0

            # 初始化
            report_info = {'report_num': self.report_num,
                           'business_id': business_id,
                           'summary_num': summary_report_num,
                           'summary_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'report_type': 1}
            report_item = Report(**report_info)
            db.add(report_item)
            db.commit()  # 创建测试报告
            self.run_single_api_loop(detail_list, business_id, data_name, pro_code, total_count,
                                     fail_count, error_count, skip_count, db,df=True)

            return {'code': 200, 'msg': '单接口参数化执行完毕！'}

        # 执行df的数据逻辑
        #     结果统计
        total_count = detail_list.__len__()
        fail_count = 0
        error_count = 0
        skip_count = 0

        # 初始化
        report_info = {'report_num': self.report_num,
                       'business_id': business_id,
                       'summary_num': summary_report_num,
                       'summary_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'report_type': 1}
        report_item = Report(**report_info)
        db.add(report_item)
        db.commit()  # 创建测试报告
        self.run_single_api_loop(detail_list, business_id, data_name, pro_code, total_count,
                                 fail_count, error_count, skip_count, db)

        return {'code': 200, 'msg': 'df执行完毕！'}
