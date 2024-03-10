from sqlalchemy import func
from fastapi import APIRouter,File, UploadFile
from fastapi import Depends
from qa_dal.testmanage import testcase_schemas
from qa_dal.database import get_case_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from sqlalchemy import or_,and_
from qa_dal.models import jira_model,User,Delay,TestCase,Version,MySelfRecord,PlanVersion,Project,MailConf,MailRecord
from qa_dal import qa_uitls
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from decimal import Decimal
from dateutil.parser import parse
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel

import common.jira_base as jira_com
import math
import random
import os
import smtplib
from uitls.send_mail import mailimg

router = APIRouter(
    prefix="/summary/report",
    tags=["质量月报"]
)


class SendMail(BaseModel):
    title: Optional[str]
    to_mail: Optional[str]
    cc_mail: Optional[str]
    mail_type: Optional[int]
    jira_id: Optional[str]
    mail_type:Optional[int]
    sendname:Optional[str]
    file_path:Optional[str]
    url:Optional[str]



@router.post("/sendmail")
async def sendmail(item:SendMail,db:Session=Depends(get_case_db)):
    try:
        #发送邮件
        content='<p><h1 style="text-align:center">{}<h1></p><p style="font-size:13px">完整报表链接:<a href="{}" target="_blank">{}</a></p><p><img src="cid:image1"></p>'.format(item.title,item.url,item.url)
        result=mailimg(item.title,item.to_mail.split(','),item.cc_mail.split(','),content,item.file_path)

        if result==False: return {'code':202,'msg':'发送邮件失败，请检查邮件地址！'}

        mail_conf=db.query(MailConf).filter(MailConf.jira_id==item.jira_id,MailConf.mail_type==item.mail_type).first()
        if mail_conf==None:
            item_info=item.dict()
            del item_info['title']
            del item_info['sendname']
            del item_info['file_path']
            del item_info['url']
            db_item = MailConf(**item_info)
            db.add(db_item)
            db.commit()
        else:
            #更新邮件地址
            if mail_conf.to_mail!=item.to_mail: mail_conf.to_mail=item.to_mail
            if mail_conf.cc_mail!=item.cc_mail: mail_conf.cc_mail=item.cc_mail
            db.commit()

        #保存邮件记录
        add_record = item.dict()
        add_record['content']=content
        del add_record['file_path']
        del add_record['url']
        record_item = MailRecord(**add_record)
        db.add(record_item)
        db.commit()

        return {'code':200,'msg':'发送成功！'}
    except smtplib.SMTPException as e:
        return {'code':500,'msg':str(e)}


@router.get("/img")
async def img(filepath:str=''):
    file_like = open(filepath, mode="rb")
    return StreamingResponse(file_like, media_type="image/jpg")

@router.get("/get_conf")
async def img(jira_id:str='',mail_type:int=1,db:Session=Depends(get_case_db)):
    mail_conf = db.query(MailConf).filter(MailConf.jira_id == jira_id, MailConf.mail_type == mail_type).first()
    mail_detail = {'to_mail': '', 'cc_mail': ''}
    if mail_conf!=None:
        mail_detail['to_mail']=mail_conf.to_mail
        mail_detail['cc_mail']=mail_conf.cc_mail
    return {'code':200,'msg':mail_detail}


@router.post("/upload")
async def upload(file: UploadFile = File(...),jira_id:str=''):
    '''
    上传月报
    :param file:
    :return:
    '''
    try:
        file_name =str(math.floor(1e6 * random.random()))
        base_path=os.path.abspath(os.path.dirname(__file__)).replace('\\','/')
        file_data = await file.read()

        #获取文件后缀
        path=file.filename.split(".")[1]
        file_path='{}/upload/testcase/{}'.format(base_path,'{}_{}.{}'.format(jira_id,file_name,path))
        file_path=file_path.replace('/summary','')
        #保存文件
        with open(file_path,"wb+") as fp:
            fp.write(file_data)
        fp.close()



        return {'code':200,'msg':file_path}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/version_list")
async def get_version_list(pro_code:str,token:str='',db:Session=Depends(get_sso_db)):
    try:
        jira_clt = jira_com.INKE_JIRA(ticket=token)
        version_list=list(reversed([item.name for item in jira_clt.project_versions(pro_code)]))
        return {'code':200,'msg':version_list}

    except Exception as ex:
        jira_info=db.query(Project.jira_id).filter(Project.pro_code==pro_code).first()
        if jira_info!=None:
            jira_clt = jira_com.INKE_JIRA(ticket=token)
            version_list = list(reversed([item.name for item in jira_clt.project_versions(jira_info.jira_id)]))
            return {'code': 200, 'msg': version_list}
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/summary")
async def get_total_list(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str='',apidb:Session=Depends(get_sso_db),db:Session=Depends(get_case_db)):
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        #初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type=='version': jql_param+=' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type=='time': jql_param+=' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param,maxResults=2000)

        summary_json={'version_summary':[],'team_summary':[],'user_summary':[]}

        version_count,team_count,user_count={},{},{}

        for bug in bug_list:

            '''版本维度数据'''
            bug_version = bug.fields.versions  # 影响版本
            version_name=''
            if bug_version: version_name = bug_version[0].name

            count_summary(bug,version_name,version_count)


            '''团队维度数据'''
            belong = bug.fields.customfield_11302  # 影响版本
            components = bug.fields.components

            df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                       "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                       "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                       "安卓": "Android", "Unity3D": "Unity3D","长沙后台":"长沙后台",
                       "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序","产运":"产运","其他":"其他"}

            team_name = ''
            if belong:
                team_name = belong.value
            else:
                if components != []:
                    if components[0].name in df_json.keys(): team_name = df_json[components[0].name]

            count_summary(bug,team_name,team_count)



            '''个人维度数据'''
            assignee=bug.fields.assignee
            assignee_name=''
            if assignee: assignee_name=assignee.displayName

            count_summary(bug, assignee_name, user_count)



        '''计算百分率'''
        summary_version=[]
        summary_user=[]
        bug_summary('version',version_count,summary_json['version_summary'],apidb,db,pro_code,summary_version,summary_user)  #计算版本百分率
        bug_summary('user',user_count, summary_json['user_summary'],apidb,db,pro_code,summary_version,summary_user)  # 计算个人百分率
        bug_summary('team', team_count, summary_json['team_summary'], apidb, db, pro_code, summary_version,summary_user)  # 计算团队百分率

        return {'code':200,'msg':summary_json}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




def bug_summary(summary_type,count_info,summary_name,apidb,db,pro_code,summary_version,summary_user):
    '''计算百分率'''
    for key in count_info:

        total = count_info[key]['total']

        detail_info = {'name': key, 'total': count_info[key]['total'],
                       'unresolved_count': count_info[key]['unresolved_count'],  # 未解决数
                       'resolved_percen': 0,  # 已解决率
                       'bequeath_percen': 0,  # 遗留bug率
                       'online_percen': 0,  # 线上缺陷率
                       'reopen_percen': 0,  # 重开率
                       'highest_percen': 0,  # 高单比例
                       'avg_time_percen': 0,  # 平均解决周期
                       'deylay_percen': 0,  # 日结率
                       'over_delay_percen': 0,  # 超一天缺陷占比
                       'resolved_count':count_info[key]['resolved_count'],
                       'myself_percen':100} # 自测通过率

        '''获取自测用例'''
        if summary_type=='version':
            project_code=apidb.query(Project.pro_code).filter(Project.jira_id==pro_code).first()
            planversion=db.query(PlanVersion.id).filter(PlanVersion.version_name==key,PlanVersion.isdelete==0,PlanVersion.pro_code==project_code.pro_code).first()
            if planversion!=None:
                summary_version.append(planversion.id)
                version_total=db.query(MySelfRecord).filter(MySelfRecord.check_result.in_(['PASS','FAIL','未验收']),MySelfRecord.plan_version_id==planversion.id,MySelfRecord.isdelete==0).count()
                version_run_total = db.query(MySelfRecord).filter(MySelfRecord.check_result.in_(['PASS', 'FAIL']),
                                                              MySelfRecord.plan_version_id == planversion.id,
                                                              MySelfRecord.isdelete == 0).count()
                version_pass_count=db.query(MySelfRecord).filter(MySelfRecord.check_result=='PASS',MySelfRecord.plan_version_id==planversion.id,MySelfRecord.isdelete==0).count()
                if version_total>0:
                    if version_run_total>0:
                        detail_info['myself_percen']=round(version_pass_count/version_run_total*100,2)
                    else:
                        detail_info['myself_percen'] = 0

        if summary_type=='user' and len(summary_version)>0:
            summary_user.append(key)
            user_total = db.query(MySelfRecord).filter(MySelfRecord.check_result.in_(['PASS', 'FAIL', '未验收']),MySelfRecord.plan_version_id.in_(summary_version),MySelfRecord.isdelete == 0,MySelfRecord.name==key).count()
            user_run_total = db.query(MySelfRecord).filter(MySelfRecord.check_result.in_(['PASS', 'FAIL']),
                                                       MySelfRecord.plan_version_id.in_(summary_version),
                                                       MySelfRecord.isdelete == 0, MySelfRecord.name == key).count()
            user_pass_count = db.query(MySelfRecord).filter(MySelfRecord.check_result == 'PASS',
                                                       MySelfRecord.plan_version_id.in_(summary_version),
                                                       MySelfRecord.isdelete == 0,MySelfRecord.name==key).count()
            if user_total > 0:
                if user_run_total>0:
                    detail_info['myself_percen'] = round(user_pass_count / user_run_total * 100, 2)
                else:
                    detail_info['myself_percen'] = 0


        if summary_type == 'team' and len(summary_version) > 0:
            team_json = {'Android': 'androiddev', 'H5前端': 'h5dev', 'iOS': 'iosdev','金融中台':'financedev',
                         '服务端': 'serverdev', '运营后台': 'managedev', 'Unity3D': 'unitydev', '微信小程序': 'appletdev',
                         '产运': 'product','其他':'other','长沙后台':'other'}
            user_list=apidb.query(User).filter(User.pro_fun==team_json[key],User.isdelete==0).all()
            new_user=[user.user_name for user in user_list if user.user_name in summary_user]
            if len(new_user)>0:
                team_total = db.query(MySelfRecord).filter(MySelfRecord.check_result.in_(['PASS', 'FAIL', '未验收']),
                                                      MySelfRecord.plan_version_id.in_(summary_version),
                                                      MySelfRecord.isdelete == 0, MySelfRecord.name.in_(new_user)).count()
                team_run_total = db.query(MySelfRecord).filter(MySelfRecord.check_result.in_(['PASS', 'FAIL']),
                                                           MySelfRecord.plan_version_id.in_(summary_version),
                                                           MySelfRecord.isdelete == 0,
                                                           MySelfRecord.name.in_(new_user)).count()
                team_pass_count = db.query(MySelfRecord).filter(MySelfRecord.check_result == 'PASS',
                                                           MySelfRecord.plan_version_id.in_(summary_version),
                                                           MySelfRecord.isdelete == 0, MySelfRecord.name.in_(new_user)).count()
                if team_total > 0:
                    if team_run_total>0:
                        detail_info['myself_percen'] = round(team_pass_count / team_run_total * 100, 2)
                    else:
                        detail_info['myself_percen'] = 0


        if total>0:detail_info['resolved_percen']=round(count_info[key]['resolved_count'] / count_info[key]['total'] * 100, 2)
        if total > 0: detail_info['bequeath_percen'] = round(count_info[key]['unresolved_count'] / total * 100, 2)
        if total > 0: detail_info['online_percen'] = round(count_info[key]['online_count'] / total * 100, 2)
        if total > 0: detail_info['reopen_percen'] = round(count_info[key]['reopen_count'] / total * 100, 2)
        if total > 0: detail_info['highest_percen'] = round(count_info[key]['highest_count'] / total * 100, 2)
        if count_info[key]['avg_time_total'] > 0: detail_info['avg_time_percen'] =round(count_info[key]['avg_time'] / count_info[key]['avg_time_total'],2)

        # 计算日结率
        total_other = 0
        total_dalay_parcen = 0
        date_count = 0

        # 计算每天的日结率
        date_item = count_info[key]['delay_json']
        for item in date_item:
            if date_item[item]['total']>0:total_other += date_item[item]['other_count']
            if date_item[item]['total']>0:total_dalay_parcen += round(date_item[item]['dalay_count'] / date_item[item]['total'] * 100, 2)
            date_count += 1
        if date_count>0: detail_info['deylay_percen'] = round(total_dalay_parcen / date_count, 2)
        if total>0: detail_info['over_delay_percen'] = round(total_other / total*100, 2)

        summary_name.append(detail_info)




def count_summary(bug,name,count_info):
    '''
    各维度数量统计
    '''
    resolution = bug.fields.resolution  # 解决结果
    resolutiondate = bug.fields.resolutiondate  # 解决时间
    online = bug.fields.customfield_10102  # 缺陷来源
    reopen = bug.fields.customfield_10103  # 是否重开
    highest = bug.fields.priority
    created = str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))

    if name in count_info.keys() and name!='':

        # 所有bug
        count_info[name]['total'] += 1

        # 未解决缺陷数
        if resolution:
            if resolution.name in ('Unresolved','未解决','下版修复','需求纳入版本计划'):
                count_info[name]['unresolved_count'] += 1
        elif resolution==None:
            count_info[name]['unresolved_count'] += 1

        # 已解决缺陷数
        if resolution:
            if resolution.name in ('已修正','不必改'):
                count_info[name]['resolved_count'] += 1

        # 线上缺陷数
        if online:
            if online.value == '线上问题': count_info[name]['online_count'] += 1
        # 重开数
        if reopen:
            if reopen.value == 'yes': count_info[name]['reopen_count'] += 1
        # highest数
        if highest == 'Highest': count_info[name]['highest_count'] += 1

        if resolutiondate:

            # 平均解决周期
            if get_time(created, str(datetime.strptime(resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800')))>0:
                count_info[name]['avg_time'] += get_time(created, str(datetime.strptime(resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800')))
            count_info[name]['avg_time_total'] += 1

            # 日结率
            # 判断日期是否存在
            resolved = str(datetime.strptime(resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800'))

            if count_info[name]['delay_json'].get(created[0:10]) == None:
                count_info[name]['delay_json'][created[0:10]] = {'other_count': 0, 'dalay_count': 0, 'total': 1}
            else:
                count_info[name]['delay_json'][created[0:10]]['total'] += 1

            other_count = count_info[name]['delay_json'][created[0:10]]['other_count']
            dalay_count = count_info[name]['delay_json'][created[0:10]]['dalay_count']

            if created[0:10] == resolved[0:10]:  # 获取当天的
                dalay_count += 1
            elif created[0:10] != resolved[0:10]:  # 判断超过当天的
                date_list = getEveryDay(created[0:10], resolved[0:10])

                # 去除节假日
                for date in date_list:
                    if is_holiday(datetime.strptime(date, "%Y-%m-%d")):
                        date_list.remove(date)

                # 只有一天的跨度
                if len(date_list) <= 2:
                    create_time = parse(created)
                    resolved_time = parse(resolved)

                    # 判断是否小于24小时
                    if ((resolved_time - create_time).total_seconds()) / 3600 < 24:
                        dalay_count += 1
                    else:
                        other_count += 1

                # 计划跨度是否节假日
                elif len(date_list) > 2:
                    other_count += 1

            count_info[name]['delay_json'][created[0:10]]['other_count'] = other_count
            count_info[name]['delay_json'][created[0:10]]['dalay_count'] = dalay_count


    elif name not in count_info.keys() and name!='':
        count_info[name] = {'total': 1, 'unresolved_count': 0, 'resolved_count': 0, 'online_count': 0,
                               'reopen_count': 0, 'highest_count': 0, 'avg_time': 0, 'avg_time_total': 0,
                               'delay_json': {}}

        # 未解决缺陷数
        if resolution:
            if resolution.name in ('Unresolved', '未解决', '下版修复', '需求纳入版本计划'):
                count_info[name]['unresolved_count'] += 1
        elif resolution == None:
            count_info[name]['unresolved_count'] += 1

        # 已解决缺陷数
        if resolution:
            if resolution.name in ('已修正', '不必改'):
                count_info[name]['resolved_count'] += 1

        # 线上缺陷数
        if online:
            if online.value == '线上问题': count_info[name]['online_count'] += 1
        # 重开数
        if reopen:
            if reopen.value == 'yes': count_info[name]['reopen_count'] += 1
        # highest数
        if highest == 'Highest': count_info[name]['highest_count'] += 1

        other_count = 0
        dalay_count = 0

        if resolutiondate:
            resolved = str(datetime.strptime(resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800'))

            # 平均解决周期
            if get_time(created, resolved)>0:
                count_info[name]['avg_time'] += get_time(created, resolved)
            count_info[name]['avg_time_total'] += 1

            # 版本日结率
            if created[0:10] == resolved[0:10]:  # 获取当天的
                dalay_count = 1
            elif created[0:10] != resolved[0:10]:  # 判断超过当天的
                date_list = getEveryDay(created[0:10], resolved[0:10])

                # 去除节假日
                for date in date_list:
                    if is_holiday(datetime.strptime(date, "%Y-%m-%d")):
                        date_list.remove(date)

                # 只有一天的跨度
                if len(date_list) <= 2:
                    create_time = parse(created)
                    resolved_time = parse(resolved)

                    # 判断是否小于24小时
                    if ((resolved_time - create_time).total_seconds()) / 3600 < 24:
                        dalay_count = 1
                    else:
                        other_count = 1

                # 计划跨度是否节假日
                elif len(date_list) > 2:
                    other_count = 1

        count_info[name]['delay_json'][created[0:10]] = {'other_count': other_count, 'dalay_count': dalay_count,'total': 1}




def getEveryDay(begin_date,end_date):
    '''
    获取时间间隔列表
    '''
    date_list = []
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date,"%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += timedelta(days=1)
    return date_list



def get_time(created_time,reso_time):
    # 拆分日期部分 # 获取bug解决时间（created-resolutiondate 去除周六日）
    c = created_time.split(' ')
    r = reso_time.split(' ')
    create_day = datetime.strptime(c[0], '%Y-%m-%d').date()
    reso_day = datetime.strptime(r[0], '%Y-%m-%d').date()
    # 拆分时间部分
    create_t = datetime.strptime(c[1], "%H:%M:%S")
    reso_t = datetime.strptime(r[1], "%H:%M:%S")
    if reso_day < create_day or (reso_day == create_day and reso_t < create_t):
        return Decimal(0.0)

    temp = datetime.strptime('00:00:00', "%H:%M:%S")
    start = create_day
    count = 0
    seconds_diff = 0
    # 在同一天直接时间部分相减（无论工作日休息日）
    if create_day == reso_day:
        seconds_diff = (reso_t - create_t).seconds
    # 相邻两天
    elif (create_day + timedelta(days=1)) == reso_day:
        seconds_diff = (reso_t.hour * 60 * 60 + (reso_t.minute * 60) + reso_t.second) + (temp - create_t).seconds
    else:
        # 计算工作日天数
        while True:
            if start > reso_day:
                break
            if is_workday(start):
                count += 1
            start += timedelta(days=1)
        # 创建日期和解决日期均为休息日（非同一周）
        if is_holiday(create_day) and is_holiday(reso_day):
            seconds_diff = count * 24 * 60 * 60
        # 创建日期在休息日 创建时间按照之后第一个工作日0点算
        elif is_holiday(create_day):
            seconds_diff = count * 24 * 60 * 60 - (temp - reso_t).seconds
        # 解决日期在休息日 解决时间按前一个工作日晚24点算
        elif is_holiday(reso_day):
            seconds_diff = count * 24 * 60 * 60 - (create_t.hour * 60 * 60 + (create_t.minute * 60) + create_t.second)
        # 创建时间解决时间都不在休息日 计算方式：工作日总时间-0点到创建时间时长-解决时间到0点时常  （工作日天数 = 包含创建时间与解决时间内的工作日总和）
        else:
            seconds_diff = count * 24 * 60 * 60 - (
                    create_t.hour * 60 * 60 + (create_t.minute * 60) + create_t.second) - (temp - reso_t).seconds
    # 秒数转成天 四舍五入取二位小数
    day_diff = Decimal(str(seconds_diff / (24 * 60 * 60))).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
    return day_diff



@router.get("/delay")
async def get_delay(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str='',casedb:Session=Depends(get_case_db)):
    '''
    延期提测情况
    '''
    try:
        sql_param=[]
        if select_type=='version':
            sql_param=list(version_list.split(','))
        else:
            # 初始化搜索条件
            jql_param = 'project={} and type=缺陷'.format(pro_code)
            jql_param += ' and created >={} and created<= {}'.format(start_time[0:10],end_time[0:10])

            jira_clt = jira_com.INKE_JIRA(ticket=token)
            bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

            sql_param=[bug.fields.versions[0].name for bug in bug_list if bug.fields.versions]
            sql_param=list(set(sql_param))

        result=casedb.query(Delay).filter(Delay.version_name.in_(sql_param),Delay.isdelete==0,Delay.pro_code==pro_code).order_by(Delay.user_name.desc()).all()

        return {'code':200,'msg':result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/selfcase")
async def get_selfcase(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str='',sys_db:Session=Depends(get_sso_db),case_db:Session=Depends(get_case_db)):
    try:
        v_list=[]
        if select_type=='version':
            v_list=list(version_list.split(','))
        else:
            # 初始化搜索条件
            jql_param = 'project={} and type=缺陷'.format(pro_code)
            jql_param += ' and created >={} and created<= {}'.format(start_time[0:10], end_time[0:10])

            jira_clt = jira_com.INKE_JIRA(ticket=token)
            bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

            v_list = [bug.fields.versions[0].name for bug in bug_list if bug.fields.versions]
            v_list = list(set(v_list))

        '''版本通过率'''
        #查询所有开发人员
        test_fun={'androiddev':(TestCase.android_name,TestCase.android_result),
                  'iosdev':(TestCase.ios_name,TestCase.ios_result),
                  'managedev':(TestCase.manage_name,TestCase.manage_result),
                  'appletdev':(TestCase.applet_name,TestCase.applet_result),
                  'h5dev':(TestCase.h5_name,TestCase.h5_result),
                  'serverdev':(TestCase.server_name,TestCase.server_result)}

        result_list=[]
        for version in v_list:
            version_detial={'name':version,'total':0,'pass_count':0,'pass_percen':0,'children':[]}
            user_list=sys_db.query(User).filter(User.pro_code_list.like('%{}%'.format(pro_code)),User.pro_fun.like('%dev'),User.isdelete==0).all()
            version_id = case_db.query(Version.id).filter(Version.version_name == version).first()
            if version_id==None:continue
            for user in user_list:
                detail={'name':user.user_name,'total':0,'pass_count':0,'fail_count':0,'pass_percen':0}
                detail['total']=case_db.query(TestCase).filter(test_fun[user.pro_fun][0]==user.user_name,test_fun[user.pro_fun][1].in_(['PASS','FAIL']),TestCase.version_id==version_id.id).count()
                detail['pass_count']=case_db.query(TestCase).filter(test_fun[user.pro_fun][0]==user.user_name,test_fun[user.pro_fun][1]=='PASS',TestCase.version_id==version_id.id).count()
                detail['fail_count']=detail['total']-detail['pass_count']
                version_detial['children'].append(detail)
                version_detial['total']+=detail['total']
                version_detial['pass_count']+=detail['pass_count']
                if detail['total']!=0: detail['pass_percen']=round(detail['pass_count']/detail['total']*100,2)
            if version_detial['total']!=0: version_detial['pass_percen']=round(version_detial['pass_count']/version_detial['total']*100,2)
            result_list.append(version_detial)

        '''个人自测通过率'''
        user_list = sys_db.query(User).filter(User.pro_code_list.like('%{}%'.format(pro_code)),
                                              User.pro_fun.like('%dev'), User.isdelete == 0).all()

        user_return_list=[]
        pass_percen_list=[]
        user_version_id=case_db.query(Version).filter(Version.version_name.in_(v_list)).all()
        user_version_id_list=[item.id for item in user_version_id]
        for user in user_list:
            user_return_list.append(user.user_name)
            total,pass_count,pass_percen=0,0,0
            total = case_db.query(TestCase).filter(test_fun[user.pro_fun][0] == user.user_name,
                                                             test_fun[user.pro_fun][1].in_(['PASS', 'FAIL']),
                                                             TestCase.version_id.in_(user_version_id_list)).count()
            pass_count = case_db.query(TestCase).filter(test_fun[user.pro_fun][0] == user.user_name,
                                                   test_fun[user.pro_fun][1]=='PASS',TestCase.version_id.in_(user_version_id_list)).count()
            if total!=0: pass_percen=round(pass_count/total*100,2)
            pass_percen_list.append(pass_percen)

        return {'code':200,'msg':result_list,'user_list':user_return_list,'pass_percen_list':pass_percen_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}







