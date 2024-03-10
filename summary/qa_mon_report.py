from sqlalchemy import func
from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import testcase_schemas
from qa_dal.database import get_case_db,get_jira_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from sqlalchemy import or_,and_
from qa_dal.models import jira_model,User,Delay,TestCase,Version
from qa_dal import qa_uitls
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from decimal import Decimal
from dateutil.parser import parse

import common.jira_base as jira_com

router = APIRouter(
    prefix="/summary/report",
    tags=["质量月报"]
)


@router.get("/total")
async def get_total_list(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str='STXgLiFLQTyyFvpxvkUkvArEMcnayRwfzfA'):
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        #初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type=='version': jql_param+=' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type=='time': jql_param+=' and created >={} and created<= {}'.format(start_time[0:10],end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param,maxResults=2000)


        #获取jira列表
        return_item={'bug_detail':{},'bug_detail_user':[],'pro_fun_name':[],'pro_fun_value':[],
                     'bug_reopen':[],'bug_reopen_user':[],
                     'bug_avg_time':[],'bug_avg_time_user':[],
                     'bug_online':[],'bug_online_user':[],
                     'bug_dalay':[],'bug_dalay_user':[]}
        assignee_detail = {}    #bug情况-个人明细

        version_reopen_json = {}    #BUG重开率
        assignee_reopen = {}  # BUG重开率-个人明细

        version_avg_time = {}   #bug解决周期
        user_avg_time = {}  #bug解决周期

        version_online = {}    #线上版本维度
        online_user={}  #线上版本个人维度

        version_dalay = {}  #日结率版本维度

        daly_user = {}  #日结率个人维度

        for bug in bug_list:

            '''Bug情况'''
            bug_detail(return_item,bug,assignee_detail)

            '''Bug重开率'''
            bug_reopen(bug,version_reopen_json,assignee_reopen)

            '''Bug解决周期'''
            bug_avg_time(bug,version_avg_time,user_avg_time)

            '''Bug日结率'''
            bug_daylay(bug,version_dalay,daly_user)

            '''Bug线上质量'''
            bug_online(bug,version_online,online_user)


        #Bug情况--个人维度
        for key,value in return_item['bug_detail'].items():
            return_item['pro_fun_name'].append(key)
            return_item['pro_fun_value'].append(value)

        return_item['bug_detail_user']=[{'name':key,'Highest':assignee_detail[key]['Highest'],
                                         'High':assignee_detail[key]['High'],'Medium':assignee_detail[key]['Medium'],
                                         'Low':assignee_detail[key]['Low'],'Lowest':assignee_detail[key]['Lowest'],
                                         'total':assignee_detail[key]['total']} for key in assignee_detail]

        return_item['bug_detail_user'] = list(reversed(sorted(return_item['bug_detail_user'], key=lambda x: x["total"])))   #重新排序

        '''重开率'''
        #BUG重开率(版本)
        return_item['bug_reopen']=[{'version_name':key,'reopen_count':version_reopen_json[key]['reopen_count'],'total':version_reopen_json[key]['total'],
                                    'reopen_percen':round(version_reopen_json[key]['reopen_count']/version_reopen_json[key]['total']*100,2)} for key in version_reopen_json]
        return_item['bug_reopen'] =list(reversed(sorted(return_item['bug_reopen'], key=lambda x: x["reopen_percen"])))   #重新排序

        #bug重开率（个人）
        return_item['bug_reopen_user'] = [{'name': key, 'reopen_count': assignee_reopen[key]['reopen_count'],
                                      'total': assignee_reopen[key]['total'],
                                      'reopen_percen': round(assignee_reopen[key]['reopen_count'] / assignee_reopen[key]['total'] * 100, 2)} for key in assignee_reopen]
        return_item['bug_reopen_user'] = list(reversed(sorted(return_item['bug_reopen_user'], key=lambda x: x["reopen_percen"])))  # 重新排序


        '''bug平均解决周期'''
        #版本维度
        return_item['bug_avg_time']=[{'version_name':avg,'bug_count':version_avg_time[avg]['total'],'avg_time':round(version_avg_time[avg]['avg_time']/version_avg_time[avg]['total'],2)} for avg in version_avg_time]
        return_item['bug_avg_time'] = list(reversed(sorted(return_item['bug_avg_time'], key=lambda x: x["avg_time"])))  # 重新排序

        #个人维度
        return_item['bug_avg_time_user'] = [{'name': avg, 'bug_count': user_avg_time[avg]['total'], 'avg_time': round(user_avg_time[avg]['avg_time'] / user_avg_time[avg]['total'], 2)} for avg in user_avg_time]
        return_item['bug_avg_time_user'] = list(reversed(sorted(return_item['bug_avg_time_user'], key=lambda x: x["avg_time"])))  # 重新排序


        '''线上问题'''
        return_item['bug_online'] = [{'version_name': key,'online_count':version_online[key]['online_count'],'total': version_online[key]['total'], 'online_percen': round(version_online[key]['online_count'] / version_online[key]['total']*100, 2)} for key in version_online]
        return_item['bug_online'] = list(reversed(sorted(return_item['bug_online'], key=lambda x: x["online_percen"])))  # 重新排序

        return_item['bug_online_user'] = [{'name': key, 'online_count': online_user[key]['online_count'],'total': online_user[key]['total'], 'online_percen': round(online_user[key]['online_count'] / online_user[key]['total'] * 100, 2)} for key in online_user]
        return_item['bug_online_user'] = list(reversed(sorted(return_item['bug_online_user'], key=lambda x: x["online_percen"])))  # 重新排序

        '''日结率'''
        #版本维度
        for key in version_dalay:
            total_other_percen=0
            total_dalay_parcen=0
            date_count=0

            #计算每天的日结率
            date_item=version_dalay[key]['dalay_detail']
            for item in date_item:
                total_other_percen+=round(date_item[item]['other_count']/date_item[item]['total']*100,2)
                total_dalay_parcen+=round(date_item[item]['dalay_count']/date_item[item]['total']*100,2)
                date_count+=1
            return_item['bug_dalay'].append({'name':key,'total':version_dalay[key]['total'],
                                             'other_percen':round(total_other_percen/date_count,2),
                                             'avg_percen':round(total_dalay_parcen/date_count,2)})

        return_item['bug_dalay'] = list(reversed(sorted(return_item['bug_dalay'], key=lambda x: x["avg_percen"])))  # 重新排序

        # 个人维度
        for key in daly_user:
            total_other_percen = 0
            total_dalay_parcen = 0
            date_count = 0

            # 计算每天的日结率
            date_item = daly_user[key]['dalay_detail']
            for item in date_item:
                total_other_percen += round(date_item[item]['other_count'] / date_item[item]['total'] * 100, 2)
                total_dalay_parcen += round(date_item[item]['dalay_count'] / date_item[item]['total'] * 100, 2)
                date_count += 1
            return_item['bug_dalay_user'].append({'name': key, 'total': daly_user[key]['total'],
                                             'other_percen': round(total_other_percen / date_count, 2),
                                             'avg_percen': round(total_dalay_parcen / date_count, 2)})

        return_item['bug_dalay_user'] = list(reversed(sorted(return_item['bug_dalay_user'], key=lambda x: x["avg_percen"])))  # 重新排序

        return {'code':200,'msg':return_item}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def bug_daylay(bug,version_dalay,daly_user):
    '''
    bug日结率
    '''
    bug_version = bug.fields.versions
    resolved = bug.fields.resolutiondate
    created = str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))
    if bug_version:
        if version_dalay.get(bug_version[0].name) != None:
            if resolved:
                resolved = str(datetime.strptime(resolved, '%Y-%m-%dT%H:%M:%S.000+0800'))
                dalay_detail = version_dalay[bug_version[0].name]['dalay_detail']

                # 判断日期是否存在
                if dalay_detail.get(created[0:10]) == None:
                    dalay_detail[created[0:10]] = {'other_count': 0, 'dalay_count': 0, 'total': 1}
                else:
                    dalay_detail[created[0:10]]['total'] += 1

                other_count = dalay_detail[created[0:10]]['other_count']
                dalay_count = dalay_detail[created[0:10]]['dalay_count']

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

                dalay_detail[created[0:10]]['other_count'] = other_count
                dalay_detail[created[0:10]]['dalay_count'] = dalay_count

            version_dalay[bug_version[0].name]['total'] += 1

        elif version_dalay.get(bug_version[0].name) == None:
            version_dalay[bug_version[0].name] = {'total': 1, 'dalay_detail': {}}
            other_count = 0
            dalay_count = 0
            if resolved:
                resolved = str(datetime.strptime(resolved, '%Y-%m-%dT%H:%M:%S.000+0800'))

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

            version_dalay[bug_version[0].name]['dalay_detail'][created[0:10]] = {'other_count': other_count,
                                                                                 'dalay_count': dalay_count,
                                                                                 'total': 1}

    assignee = bug.fields.assignee
    resolved_user = bug.fields.resolutiondate
    created_user = str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))
    if assignee:
        if daly_user.get(assignee.displayName) != None:
            daly_user[assignee.displayName]['total'] += 1
            if resolved_user:
                resolved_user = str(datetime.strptime(resolved_user, '%Y-%m-%dT%H:%M:%S.000+0800'))
                dalay_detail = daly_user[assignee.displayName]['dalay_detail']

                # 判断日期是否存在
                if dalay_detail.get(created_user[0:10]) == None:
                    dalay_detail[created_user[0:10]] = {'other_count': 0, 'dalay_count': 0, 'total': 1}
                else:
                    dalay_detail[created_user[0:10]]['total'] += 1

                other_count = dalay_detail[created_user[0:10]]['other_count']
                dalay_count = dalay_detail[created_user[0:10]]['dalay_count']

                if created_user[0:10] == resolved_user[0:10]:  # 获取当天的
                    dalay_count += 1
                elif created_user[0:10] != resolved_user[0:10]:  # 判断超过当天的
                    date_list = getEveryDay(created_user[0:10], resolved_user[0:10])

                    # 去除节假日
                    for date in date_list:
                        if is_holiday(datetime.strptime(date, "%Y-%m-%d")):
                            date_list.remove(date)

                    # 只有一天的跨度
                    if len(date_list) <= 2:
                        create_time = parse(created_user)
                        resolved_time = parse(resolved_user)

                        # 判断是否小于24小时
                        if ((resolved_time - create_time).total_seconds()) / 3600 < 24:
                            dalay_count += 1
                        else:
                            other_count += 1

                    # 计划跨度是否节假日
                    elif len(date_list) > 2:
                        other_count += 1

                dalay_detail[created_user[0:10]]['other_count'] = other_count
                dalay_detail[created_user[0:10]]['dalay_count'] = dalay_count


        elif daly_user.get(assignee.displayName) == None:
            daly_user[assignee.displayName] = {'total': 1, 'dalay_detail': {}}
            other_count = 0
            dalay_count = 0

            if resolved_user:
                resolved_user = str(datetime.strptime(resolved_user, '%Y-%m-%dT%H:%M:%S.000+0800'))



                if created_user[0:10] == resolved_user[0:10]:  # 获取当天的
                    dalay_count = 1
                elif created_user[0:10] != resolved_user[0:10]:  # 判断超过当天的
                    date_list = getEveryDay(created_user[0:10], resolved_user[0:10])

                    # 去除节假日
                    for date in date_list:
                        if is_holiday(datetime.strptime(date, "%Y-%m-%d")):
                            date_list.remove(date)

                    # 只有一天的跨度
                    if len(date_list) <= 2:
                        create_time = parse(created_user)
                        resolved_time = parse(resolved_user)

                        # 判断是否小于24小时
                        if ((resolved_time - create_time).total_seconds()) / 3600 < 24:
                            dalay_count = 1
                        else:
                            other_count = 1

                    # 计划跨度是否节假日
                    elif len(date_list) > 2:
                        other_count = 1

            daly_user[assignee.displayName]['dalay_detail'][created_user[0:10]] = {'other_count': other_count,
                                                                                   'dalay_count': dalay_count, 'total': 1}


def bug_online(bug,version_online,online_user):
    '''
    线上问题
    '''
    bug_version = bug.fields.versions
    online = bug.fields.customfield_10102
    if bug_version:
        if version_online.get(bug_version[0].name) != None:
            if online:
                if online.value == '线上问题': version_online[bug_version[0].name]['online_count'] += 1
            version_online[bug_version[0].name]['total'] += 1
        elif version_online.get(bug_version[0].name) == None:
            version_online[bug_version[0].name] = {'online_count': 0, 'total': 1}
            if online:
                if online.value == '线上问题': version_online[bug_version[0].name]['online_count'] = 1

    assignee = bug.fields.assignee
    if assignee:
        if online_user.get(assignee.displayName) != None:
            if online:
                if online.value == '线上问题': online_user[assignee.displayName]['online_count'] += 1
            online_user[assignee.displayName]['total'] += 1
        elif online_user.get(assignee.displayName) == None:
            online_user[assignee.displayName] = {'online_count': 0, 'total': 1}
            if online:
                if online.value == '线上问题': online_user[assignee.displayName]['online_count'] = 1


def bug_avg_time(bug,version_avg_time,user_avg_time):
    '''
    平均解决周期
    '''
    bug_version = bug.fields.versions
    resolved = bug.fields.resolutiondate
    created = str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))
    if bug_version:
        if version_avg_time.get(bug_version[0].name) != None:
            if resolved:
                resolved = str(datetime.strptime(resolved, '%Y-%m-%dT%H:%M:%S.000+0800'))
                version_avg_time[bug_version[0].name]['avg_time'] += get_time(created, resolved)
            version_avg_time[bug_version[0].name]['total'] += 1
        elif version_avg_time.get(bug_version[0].name) == None:
            version_avg_time[bug_version[0].name] = {'total': 1, 'avg_time':0}
            if resolved:
                resolved = str(datetime.strptime(resolved, '%Y-%m-%dT%H:%M:%S.000+0800'))
                version_avg_time[bug_version[0].name]['avg_time']=get_time(created, resolved)


    assignee = bug.fields.assignee
    user_resolved = bug.fields.resolutiondate
    if assignee:
        if user_avg_time.get(assignee.displayName) != None:
            if user_resolved:
                user_resolved = str(datetime.strptime(user_resolved, '%Y-%m-%dT%H:%M:%S.000+0800'))
                user_avg_time[assignee.displayName]['avg_time'] += get_time(created, user_resolved)
            user_avg_time[assignee.displayName]['total'] += 1
        elif user_avg_time.get(assignee.displayName) == None:
            user_avg_time[assignee.displayName] = {'total': 1, 'avg_time': 0}
            if user_resolved:
                user_resolved = str(datetime.strptime(user_resolved, '%Y-%m-%dT%H:%M:%S.000+0800'))
                user_avg_time[assignee.displayName]['avg_time']=get_time(created, user_resolved)




def bug_reopen(bug,version_reopen_json,assignee_reopen):
    '''
    BUG重开率
    '''
    # 版本维度
    bug_version = bug.fields.versions
    version_reopen=bug.fields.customfield_10103
    if bug_version:
        if version_reopen_json.get(bug_version[0].name) != None:
            if version_reopen:
                if version_reopen.value == 'yes':version_reopen_json[bug_version[0].name]['reopen_count'] += 1
            version_reopen_json[bug_version[0].name]['total'] += 1
        elif version_reopen_json.get(bug_version[0].name) == None:
            version_reopen_json[bug_version[0].name] = {'reopen_count': 0, 'total': 1}
            if version_reopen:
                if version_reopen.value == 'yes':version_reopen_json[bug_version[0].name]['reopen_count'] = 1

    # 个人维度
    assignee = bug.fields.assignee
    reopen = bug.fields.customfield_10103

    # 判断经办人和用例等级赋值
    if assignee:
        if assignee.displayName in assignee_reopen.keys():
            if reopen:
                if reopen.value == 'yes': assignee_reopen[assignee.displayName]['reopen_count'] += 1
            assignee_reopen[assignee.displayName]['total'] += 1
        elif assignee.displayName not in assignee_reopen.keys():
            assignee_reopen[assignee.displayName] = {'reopen_count': 0, 'total': 1}

            if reopen:
                if reopen.value == 'yes': assignee_reopen[assignee.displayName]['reopen_count'] = 1



def bug_detail(return_item,bug,assignee_detail):
    '''
    Bug情况
    '''
    # 各端维度
    belong = bug.fields.customfield_11302
    if belong:
        if return_item['bug_detail'].get(belong.value)!=None:
            return_item['bug_detail'][belong.value] += 1
        elif return_item['bug_detail'].get(belong.value)==None:
            return_item['bug_detail'][belong.value] = 1
    else:
        # 清洗老数据
        df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                   "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                   "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                   "安卓": "Android", "Unity3D": "Unity3D",
                   "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序"}

        components = bug.fields.components
        if components != []:
            df_name = df_json.get(components[0].name)
            if df_name != None and return_item['bug_detail'].get(df_name)!=None:
                return_item['bug_detail'][df_name] += 1
            elif df_name != None and return_item['bug_detail'].get(df_name)==None:
                return_item['bug_detail'][df_name] = 1

    # 个人维度
    bug_level_list = {'Highest': 1, 'High': 1, 'Medium': 1, 'Low': 1, 'Lowest': 1}
    assignee = bug.fields.assignee
    priority = bug.fields.priority

    # 判断经办人和用例等级赋值
    if assignee and priority:
        if assignee.displayName in assignee_detail.keys():
            assignee_detail[assignee.displayName]['total'] += 1
            assignee_detail[assignee.displayName][priority.name] += bug_level_list[priority.name]
        elif assignee.displayName not in assignee_detail.keys():
            assignee_detail[assignee.displayName] = {'Highest': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Lowest': 0,
                                                     'total': 1}
            assignee_detail[assignee.displayName][priority.name] += bug_level_list[priority.name]



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


''''旧接口'''

# @router.get("/reopen")
# async def get_open(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
#     '''
#     重开率统计
#     '''
#     try:
#         pro=jira_model(pro_code)
#         version_result=[]
#         v_list = []
#
#         reopen_sql_param=[]
#         if select_type == 'version':
#             v_list=list(version_list.split(','))
#             reopen_sql_param=[pro.affectedVersion.in_(v_list)]
#         else:
#             reopen_sql_param=[pro.created.between(start_time,end_time)]
#             group_version = db.query(pro.affectedVersion).filter(*reopen_sql_param).group_by(pro.affectedVersion).all()
#             v_list=[item.affectedVersion for item in group_version]
#
#
#         '''按版本'''
#         # 打开的数量
#         reopen_list = db.query(pro.affectedVersion, func.count(pro.affectedVersion).label('total')) \
#             .filter(*reopen_sql_param).filter(pro.reopen != 0).group_by(pro.affectedVersion).all()
#         reopen_json = {item.affectedVersion: item.total for item in reopen_list}
#
#         # 总数列表
#         total_list = db.query(pro.affectedVersion, func.count(pro.affectedVersion).label('total')) \
#             .filter(*reopen_sql_param).group_by(pro.affectedVersion).all()
#         total_json = {item.affectedVersion: item.total for item in total_list}
#
#         for version in v_list:
#             if version=='': continue
#             version_detail = {'version_name':'','reopen_count':0,'total':0,'reopen_percen':0.0}
#             version_detail['version_name'] = version
#             version_detail['reopen_count'] = [0, reopen_json.get(version)][reopen_json.get(version) != None]
#             version_detail['total'] = [0, total_json.get(version)][total_json.get(version) != None]
#             if version_detail['total'] != 0: version_detail['reopen_percen'] = round(version_detail['reopen_count'] / version_detail['total'] * 100,2)
#             version_result.append(version_detail)
#
#
#         '''按人维度'''
#         reopen_people=db.query(pro.assignee,func.count(pro.assignee).label('total')).filter(*reopen_sql_param).group_by(pro.assignee).filter(pro.reopen != 0).all()
#         people_json = {item.assignee: item.total for item in reopen_people}
#
#         #所有缺陷
#         people_total_list = db.query(pro.assignee, func.count(pro.assignee).label('total')).filter(*reopen_sql_param).group_by(pro.assignee).all()
#         people_total_json = {item.assignee: item.total for item in people_total_list}
#
#         #所有人员
#         people_list=db.query(pro.assignee).filter(*reopen_sql_param).group_by(pro.assignee).all()
#
#         people_result = []
#         for people in people_list:
#             people_detail={'name':'','reopen_count':0,'total':0,'reopen_percen':0.0}
#             people_detail['name']=people.assignee
#             people_detail['reopen_count']=[0, people_json.get(people.assignee)][people_json.get(people.assignee) != None]
#             people_detail['total']=[0, people_total_json.get(people.assignee)][people_total_json.get(people.assignee) != None]
#             if people_detail['total'] != 0: people_detail['reopen_percen'] = round(people_detail['reopen_count'] / people_detail['total'] * 100,2)
#             people_result.append(people_detail)
#         people_result=sorted(people_result, key = lambda x: x["reopen_percen"])
#
#         return {'code': 200, 'msg':'数据已加载！','version_list':version_result,'people_list':list(reversed(people_result))}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



# @router.get("/bug_avg_time")
# async def bug_avg_time(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
#     '''
#     平均解决周期
#     '''
#     try:
#         pro=jira_model(pro_code)
#
#         version_result=[]
#         avg_sql_param=[]
#         v_list=[]
#         if select_type == 'version':
#             v_list=list(version_list.split(','))
#             avg_sql_param=[pro.affectedVersion.in_(v_list),pro.resolved!='']
#             version_list=db.query(pro.affectedVersion,func.count(pro.affectedVersion).label('total'))\
#                 .filter(*avg_sql_param).group_by(pro.affectedVersion).all()
#             version_result ={item.affectedVersion:item.total for item in version_list}
#         else:
#             avg_sql_param=[pro.created.between(start_time,end_time),pro.resolved!='']
#             version_list = db.query(pro.affectedVersion,func.count(pro.affectedVersion).label('total'))\
#                 .filter(*avg_sql_param).group_by(pro.affectedVersion).all()
#             v_list=[item.affectedVersion for item in version_list]
#             version_result = {item.affectedVersion: item.total for item in version_list}
#
#
#         '''按版本'''
#         return_version=[]
#         all_bug_list=db.query(pro).filter(*avg_sql_param).all()
#         for version in v_list:
#             version_detail = {'version_name': '', 'bug_count': 0, 'avg_time': 0.00}
#             version_detail['version_name']=version
#             version_detail['bug_count']=[0, version_result.get(version)][version_result.get(version) != None]
#
#             #计算平均时间
#             if version_detail['bug_count']!=0:
#                 avg_count = 0
#                 avg_total_time = 0
#                 for bug in all_bug_list:
#                     if bug.affectedVersion==version:
#                         avg_count+=1
#                         avg_total_time+=get_time(str(bug.created),str(bug.resolved))
#                 version_detail['avg_time']=round(avg_total_time/avg_count,2)
#             return_version.append(version_detail)
#
#
#
#         '''按人维度'''
#         avg_people=db.query(pro.assignee,func.count(pro.assignee).label('total')).filter(*avg_sql_param).group_by(pro.assignee).all()
#         people_total=db.query(pro).filter(*avg_sql_param).all()
#         people_result = []
#         for people in avg_people:
#             people_detail={'name':'','bug_count':0,'avg_time':0}
#             people_detail['name']=people.assignee
#             people_detail['bug_count']=people.total
#
#             #计算平均周期
#             people_time_count=0
#             people_time=0
#             for pr in people_total:
#                 if pr.assignee == people.assignee:
#                     people_time_count+=1
#                     people_time+=get_time(str(pr.created),str(pr.resolved))
#
#             people_detail['avg_time']=round(people_time/people_time_count,2)
#             people_result.append(people_detail)
#
#         people_result=sorted(people_result, key = lambda x: x["avg_time"])
#
#         return {'code': 200, 'msg':'数据已加载！','version_list':return_version,'people_list':list(reversed(people_result))}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




# @router.get("/bug_detail")
# async def bug_detail(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
#     try:
#         pro = jira_model(pro_code)
#         version_result = []
#
#         sql_param = []
#         if select_type == 'version':
#             sql_param = [pro.affectedVersion.in_(list(version_list.split(',')))]
#         else:
#             sql_param = [pro.created.between(start_time, end_time)]
#
#         #按端划分
#         pro_fun_list = db.query(pro.belong, func.count(pro.belong).label('total')).filter(
#             *sql_param).group_by(pro.belong).all()
#         pro_fun_json = {item.belong:item.total for item in pro_fun_list if item.belong!=None}
#
#
#         #按个人维度
#         user_list=db.query(pro).filter(*sql_param).group_by(pro.assignee).all()
#         bug_list=db.query(pro).filter(*sql_param).all()
#
#         bug_return=[]
#         for user in user_list:
#             detail={'name':user.assignee,'High':0,'Medium':0,'Low':0,'total':0}
#             for bug in bug_list:
#                 if user.assignee != bug.assignee: continue
#                 if user.priority =='High': detail['High']+=1
#                 if user.priority == 'Medium': detail['Medium'] += 1
#                 if user.priority == 'Low': detail['Low'] += 1
#                 detail['total']+=1
#             bug_return.append(detail)
#         bug_return = sorted(bug_return, key=lambda x: x["total"])
#
#         return {'code':200,'pro_fun':pro_fun_json,'bug_list':list(reversed(bug_return))}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





# @router.get("/online")
# async def get_online(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
#     '''
#     线上bug率
#     '''
#     try:
#         pro=jira_model(pro_code)
#         version_result=[]
#         v_list = []
#
#         online_sql_param=[]
#         if select_type == 'version':
#             v_list=list(version_list.split(','))
#             online_sql_param=[pro.affectedVersion.in_(v_list)]
#         else:
#
#             online_sql_param=[pro.created.between(start_time,end_time)]
#             group_version = db.query(pro.affectedVersion).filter(*online_sql_param).group_by(pro.affectedVersion).all()
#             v_list=[item.affectedVersion for item in group_version]
#
#
#         '''按版本'''
#         # 打开的数量
#         online_list = db.query(pro.affectedVersion, func.count(pro.affectedVersion).label('total')) \
#             .filter(*online_sql_param).filter(pro.isonline != 0).group_by(pro.affectedVersion).all()
#         online_json = {item.affectedVersion: item.total for item in online_list}
#
#         # 总数列表
#         total_list = db.query(pro.affectedVersion, func.count(pro.affectedVersion).label('total')) \
#             .filter(*online_sql_param).group_by(pro.affectedVersion).all()
#         total_json = {item.affectedVersion: item.total for item in total_list}
#
#         for version in v_list:
#             if version=='': continue
#             version_detail = {'version_name':'','online_count':0,'total':0,'online_percen':0.0}
#             version_detail['version_name'] = version
#             version_detail['online_count'] = [0, online_json.get(version)][online_json.get(version) != None]
#             version_detail['total'] = [0, total_json.get(version)][total_json.get(version) != None]
#             if version_detail['total'] != 0: version_detail['online_percen'] = round(version_detail['online_count'] / version_detail['total'] * 100,2)
#             version_result.append(version_detail)
#
#
#         '''按人维度'''
#         online_people=db.query(pro.assignee,func.count(pro.assignee).label('total')).filter(*online_sql_param).group_by(pro.assignee).filter(pro.isonline != 0).all()
#         people_json = {item.assignee: item.total for item in online_people}
#
#         #所有缺陷
#         people_total_list = db.query(pro.assignee, func.count(pro.assignee).label('total')).filter(*online_sql_param).group_by(pro.assignee).all()
#         people_total_json = {item.assignee: item.total for item in people_total_list}
#
#         #所有人员
#         people_list=db.query(pro.assignee).filter(*online_sql_param).group_by(pro.assignee).all()
#
#         people_result = []
#         for people in people_list:
#             people_detail={'name':'','online_count':0,'total':0,'online_percen':0.0}
#             people_detail['name']=people.assignee
#             people_detail['online_count']=[0, people_json.get(people.assignee)][people_json.get(people.assignee) != None]
#             people_detail['total']=[0, people_total_json.get(people.assignee)][people_total_json.get(people.assignee) != None]
#             if people_detail['total'] != 0: people_detail['online_percen'] = round(people_detail['online_count'] / people_detail['total'] * 100,2)
#             people_result.append(people_detail)
#         people_result=sorted(people_result, key = lambda x: x["online_percen"])
#
#         return {'code': 200, 'msg':'数据已加载！','version_list':version_result,'people_list':list(reversed(people_result))}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



# @router.get("/delay2")
# async def get_delay(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db),casedb:Session=Depends(get_case_db)):
#     '''
#     延期提测情况
#     '''
#     try:
#         pro = jira_model(pro_code)
#         version_result = []
#
#         sql_param = []
#         #后去搜索条件
#         if select_type == 'version':
#             sql_param = list(version_list.split(','))
#         else:
#             group_version = db.query(pro.affectedVersion).filter(pro.created.between(start_time, end_time)).group_by(
#                 pro.affectedVersion).all()
#             sql_param = [item.affectedVersion for item in group_version]
#
#         result=casedb.query(Delay).filter(Delay.version_name.in_(sql_param),Delay.isdelete==0,Delay.pro_code==pro_code).order_by(Delay.user_name.desc()).all()
#
#         return {'code':200,'msg':result}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



# @router.get("/selfcase2")
# async def get_selfcase(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db),sys_db:Session=Depends(get_api_db),case_db:Session=Depends(get_case_db)):
#     try:
#         pro = jira_model(pro_code)
#         version_result = []
#         v_list = []
#
#         sql_param = []
#         if select_type == 'version':
#             v_list = list(version_list.split(','))
#         else:
#             sql_param = [pro.created.between(start_time, end_time)]
#             group_version = db.query(pro.affectedVersion).filter(*sql_param).group_by(pro.affectedVersion).all()
#             v_list = [item.affectedVersion for item in group_version]
#
#         '''版本通过率'''
#         #查询所有开发人员
#         test_fun={'androiddev':(TestCase.android_name,TestCase.android_result),
#                   'iosdev':(TestCase.ios_name,TestCase.ios_result),
#                   'managedev':(TestCase.manage_name,TestCase.manage_result),
#                   'appletdev':(TestCase.applet_name,TestCase.applet_result),
#                   'h5dev':(TestCase.h5_name,TestCase.h5_result),
#                   'serverdev':(TestCase.server_name,TestCase.server_result)}
#
#         result_list=[]
#         for version in v_list:
#             version_detial={'name':version,'total':0,'pass_count':0,'pass_percen':0,'children':[]}
#             user_list=sys_db.query(User).filter(User.pro_code_list.like('%{}%'.format(pro_code)),User.pro_fun.like('%dev'),User.isdelete==0).all()
#             version_id = case_db.query(Version.id).filter(Version.version_name == version).first()
#             if version_id==None:continue
#             for user in user_list:
#                 detail={'name':user.user_name,'total':0,'pass_count':0,'fail_count':0,'pass_percen':0}
#                 detail['total']=case_db.query(TestCase).filter(test_fun[user.pro_fun][0]==user.user_name,test_fun[user.pro_fun][1].in_(['PASS','FAIL']),TestCase.version_id==version_id.id).count()
#                 detail['pass_count']=case_db.query(TestCase).filter(test_fun[user.pro_fun][0]==user.user_name,test_fun[user.pro_fun][1]=='PASS',TestCase.version_id==version_id.id).count()
#                 detail['fail_count']=detail['total']-detail['pass_count']
#                 version_detial['children'].append(detail)
#                 version_detial['total']+=detail['total']
#                 version_detial['pass_count']+=detail['pass_count']
#                 if detail['total']!=0: detail['pass_percen']=round(detail['pass_count']/detail['total']*100,2)
#             if version_detial['total']!=0: version_detial['pass_percen']=round(version_detial['pass_count']/version_detial['total']*100,2)
#             result_list.append(version_detial)
#
#         '''个人自测通过率'''
#         user_list = sys_db.query(User).filter(User.pro_code_list.like('%{}%'.format(pro_code)),
#                                               User.pro_fun.like('%dev'), User.isdelete == 0).all()
#
#         user_return_list=[]
#         pass_percen_list=[]
#         user_version_id=case_db.query(Version).filter(Version.version_name.in_(v_list)).all()
#         user_version_id_list=[item.id for item in user_version_id]
#         for user in user_list:
#             user_return_list.append(user.user_name)
#             total,pass_count,pass_percen=0,0,0
#             total = case_db.query(TestCase).filter(test_fun[user.pro_fun][0] == user.user_name,
#                                                              test_fun[user.pro_fun][1].in_(['PASS', 'FAIL']),
#                                                              TestCase.version_id.in_(user_version_id_list)).count()
#             pass_count = case_db.query(TestCase).filter(test_fun[user.pro_fun][0] == user.user_name,
#                                                    test_fun[user.pro_fun][1]=='PASS',TestCase.version_id.in_(user_version_id_list)).count()
#             if total!=0: pass_percen=round(pass_count/total*100,2)
#             pass_percen_list.append(pass_percen)
#
#         return {'code':200,'msg':result_list,'user_list':user_return_list,'pass_percen_list':pass_percen_list}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



# @router.get("/daily_percen")
# async def daily_percen(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
#     '''
#     日结率
#     '''
#     try:
#         pro=jira_model(pro_code)
#         version_result=[]
#         v_list = []
#
#         sql_param=[]
#         if select_type == 'version':
#             v_list=list(version_list.split(','))
#             sql_param=[pro.affectedVersion.in_(v_list)]
#         else:
#             sql_param=[pro.created.between(start_time,end_time)]
#             group_version = db.query(pro.affectedVersion).filter(*sql_param).group_by(pro.affectedVersion).all()
#             v_list=[item.affectedVersion for item in group_version]
#
#         '''按版本维度'''
#         result_list= [[], []]
#         aa = []
#         for version in v_list:
#             version_detail={'name':version,'total':0,'avg_percen':0.00,'other_percen':0.00,'null_percen':0.00,'date_total':0}
#             # 符合当天
#             date_bug_ok=db.query(pro.affectedVersion,func.substring(pro.created,1,10).label('date'),func.count(pro.id).label('total'))\
#                 .filter(func.substring(pro.created,1,10)==func.substring(pro.resolved,1,10),pro.affectedVersion==version).group_by(func.substring(pro.created,1,10)).all()
#             date_bug_json={date_bug.date:date_bug.total for date_bug in date_bug_ok}
#
#             # 超过1天
#             date_bug_no = db.query(pro).filter(pro.affectedVersion == version).all()
#
#             date_bug_no_json={}
#             for all_bug in date_bug_no:
#                 c_time=str(all_bug.created)[0:10]
#                 if all_bug.resolved==None:
#                     if c_time in date_bug_no_json.keys():
#                         date_bug_no_json[c_time] += 1
#                     else:
#                         date_bug_no_json[c_time] = 1
#                     continue
#
#                 if c_time==str(all_bug.resolved)[0:10]: continue
#
#                 create_time=parse(str(all_bug.created))
#                 resolved=parse(str(all_bug.resolved))
#
#                 #判断是否小于24小时
#                 if ((resolved-create_time).total_seconds())/3600 < 24:
#                     if c_time in date_bug_json.keys():
#                         date_bug_json[c_time]+=1
#                     else:
#                         date_bug_json[c_time]=1
#                 else:
#                     if c_time in date_bug_no_json.keys():
#                         date_bug_no_json[c_time] += 1
#                     else:
#                         date_bug_no_json[c_time] = 1
#
#             #总数
#             date_bug_total = db.query(pro.affectedVersion,func.substring(pro.created, 1, 10).label('date'), func.count(pro.id).label('total'))\
#                 .filter(pro.affectedVersion == version).group_by(func.substring(pro.created, 1, 10)).all()
#             date_bug_total_json={date_bug.date:date_bug.total for date_bug in date_bug_total}
#
#
#             ok_total=0
#             no_total=0
#             for key,value in date_bug_total_json.items():
#                 ok_count,no_count,ok_percen,no_percen=0,0,0,0
#                 version_detail['total']+=value
#                 version_detail['date_total']+=1
#                 if date_bug_json.get(key)!=None: ok_count=date_bug_json.get(key)
#                 if date_bug_no_json.get(key)!=None: no_count=date_bug_no_json.get(key)
#                 ok_percen=ok_count/date_bug_total_json[key]*100
#                 no_percen=no_count/date_bug_total_json[key]*100
#                 ok_total+=ok_percen
#                 no_total+=no_percen
#
#             if version_detail['date_total']!=0:version_detail['avg_percen']=round(ok_total/version_detail['date_total'],2)
#             if version_detail['date_total']!= 0: version_detail['other_percen'] = round(no_total /version_detail['date_total'],2)
#             if version_detail['total']!=0:version_detail['null_percen']=100-version_detail['avg_percen']-version_detail['other_percen']
#             result_list[0].append(version_detail)
#
#         '''按人维度'''
#         all_user = db.query(pro.assignee).filter(*sql_param).group_by(pro.assignee).all()
#         for user in all_user:
#             user_detail = {'name': user.assignee, 'avg_percen': 0.00,'date_total': 0}
#
#             # 符合当天
#             user_date_ok = db.query(func.substring(pro.created, 1, 10).label('date'), func.count(pro.id).label('total')) \
#                 .filter(*sql_param).filter(func.substring(pro.created, 1, 10) == func.substring(pro.resolved, 1, 10),
#                         pro.assignee == user.assignee).group_by(func.substring(pro.created, 1, 10)).all()
#             user_date_json = {date_bug.date: date_bug.total for date_bug in user_date_ok}
#
#
#             # 超过1天
#             date_bug_no = db.query(pro).filter(pro.assignee == user.assignee).all()
#
#             for all_bug in date_bug_no:
#                 c_time = str(all_bug.created)[0:10]
#                 if all_bug.resolved == None: continue
#
#                 if c_time == str(all_bug.resolved)[0:10]: continue
#
#                 create_time = parse(str(all_bug.created))
#                 resolved = parse(str(all_bug.resolved))
#
#                 # 判断是否小于24小时
#                 if ((resolved - create_time).total_seconds()) / 3600 < 24:
#                     if c_time in user_date_json.keys():
#                         user_date_json[c_time] += 1
#                     else:
#                         user_date_json[c_time] = 1
#
#
#             # 总数
#             user_date_total = db.query(func.substring(pro.created, 1, 10).label('date'),func.count(pro.id).label('total')) \
#                 .filter(*sql_param).filter(pro.assignee == user.assignee).group_by(func.substring(pro.created, 1, 10)).all()
#             user_total_json = {date_bug.date: date_bug.total for date_bug in user_date_total}
#
#             ok_total = 0
#             for key,value in user_total_json.items():
#                 ok_count,ok_percen=0,0
#                 user_detail['date_total']+=1
#                 if user_date_json.get(key)!=None: ok_count=user_date_json.get(key)
#                 ok_percen=(ok_count/user_total_json[key])*100
#                 ok_total+=ok_percen
#
#             if user_detail['date_total']!=0:user_detail['avg_percen']=round(ok_total/user_detail['date_total'],2)
#             result_list[1].append(user_detail)
#
#         result_list[1] = sorted(result_list[1], key=lambda x: x["avg_percen"])
#         result_list[1] = list(reversed(result_list[1]))
#         return {'code':200,'msg':result_list,'aa':aa}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




