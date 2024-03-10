from sqlalchemy import func
from fastapi import APIRouter
from fastapi import Depends
from qa_dal.database import get_case_db,get_jira_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from qa_dal.models import jira_model,User,Delay,TestCase,Version,MySelfRecord,PlanVersion
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from decimal import Decimal
from dateutil.parser import parse

import common.jira_base as jira_com

router = APIRouter(
    prefix="/summary/report",
    tags=["质量月报"]
)


@router.get("/middle/summary")
async def get_summary(start_time:str='',end_time:str='',select_type:str='',token:str='',apidb:Session=Depends(get_sso_db),db:Session=Depends(get_case_db)):
    jql_param = 'type=缺陷 and created >="{} 00:00" and created<= "{} 23:59" and 缺陷归属 = {}'\
        .format(start_time[0:10],end_time[0:10],select_type)

    jira_clt = jira_com.INKE_JIRA(ticket=token)
    bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

    summary_json = {'project_summary': [],'team_summary': [], 'user_summary': []}

    project_count,version_count, team_count, user_count = {}, {}, {},{}


    for bug in bug_list:
        if bug.fields.issuetype.name!='缺陷': continue
        #项目维度
        project_name=bug.fields.project
        if project_name: project_name=project_name.name
        count_summary(bug,project_name,project_count)

        #版本维度
        bug_version = bug.fields.versions  # 影响版本
        version_name = ''
        if bug_version: version_name = bug_version[0].name
        count_summary(bug, version_name, version_count,type='version')

        #团队维度
        count_summary(bug, select_type, team_count)


        '''个人维度数据'''
        assignee = bug.fields.assignee
        assignee_name = ''
        if assignee: assignee_name = assignee.displayName

        count_summary(bug, assignee_name, user_count)

    '''计算百分率'''
    bug_summary('project',apidb,db,start_time,end_time,select_type,project_count, summary_json['project_summary'])  # 计算项目百分率
    version_list=[]
    bug_summary('version',apidb,db,start_time,end_time,select_type,version_count, version_list,type='version')  # 计算版本百分率
    bug_summary('team',apidb,db,start_time,end_time,select_type,team_count, summary_json['team_summary'])  # 计算团队百分率
    bug_summary('user',apidb,db,start_time,end_time,select_type,user_count, summary_json['user_summary'])  # 计算个人百分率

    #嵌套版本到项目里
    for pro in summary_json['project_summary']:
        pro['version_item']=[]
        for version in version_list:
            if pro['name']==version['project']:
                pro['version_item'].append(version)

    return {'code': 200, 'msg': summary_json}





def bug_summary(summary_type,apidb,db,strat_time,end_time,select_type,count_info,summary_name,type='df'):
    '''计算百分率'''

    team_json = {'金融中台': 'financedev', 'H5前端': 'h5dev', '运营后台': 'managedev'}

    for key in count_info:

        #汇总数据
        total = count_info[key]['total']

        detail_info = {'name': key, 'total': total,
                       'unresolved_count': count_info[key]['unresolved_count'],  # 未解决数
                       'resolved_percen': 0,  # 已解决率
                       'bequeath_percen': 0,  # 遗留bug率
                       'online_percen': 0,  # 线上缺陷率
                       'reopen_percen': 0,  # 重开率
                       'highest_percen': 0,  # 高单比例
                       'avg_time_percen': 0,  # 平均解决周期
                       'deylay_percen': 0,  # 日结率
                       'over_delay_percen': 0,
                       'myself_percen':100}  # 超一天缺陷占比


        '''获取自测通过率'''
        if summary_type == 'version':
            version_total = db.query(MySelfRecord).join(PlanVersion,PlanVersion.id == MySelfRecord.plan_version_id).filter(PlanVersion.version_name==key,MySelfRecord.check_result.in_(['PASS', 'FAIL', '未验收']),
                MySelfRecord.check_time.between(strat_time, end_time),MySelfRecord.isdelete == 0).count()
            version_run_total = db.query(MySelfRecord).join(PlanVersion,PlanVersion.id == MySelfRecord.plan_version_id).filter(PlanVersion.version_name == key, MySelfRecord.check_result.in_(['PASS', 'FAIL']),
                MySelfRecord.check_time.between(strat_time, end_time), MySelfRecord.isdelete == 0).count()
            version_pass_total = db.query(MySelfRecord).join(PlanVersion,PlanVersion.id == MySelfRecord.plan_version_id).filter(PlanVersion.version_name == key, MySelfRecord.check_result=='PASS',
                MySelfRecord.check_time.between(strat_time, end_time), MySelfRecord.isdelete == 0).count()
            if version_total>0:
                if version_run_total > 0:
                    detail_info['myself_percen']=round(version_pass_total/version_run_total*100,2)
                else:
                    detail_info['myself_percen'] = 0

        elif summary_type =='team':
            user_list=apidb.query(User.user_name).filter(User.pro_fun==team_json[select_type],User.isdelete==0).all()
            u_list=[user.user_name for user in user_list]
            if len(u_list)>0:
                team_total = db.query(MySelfRecord).filter(MySelfRecord.name.in_(u_list),MySelfRecord.check_result.in_(['PASS', 'FAIL', '未验收']),MySelfRecord.check_time.between(strat_time, end_time), MySelfRecord.isdelete == 0).count()
                team_run_total = db.query(MySelfRecord).filter(MySelfRecord.name.in_(u_list),MySelfRecord.check_result.in_(['PASS', 'FAIL']),MySelfRecord.check_time.between(strat_time, end_time),MySelfRecord.isdelete == 0).count()
                team_pass_total = db.query(MySelfRecord).filter(MySelfRecord.name.in_(u_list),MySelfRecord.check_result == 'PASS',MySelfRecord.check_time.between(strat_time, end_time), MySelfRecord.isdelete == 0).count()
                if team_total > 0:
                    if team_run_total>0:
                        detail_info['myself_percen'] = round(team_pass_total / team_run_total * 100, 2)
                    else:
                        detail_info['myself_percen'] =0

        elif summary_type == 'user':
            user_total = db.query(MySelfRecord).filter(MySelfRecord.name==key,MySelfRecord.check_result.in_(['PASS', 'FAIL', '未验收']),MySelfRecord.check_time.between(strat_time, end_time), MySelfRecord.isdelete == 0).count()
            user_run_total = db.query(MySelfRecord).filter(MySelfRecord.name == key,MySelfRecord.check_result.in_(['PASS', 'FAIL']),MySelfRecord.check_time.between(strat_time, end_time),MySelfRecord.isdelete == 0).count()
            user_pass_total = db.query(MySelfRecord).filter(MySelfRecord.name==key,MySelfRecord.check_result == 'PASS',MySelfRecord.check_time.between(strat_time, end_time),MySelfRecord.isdelete == 0).count()
            if user_total > 0:
                if user_run_total>0:
                    detail_info['myself_percen'] = round(user_pass_total / user_total * 100, 2)
                else:
                    detail_info['myself_percen'] =0

        if total>0:detail_info['resolved_percen']=round(count_info[key]['resolved_count'] / total * 100, 2)
        if total > 0: detail_info['bequeath_percen'] = round(count_info[key]['unresolved_count'] / total * 100, 2)
        if total > 0: detail_info['online_percen'] = round(count_info[key]['online_count'] / total * 100, 2)
        if total > 0: detail_info['reopen_percen'] = round(count_info[key]['reopen_count'] / total * 100, 2)
        if total > 0: detail_info['highest_percen'] = round(count_info[key]['highest_count'] / total * 100, 2)
        if count_info[key]['avg_time_total'] > 0: detail_info['avg_time_percen'] =round(count_info[key]['avg_time'] / count_info[key]['avg_time_total'],2)

        # 计算日结率
        total_other = 0
        total_dalay_parcen = 0

        # 计算每天的日结率
        date_item = count_info[key]['delay_json']
        date_count = len(date_item)
        for item in date_item:
            if date_item[item]['total']>0:total_other += date_item[item]['other_count']
            if date_item[item]['total']>0:total_dalay_parcen += round(date_item[item]['dalay_count'] / date_item[item]['total'] * 100, 2)

        if date_count: detail_info['deylay_percen'] = round(total_dalay_parcen / date_count, 2)
        if total>0: detail_info['over_delay_percen'] = round(total_other/total*100,2)

        if type != 'df': detail_info['project']=count_info[key]['project']
        summary_name.append(detail_info)



def count_summary(bug,name,count_info,type='df'):
    '''
    各维度数量统计
    '''


    project_name = ''
    if bug.fields.project and type!='df': project_name = bug.fields.project.name
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

        if resolutiondate:

            # 平均解决周期
            count_info[name]['avg_time'] += get_time(created, str(
                datetime.strptime(resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800')))
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
        if bug.fields.project and type!='df': count_info[name]['project']=project_name




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






@router.get("/middle/delay2")
async def get_delay(start_time:str='',end_time:str='',select_type:str='',token:str='',casedb:Session=Depends(get_case_db)):
    '''
    延期提测情况
    '''
    try:
        # 初始化搜索条件
        param = {'金融中台': '金融,金融中台', 'H5前端': 'H5,h5,H5端', '运营后台': '后台,运营后台,管理后台'}
        jql_param = '(type=缺陷 and created >={} and created<= {} and component in ({})) or (type=缺陷 and created >={} and created<= {} and 缺陷归属 = {})' \
            .format(start_time[0:10], end_time[0:10], param[select_type], start_time[0:10], end_time[0:10], select_type)

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        sql_param = [bug.fields.versions[0].name for bug in bug_list if bug.fields.versions]
        sql_param = list(set(sql_param))
        user_list = [bug.fields.assignee.displayName for bug in bug_list if bug.fields.assignee]
        user_list = list(set(user_list))

        result=casedb.query(Delay).filter(Delay.version_name.in_(sql_param),Delay.user_name.in_(user_list),Delay.isdelete==0).order_by(Delay.user_name.desc()).all()

        return {'code':200,'msg':result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}








