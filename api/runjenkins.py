import asyncio

import sqlalchemy.exc
from sqlalchemy import func

from api.run_case_uitls.run_single_api import RunSingleApi
from api.run_case_uitls.run_business import Run_Business
from uitls.read_config import ReadConfig as rc
from api.run_case_uitls.case_plugin import Case_Plugin
from api.run_case_uitls.global_case_run import Global_case
from qa_dal.database import get_api_db,get_sso_db
from qa_dal.models import JenkinsRecord, Business, ApiData, Report, ReportDetail, Case, Api, ApiHost, Job,User
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from uitls.log import LOG
from lxml import etree
from urllib import parse

import json
import math
import datetime
import urllib.parse as parse
import random
import jenkins
import os
import time

# 获取jenkins配置
from uitls.send_report import Send_Report

jenkins_url = rc().read_config('dbconfig', 'Jenkins', 'host')
user_name = rc().read_config('dbconfig', 'Jenkins', 'user_name')
password = rc().read_config('dbconfig', 'Jenkins', 'password')

# 初始化jenkins服务对象
server = jenkins.Jenkins(f"http://{jenkins_url}", username=user_name, password=password)
# server = jenkins.Jenkins(f"http://127.0.0.1:8887", username="admin", password='1126defeccb84ba2a248d23942da2f4ce5')

report_num_list = []

router = APIRouter(
    prefix="/api/jenkins",
    tags=["定时任务"]
)


def update_jenkins_job(pro_code: str = '', job_name: str = '', run_type: int = -1, run_time=10,
                       run_state: int = -1, job_id="", business_list: list = [], data_name='非默认'):
    """

    :param pro_code:
    :param job_name:
    :param run_type:
    :param run_state:
    :return: 创建成功200,重复创建201,创建失败202
    """
    base_file_url = os.path.abspath(os.path.dirname(__file__)).replace('/api', '')
    default_local_conf = etree.tostring(etree.parse(f'{base_file_url}/conf/jenkins_conf.xml'), encoding='utf-8').decode(
        'utf-8')

    # origin_conf
    time_conf_oj = etree.HTML(default_local_conf.encode('utf-8'))
    time_num_ob = time_conf_oj.xpath('//spec')  # 获取修改
    # LOG().info(f"run_time:{run_time}")

    if run_type == 2:
        time_num_ob[0].text = run_time  # 修改配置里面的运行分钟数
        time_conf = time_conf_oj.xpath('//spec')[0].text
        conf_run_times = time_conf.split(' ')[0].split('/')[1]  # 获取jenkins配置的每多少分钟运行一次
        # LOG().info(conf_run_times)

    elif run_type == 1:
        # conf_run_times = ','.join([str(i) for i in run_time])
        time_num_ob[0].text = run_time  # 修改每天需要运行的小时，如每天10点跟18点
        time_conf = time_conf_oj.xpath('//spec')[0].text

    switch_dict = {0: "false", 1: "true"}
    time_conf_oj.xpath('//disabled')[0].text = switch_dict[run_state]  # 修改
    # LOG().info(time_conf_oj)
    # server.reconfig_job(job_name,etree.tostring(time_conf_oj,encoding='utf-8').decode('utf-8'))

    time_conf_tmp = etree.tostring(time_conf_oj, encoding='utf-8').decode('utf-8')
    config_xml = time_conf_tmp.replace('<html><body>', '').replace('</body></html>', '')
    # config_xml = re.sub(r'<?xml version="1.0" encoding="UTF-8"?>', r'<?xml version="1.0" encoding="UTF-8"?>\n',
    #                     # config_xml, 1)
    config_xml = config_xml.replace('timertrigger', 'TimerTrigger')
    config_xml = config_xml.replace('configuredlocalrules', 'configuredLocalRules')
    config_xml = config_xml.replace('hudson.tasks.shell', 'hudson.tasks.Shell')
    config_xml = config_xml.replace('{{job_id}}', str(job_id))
    # LOG().info(config_xml)

    if server.job_exists(job_name):
        '''
        假如job是已经存在，更新job的配置
        '''
        # LOG().info(config_xml)

        server.reconfig_job(job_name, config_xml)  # 修改jenkins的配置

        # LOG().info(server.get_job_config(job_name))
        # server.build_job(job_name)

        return {'code': 201, 'msg': '修改成功！'}

    else:
        server.create_job(job_name, config_xml=config_xml)
        is_find = server.job_exists(job_name)
        if is_find: return {'code': 200, 'msg': 'job创建成功'}
        return {'code': 202, 'msg': 'job创建失败'}


def del_jenkins_job(job_name: str):
    server.delete_job(job_name)
    is_exist = server.job_exists(job_name)
    if is_exist: return {'code': 201, 'msg': '删除失败'}
    return {'code': 200, 'msg': '删除成功'}


def get_build_running_result(job_name: str):
    try:
        server.assert_job_exists(job_name)
    except Exception as e:
        print(e)
        job_statue = '1'

    # 判断job是否处于排队状态
    inQueue = server.get_job_info(job_name)['inQueue']
    run_time = ''
    if str(inQueue) == 'True':
        job_statue = 'pending'
        running_number = server.get_job_info(job_name)['nextBuildNumber']
    else:
        # 先假设job处于running状态，则running_number = nextBuildNumber -1 ,执行中的job的nextBuildNumber已经更新
        running_number = server.get_job_info(job_name)['nextBuildNumber'] - 1
        try:
            running_status = server.get_build_info(job_name, running_number)['building']
            if str(running_status) == 'True':
                job_statue = 'running'
                job_run_all_info = server.get_build_info(job_name, running_number)
                run_time = job_run_all_info['timestamp']
                now = time.localtime(run_time / 1000)
                run_time = time.strftime("%Y-%m-%d %H:%M:%S", now)
            else:
                # 若running_status不是True说明job执行完成
                job_run_all_info = server.get_build_info(job_name, running_number)
                job_statue = job_run_all_info['result']
                run_time = job_run_all_info['timestamp']
                now = time.localtime(run_time / 1000)
                run_time = time.strftime("%Y-%m-%d %H:%M:%S", now)
        except Exception as e:
            # 上面假设job处于running状态的假设不成立，则job的最新number应该是['lastCompletedBuild']['number']
            lastCompletedBuild_number = server.get_job_info(job_name)['lastCompletedBuild']['number']
            job_statue = server.get_build_info(job_name, lastCompletedBuild_number)['result']

    return job_statue, running_number, run_time


@router.get("/getresult")
def get_run_result(job_id: int, job_name: str, db: Session = Depends(get_api_db)):
    # result={}
    item = {}
    item['job_id'] = job_id
    item['report_id'] = 1

    while True:
        job_statue, running_number, run_time = get_build_running_result(job_name)
        # LOG().info(f"{job_statue}__{running_number}", )

        if job_statue == "FAILURE":
            item['build_id'] = int(running_number)
            item['run_time'] = run_time
            item['run_result'] = job_statue
            result = {'code': 201, 'msg': f'#{running_number}构建失败', 'item': item}
            save_result(result['item'], db)
            break
        elif job_statue == 'SUCCESS':
            # print('构建成功')
            item['build_id'] = int(running_number)
            item['run_time'] = run_time
            item['run_result'] = job_statue
            # LOG().info(server.get_build_info(job_name, running_number))  # 检查构建的信息
            result = {'code': 200, 'msg': f'#{running_number}构建成功', 'item': item}
            save_result(result['item'], db)

            break
        elif job_statue == 'ABORTED':
            item['build_id'] = int(running_number)
            item['run_time'] = run_time
            item['run_result'] = job_statue
            # LOG().info(server.get_build_info(job_name, running_number))  # 检查构建的信息
            result = {'code': 200, 'msg': f'#{running_number}构建终止', 'item': item}
            save_result(result['item'], db)
            break
        time.sleep(5)
    return result


def save_result(item, db: Session):
    db_item = JenkinsRecord(**item)
    db.add(db_item)
    db.commit()
    return {'code': 200, 'msg': '数据库操作成功！'}


def send_report(job_name, summary_report_num,db:Session,report_name='',sysdb=''):
    # 获取@人列表
    phone_list=[]
    user_list=[]
    job_info=db.query(Job).filter(Job.job_name==job_name,Job.isdelete==0).first()
    # LOG().info(job_info.job_name)

    dingding_token=job_info.dingding_token
    # LOG().info(f'queren{job_info.dingding_token}')

    if ',' in job_info.notice:
        user_list=job_info.notice.split(',')
    else:
        user_list.append(job_info.notice)
    # LOG().info(f'test{user_list}')

    for user_name in user_list:
        phone = sysdb.query(User).filter(User.user_name == user_name,User.isdelete == 0).first()
        phone_list.append(phone.tel)


    # 拼接报告文本发送钉钉

    run_result = get_job_report(db,summary_report_num)

    if  int(run_result["pass_percen"]) < 100:
        at_list=phone_list
    else:
        at_list = []


    text_info = '***********************{}***********************\n'.format(job_name)
    text_info += f'[执行结果]：测试完成\n总运行用例:{run_result["total"]}\n成功：{run_result["ok_count"]}\n失败：{run_result["fail_count"]}\n错误：{run_result["error_count"]}\n跳过：{run_result["skip_count"]}\n通过率：{run_result["pass_percen"]}%\n[报告情]：http://gz-qa.inkept.cn/qa_view/#/job_report?summary_num={summary_report_num}'

    Send_Report().send_dingding(text_info, dingding_token, at_list)


def get_job_report(db: Session,summary_num: str = ''):
    # 汇总
    result = db.query(func.sum(Report.total_count).label('total'), func.sum(Report.ok_count).label('ok_count'),
                      func.sum(Report.fail_count).label('fail_count'),
                      func.sum(Report.error_count).label('error_count'),
                      func.sum(Report.skip_count).label('skip_count')).filter(Report.summary_num == summary_num).first()

    summary_total = {'total': 0, 'ok_count': 0, 'fail_count': 0, 'error_count': 0, 'skip_count': 0, 'pass_percen': 0}
    if result != None:
        if result.total not in (None, 0):
            summary_total['total'] = result.total
            summary_total['ok_count'] = result.ok_count
            summary_total['fail_count'] = result.fail_count
            summary_total['error_count'] = result.error_count
            summary_total['skip_count'] = result.skip_count
            summary_total['pass_percen'] = round(result.ok_count / result.total * 100, 2)

    return summary_total


@router.get("/runbstask")
def run_business_task(job_id, db: Session = Depends(get_api_db),sysdb:Session=Depends(get_sso_db)):
    '''
   执行定时任务
   :return:
   '''
    try:
        data_name = '非默认'

        # 获取job_name，项目名，业务流列表
        job = db.query(Job).filter(Job.id == job_id).first()
        job_name = job.job_name
        pro_code = job.pro_code
        tmp_business_list = json.loads(job.business_list)
        business_task_list = [i['business_id'] for i in tmp_business_list]

        # 获取business 类型
        business_type = db.query(Business.business_type).filter(Business.id == business_task_list[0]).first()[0]
        # business_info = db.query(Business.).filter(Business.id == business_task_list[1]).first()[0]

        # 报告id生成
        summary_report_num = "{}_summary_{}".format(pro_code, str(math.floor(1e6 * random.random())))
        report_num_list.append(summary_report_num)  # 临时存放生成的报告编号

        task_info = {}
        all_data = []
        # count=0

        for items in tmp_business_list:
            for data in items['data_name']:
                if data not in all_data:
                    # business_info = db.query(Business.business_detail).filter(Business.id == items['business_id']).first()
                    # detail_list = json.loads(business_info.business_detail)
                    task_info[f'{data}'] = []
                    all_data.append(data)

        for items in tmp_business_list:
            for data in items['data_name']:
                task_info[data].append(items['business_id'])

        if business_type == 1:  # 单接口业务流

            for items in task_info.items():
                for business_id in items[1]:
                    # LOG().info(f"{business_id}")
                    RunSingleApi(pro_code).run_single_api(pro_code, business_id, items[0], db, summary_report_num)

        elif business_type == 0:
            for items in task_info.items():
                for business_id in items[1]:
                    # LOG().info(f"执行业务流：{business_id}")
                    # LOG().info(f"items索引：{items[0]}")
                    Run_Business(pro_code).run_business(pro_code, business_id, items[0], db, summary_report_num)


        # 获取存jenkins记录表的相关信息
        item = {}
        item['job_id'] = job_id
        item['report_id'] = summary_report_num
        job_statue, running_number, run_time = get_build_running_result(job_name)
        item['build_id'] = int(running_number)
        item['run_time'] = run_time
        item['run_result'] = 'SUCCESS'

        # 保存到jenkins的运行记录表
        save_result(item, db)
        send_report(job_name, summary_report_num,db,job.notice,sysdb)
        return {'code': 200, 'msg': '执行成功！', 'summary_report_num': summary_report_num}

    except sqlalchemy.exc.OperationalError as sql_ex:
        LOG().ex_position(sql_ex)
        job_name = db.query(Job.job_name).filter(Job.id == job_id).first()[0]

        # 获取存jenkins记录表的相关信息
        item = {}
        item['job_id'] = job_id
        item['report_id'] = report_num_list[0]
        job_statue, running_number, run_time = get_build_running_result(job_name)
        item['build_id'] = int(running_number)
        item['run_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        item['run_result'] = 'SUCCESS'

        # 保存到jenkins的运行记录表
        save_result(item, db)
        send_report(job_name, item['report_id'],db,'',sysdb)
        return {'code': 200, 'msg': '业务流执行完毕，补录数据库！', 'summary_report_num': item['report_id']}
    except Exception as ex:
        LOG().ex_position(ex)
        job_name = db.query(Job.job_name).filter(Job.id == job_id).first()[0]

        # 获取存jenkins记录表的相关信息
        item = {}
        item['job_id'] = job_id
        item['report_id'] = report_num_list[0]
        job_statue, running_number, run_time = get_build_running_result(job_name)
        item['build_id'] = int(running_number)
        item['run_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        item['run_result'] = 'FAILURE'

        # 保存到jenkins的运行记录表
        save_result(item, db)
        send_report(job_name, item['report_id'],db,'',sysdb)
        return {'code': 201, 'msg': '业务流执行失败！', 'summary_report_num': item['report_id']}
