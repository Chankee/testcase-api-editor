#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：重开率


from typing import List,Union,Optional
from sqlalchemy import func
from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import testcase_schemas
from qa_dal.database import get_case_db,get_jira_db,get_online_db
from sqlalchemy.orm import Session
from sqlalchemy import or_
from qa_dal.models import jira_model,User
from qa_dal import qa_uitls
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from decimal import Decimal
from dateutil.parser import parse
import common.jira_base as jira_com
from qa_dal.models import QaProOnline
import requests
router = APIRouter(
    prefix="/summary/jira",
    tags=["jira统计"]
)

def dingding(context):
    url = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(
        '706567debfcbbffa52b61119c5843566ecf8c870d5a9fb7c82fec1e288b29c12')
    content = {
        "msgtype": "markdown",
        "markdown": {
            "title": "线上数据同步提醒",
            "text": context
        },
        "at": {
            "atMobiles": ['15986365650'],
            "isAtAll": False
        }
    }
    requests.post(url, json=content).json()


@router.get("/today_online")
async def get_today_online(today_time:str='',token:str='',db:Session=Depends(get_online_db)):
    '''
    同步当天线上情况
    '''

    try:

        today=db.query(QaProOnline).filter(QaProOnline.summary_date.like('{}%'.format(today_time))).first()

        if today!=None:
            dingding('{}数据已同步过了!'.format(today_time))
            return {'code': 203, 'msg': '{}数据已同步过了!'.format(today_time)}
        pro_name_json={
            'MAIFOU':'音泡',
            'LOCALMEET':'缘来同城',
            'LOV':'陌亲',
            'GMLIVE':'深得我心',
            'SEEKLOVE':'觅缘',
            'TIANMI': '甜觅',
            'CAMP':'Camp',
            'WAHA': 'Waha',
            'SQ':'甜言',
            'ZT':'中台',
            'OWONOVEL':'OWONOVEL',
            'KISSES':'kisses',
            'PANDORA':'叮当魔盒',
            'SWEETHEART': '甜心',
            'FUBOX':'福盒',
            'LUCKYBOX':'盒子很忙',
            'HASHBOX':'哈希部落',
            'ACCOMPANY':'伴你同行',
            'READ':'Readom'
        }
        pro_json= {'MAIFOU':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'LOCALMEET':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'LOV':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'GMLIVE':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'SEEKLOVE':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'TIANMI':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'CAMP':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'WAHA':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'SQ':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'ZT':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'OWONOVEL':{'sum_total':0,'sum_res_count':0,'sum_solve_count':0,'total':0,'res_count':0,'solve_count':0},
                    'KISSES': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                   'PANDORA': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                    'SWEETHEART':{'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                   'FUBOX': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                   'LUCKYBOX': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                   'HASHBOX': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                   'ACCOMPANY': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0},
                   'READ': {'sum_total': 0, 'sum_res_count': 0, 'sum_solve_count': 0, 'total': 0, 'res_count': 0,'solve_count': 0}
                   }

        date_list = []
        for pro in pro_json:
            jql_param = 'issuetype=缺陷 and project ={} and 缺陷来源=线上问题 and created<= "{} 23:59" ORDER BY created DESC'.format(pro,today_time)

            jira_clt = jira_com.INKE_JIRA(ticket=token)
            bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

            for bug in bug_list:

                created_time = bug.fields.created[0:10]
                pro_json[pro]['sum_total']+=1   #线上总数

                if created_time == today_time: pro_json[pro]['total']+=1
                if bug.fields.resolutiondate:
                    #汇总解决个数
                    pro_json[pro]['sum_solve_count'] += 1
                    #当天解决个数
                    if created_time==today_time: pro_json[pro]['solve_count'] += 1

                if bug.fields.status.name in ('InProcess','Resolved','Closed','Done') or bug.fields.resolutiondate:
                    #汇总响应个数
                    pro_json[pro]['sum_res_count'] += 1
                    #当天响应个数
                    if created_time==today_time:pro_json[pro]['res_count'] += 1


            detail={'pro_name':pro_name_json[pro],
                    'online_count':pro_json[pro]['sum_total'],
                    'online_res_percen':0,
                    'online_solve_percen':0,
                    'summary_date':today_time[0:10],
                    'same_day_total':pro_json[pro]['total'],
                    'same_day_solve_percen':100,
                    'same_day_res_percen':100}

            #计算汇总
            if detail['online_count']>0:
                detail['online_res_percen']=round(pro_json[pro]['sum_res_count']/detail['online_count']*100,2)
                detail['online_solve_percen'] = round(pro_json[pro]['sum_solve_count'] / detail['online_count']*100, 2)

            #计算当天
            if detail['same_day_total']>0:
                detail['same_day_solve_percen']=round(pro_json[pro]['solve_count']/detail['same_day_total']*100,2)
                detail['same_day_res_percen'] = round(pro_json[pro]['res_count'] / detail['same_day_total']*100, 2)

            date_list.append(detail)


        #添加到本地库
        for item in date_list:
            db_item = QaProOnline(**item)
            db.add(db_item)
        db.commit()

        dingding('同步数据成功')

        return {'code': 200, 'msg': '同步数据成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        dingding('接口报错，报错信息：{}'.format(error_info))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/daily")
async def get_delay(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str=''):
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        # 初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type == 'version': jql_param += ' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type == 'time': jql_param += ' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],
                                                                                                           end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        version_count,team_count,user_count = {},{},{}
        team_detail = {'中台金融': 0, '服务端': 0, 'iOS': 0, 'Android': 0, 'H5前端': 0, '运营后台': 0, 'Unity3D': 0, '微信小程序': 0,
                       '长沙后台': 0, '产运': 0, '其他': 0}
        return_json = {'version_list': [], 'team_name':[],'team_avg_daly_value':[],'team_over_value':{}, 'user_list':[],'over_user_list':[]}

        for bug in bug_list:
            # 版本维度
            version_name=''
            versions = bug.fields.versions
            if versions:
                version_name=versions[0].name

            count_delay(bug,version_name,version_count)



            '''团队维度数据'''
            belong = bug.fields.customfield_11302  # 影响版本
            components = bug.fields.components

            df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                       "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                       "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                       "安卓": "Android", "Unity3D": "Unity3D",
                       "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序","产运":"产运","其他":"其他"}

            team_name = ''
            if belong:
                team_name = belong.value
            else:
                if components != []:
                    if components[0].name in df_json.keys(): team_name = df_json[components[0].name]

            count_delay(bug,team_name,team_count)


            '''经办人维度'''
            assignee = bug.fields.assignee
            assignee_name = ''
            if assignee: assignee_name = assignee.displayName
            count_delay(bug, assignee_name, user_count)


        #计算版本数据
        summary_delay(version_count,return_json['version_list'])

        #团队
        team_list=[]
        summary_delay(team_count,team_list)
        for item in team_list:
            #柱形图
            return_json['team_name'].append(item['name'])
            return_json['team_avg_daly_value'].append(item['deylay_percen'])

            #圆图
            if item['name'] in team_detail.keys():
                team_detail[item['name']]=item['total_other']
        return_json['team_over_value']=team_detail

        #计算经办人数据
        summary_delay(user_count, return_json['user_list'])
        return_json['over_user_list']=return_json['user_list']
        return_json['user_list']=list(reversed(sorted(return_json['user_list'], key=lambda x: x["deylay_percen"])))
        return_json['over_user_list']=list(reversed(sorted(return_json['over_user_list'], key=lambda x: x["over_delay_percen"])))

        return {'code':200,'msg':return_json}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def summary_delay(count_info,return_json):
    '''计算日结率'''
    for key in count_info:
        detail_info = {'name':key,'total':count_info[key]['total'],'total_other':0,'delay_item':[],'deylay_percen': 0,'over_delay_percen': 0}  # 超一天缺陷占比

        # 计算每天的日结率
        total_dalay_parcen=0
        date_count=0

        date_item = count_info[key]['delay_json']
        for item in date_item:
            item_detail={'data_info':item,'other_count':date_item[item]['other_count'],
                         'dalay_count':date_item[item]['dalay_count'],'total':date_item[item]['total'],
                         'deylay_percen':0}

            if date_item[item]['total'] > 0:
                item_detail['deylay_percen']=round(date_item[item]['dalay_count'] / date_item[item]['total'] * 100, 2)
                detail_info['total_other'] += date_item[item]['other_count']
                total_dalay_parcen += round(date_item[item]['dalay_count'] / date_item[item]['total'] * 100, 2)
            date_count += 1
            detail_info['delay_item'].append(item_detail)

        if date_count > 0: detail_info['deylay_percen'] = round(total_dalay_parcen / date_count, 2)     #平均日结率
        if date_count > 0: detail_info['over_delay_percen'] = round(detail_info['total_other'] / detail_info['total']*100, 2)   #超1天缺陷占比
        return_json.append(detail_info)


def count_delay(bug,name,count_info):
    '''
    各维度日结个数
    '''
    resolutiondate = bug.fields.resolutiondate  # 解决时间
    created = str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))

    if name in count_info.keys() and name!='':

        # 所有bug
        count_info[name]['total'] += 1

        if resolutiondate:

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
        count_info[name] = {'total': 1,'delay_json': {}}

        other_count = 0
        dalay_count = 0

        if resolutiondate:
            resolved = str(datetime.strptime(resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800'))

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


@router.get("/online_detail")
async def online_detail(pro_code:str,version_list:str,start_time:str='',end_time:str='',online_level:str='',team:str='',status:str='',token:str=''):
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        jql_param='type=缺陷 and 缺陷来源=线上问题'
        if pro_code!='全部': jql_param+=' and project={}'.format(pro_code)
        if version_list!='': jql_param+=' and affectedVersion in ({})'.format(','.join(sql_version))
        if team!='全部': jql_param+=' and 缺陷归属={}'.format(team)
        if start_time!='': jql_param+=' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],end_time[0:10])
        if online_level!='全部': jql_param+=' and 故障级别={}'.format(online_level)
        if status!='全部': jql_param+=' and status in ({})'.format(status)
        jql_param+= ' ORDER BY created desc'

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        result_list=[]
        for bug in bug_list:

            #项目名称
            project_name = bug.fields.project
            if project_name:
                bug_detail={'project_name':project_name.name,
                            'version_name':'',
                            'online_level':'',
                            'JiraID':'',
                            'summary':'',
                            'assignee':'',
                            'belong':'',
                            'status':'',
                            'resolutiondate':'',
                            'created':'',
                            'create_name':''
                            }
                if bug.key: bug_detail['JiraID']=bug.key
                if bug.fields.summary: bug_detail['summary']=bug.fields.summary
                if bug.fields.versions: bug_detail['version_name']= bug.fields.versions[0].name
                if bug.fields.assignee: bug_detail['assignee'] = bug.fields.assignee.displayName
                if bug.fields.customfield_11302: bug_detail['belong']= bug.fields.customfield_11302.value
                if bug.fields.status: bug_detail['status'] = bug.fields.status.name
                if bug.fields.created: bug_detail['created']=str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))
                if bug.fields.resolutiondate: bug_detail['resolutiondate'] = str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))
                if bug.fields.customfield_11310: bug_detail['online_level']=bug.fields.customfield_11310.value
                if bug.fields.creator: bug_detail['create_name']=bug.fields.creator.displayName
                result_list.append(bug_detail)

        return {'code':200,'msg':result_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/reopen")
async def get_reopen(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str=''):
    '''
    重开率统计
    '''
    try:
        sql_version=['"{}"'.format(verion) for verion in version_list.split(',')]
        # 初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type == 'version': jql_param += ' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type == 'time': jql_param += ' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],
                                                                                           end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        version_count,user_count={},{}
        team_detail = {'中台金融': 0, '服务端': 0, 'iOS': 0, 'Android': 0, 'H5前端': 0, '运营后台': 0, 'Unity3D': 0, '微信小程序': 0,
                       '长沙后台': 0,'产运':0,'其他':0}
        return_json={'version_list':[],'team_json':{},'user_list':[]}

        for bug in bug_list:
            #版本维度
            version_name=bug.fields.versions
            reopen=bug.fields.customfield_10103

            if version_name:
                if version_name[0].name in version_count.keys():
                    version_count[version_name[0].name]['total']+=1
                    if reopen:
                        if reopen.value=='yes': version_count[version_name[0].name]['other_count'] += 1
                else:
                    version_count[version_name[0].name]={'name':version_name[0].name,'total':1,'other_count':0}
                    if reopen:
                        if reopen.value=='yes': version_count[version_name[0].name]['other_count']+=1



            '''团队维度数据'''
            belong = bug.fields.customfield_11302  # 影响版本
            components = bug.fields.components

            df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                       "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                       "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                       "安卓": "Android", "Unity3D": "Unity3D",
                       "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序","产运":"产运","其他":"其他"}

            team_name = ''
            if belong:
                team_name = belong.value
            else:
                if components != []:
                    if components[0].name in df_json.keys(): team_name = df_json[components[0].name]

            if team_name in team_detail.keys() and reopen:
                if reopen.value == 'yes': team_detail[team_name]+=1


            '''个人维度数据'''
            assignee=bug.fields.assignee

            if assignee:
                assignee_name=assignee.displayName
                if assignee_name in user_count.keys():
                    user_count[assignee_name]['total']+=1
                    if reopen:
                        if reopen.value == 'yes': user_count[assignee_name]['other_count'] += 1
                else:
                    user_count[assignee_name]={'name':assignee_name,'total':1,'other_count':0}
                    if reopen:
                        if reopen.value == 'yes': user_count[assignee_name]['other_count'] += 1

        #计算版本
        for key in version_count:
            version_detail={'name':key,'other_count':version_count[key]['other_count'],'total':version_count[key]['total'],'percen':0}
            if version_count[key]['total']>0:
                version_detail['percen']=round(version_count[key]['other_count']/version_count[key]['total']*100,2)
            return_json['version_list'].append(version_detail)

        #团队维度
        return_json['team_json']=team_detail

        #计算个人
        for key in user_count:
            user_detail={'name':key,'other_count':user_count[key]['other_count'],'total':user_count[key]['total'],'percen':0}
            if user_count[key]['total']>0:
                user_detail['percen']=round(user_count[key]['other_count']/user_count[key]['total']*100,2)
            return_json['user_list'].append(user_detail)

        return_json['user_list'] = list(reversed(sorted(return_json['user_list'], key=lambda x: x["percen"])))

        return {'code':200,'msg':return_json}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/online")
async def get_online(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str=''):
    '''
    线上率
    '''
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        # 初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type == 'version': jql_param += ' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type == 'time': jql_param += ' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],
                                                                                           end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        version_count,user_count={},{}
        team_detail = {'中台金融': 0, '服务端': 0, 'iOS': 0, 'Android': 0, 'H5前端': 0, '运营后台': 0, 'Unity3D': 0, '微信小程序': 0,
                       '长沙后台': 0,'产运':0,'其他':0}
        return_json={'version_list':[],'team_json':{},'user_list':[]}

        for bug in bug_list:
            #版本维度
            version_name=bug.fields.versions
            isonline=bug.fields.customfield_10102

            if version_name:
                if version_name[0].name in version_count.keys():
                    version_count[version_name[0].name]['total']+=1
                    if isonline:
                        if isonline.value=='线上问题': version_count[version_name[0].name]['other_count'] += 1
                else:
                    version_count[version_name[0].name]={'name':version_name[0].name,'total':1,'other_count':0}
                    if isonline:
                        if isonline.value=='线上问题': version_count[version_name[0].name]['other_count']+=1



            '''团队维度数据'''
            belong = bug.fields.customfield_11302  # 影响版本
            components = bug.fields.components

            df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                       "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                       "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                       "安卓": "Android", "Unity3D": "Unity3D",
                       "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序","产运":"产运","其他":"其他"}

            team_name = ''
            if belong:
                team_name = belong.value
            else:
                if components != []:
                    if components[0].name in df_json.keys(): team_name = df_json[components[0].name]

            if team_name in team_detail.keys() and isonline:
                if isonline.value == '线上问题': team_detail[team_name]+=1


            '''个人维度数据'''
            assignee=bug.fields.assignee

            if assignee:
                assignee_name=assignee.displayName
                if assignee_name in user_count.keys():
                    user_count[assignee_name]['total']+=1
                    if isonline:
                        if isonline.value == '线上问题': user_count[assignee_name]['other_count'] += 1
                else:
                    user_count[assignee_name]={'name':assignee_name,'total':1,'other_count':0}
                    if isonline:
                        if isonline.value == '线上问题': user_count[assignee_name]['other_count'] += 1

        #计算版本
        for key in version_count:
            version_detail={'name':key,'other_count':version_count[key]['other_count'],'total':version_count[key]['total'],'percen':0}
            if version_count[key]['total']>0:
                version_detail['percen']=round(version_count[key]['other_count']/version_count[key]['total']*100,2)
            return_json['version_list'].append(version_detail)

        #团队维度
        return_json['team_json']=team_detail

        #计算个人
        for key in user_count:
            user_detail={'name':key,'other_count':user_count[key]['other_count'],'total':user_count[key]['total'],'percen':0}
            if user_count[key]['total']>0:
                user_detail['percen']=round(user_count[key]['other_count']/user_count[key]['total']*100,2)
            return_json['user_list'].append(user_detail)

        return_json['user_list'] = list(reversed(sorted(return_json['user_list'], key=lambda x: x["percen"])))

        return {'code':200,'msg':return_json}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/bug_avg_time")
async def get_bug_avg_time(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str=''):
    '''
    平均解决周期
    '''
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        # 初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type == 'version': jql_param += ' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type == 'time': jql_param += ' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],
                                                                                           end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        version_count,user_count={},{}
        team_detail = {'中台金融': {'avg_time':0,'total':0},
                       '服务端': {'avg_time':0,'total':0},
                       'iOS': {'avg_time':0,'total':0},
                       'Android':{'avg_time':0,'total':0},
                       'H5前端': {'avg_time':0,'total':0},
                       '运营后台': {'avg_time':0,'total':0},
                       'Unity3D': {'avg_time':0,'total':0},
                       '微信小程序': {'avg_time':0,'total':0},
                       '长沙后台': {'avg_time':0,'total':0},
                       '产运':{'avg_time':0,'total':0},
                       '其他':{'avg_time':0,'total':0}}
        return_json={'version_list':[],'team_name':[],'team_value':[],'user_list':[]}

        for bug in bug_list:
            #版本维度
            version_name=bug.fields.versions
            resolutiondate=bug.fields.resolutiondate
            created=str(datetime.strptime(bug.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800'))
            r_date=''
            if resolutiondate:
                r_date=str(datetime.strptime(bug.fields.resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800'))

            if version_name:
                if version_name[0].name in version_count.keys():
                    version_count[version_name[0].name]['total']+=1
                    if r_date!='':
                        version_count[version_name[0].name]['avg_time'] +=get_time(created,r_date)
                        version_count[version_name[0].name]['other_count']+=1
                else:
                    version_count[version_name[0].name]={'name':version_name[0].name,'total':1,'avg_time':0,'other_count':0}
                    if r_date != '':
                        version_count[version_name[0].name]['avg_time'] += get_time(created, r_date)
                        version_count[version_name[0].name]['other_count'] += 1



            '''团队维度数据'''
            belong = bug.fields.customfield_11302  # 影响版本
            components = bug.fields.components

            df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                       "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                       "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                       "安卓": "Android", "Unity3D": "Unity3D",
                       "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序","产运":"产运","其他":"其他"}

            team_name = ''
            if belong:
                team_name = belong.value
            else:
                if components != []:
                    if components[0].name in df_json.keys(): team_name = df_json[components[0].name]

            if team_name in team_detail.keys():
                if r_date != '':
                    team_detail[team_name]['avg_time'] += get_time(created, r_date)
                    team_detail[team_name]['total'] += 1


            '''个人维度数据'''
            assignee=bug.fields.assignee

            if assignee:
                assignee_name=assignee.displayName
                if assignee_name in user_count.keys():
                    user_count[assignee_name]['total']+=1
                    if r_date != '':
                        user_count[assignee_name]['avg_time'] += get_time(created, r_date)
                        user_count[assignee_name]['other_count'] += 1
                else:
                    user_count[assignee_name]={'name':assignee_name,'total':1,'other_count':0,'avg_time':0}
                    if r_date != '':
                        user_count[assignee_name]['avg_time'] += get_time(created, r_date)
                        user_count[assignee_name]['other_count'] += 1

        #计算版本
        for key in version_count:
            version_detail={'name':key,'avg_time':0,'total':version_count[key]['total']}
            if version_count[key]['other_count']>0:
                version_detail['avg_time']=round(version_count[key]['avg_time']/version_count[key]['other_count'],2)
            return_json['version_list'].append(version_detail)

        #团队维度
        for key,value in team_detail.items():
            return_json['team_name'].append(key)
            if team_detail[key]['total']>0:
                return_json['team_value'].append(round(team_detail[key]['avg_time']/team_detail[key]['total'],2))
            else:
                return_json['team_value'].append(0)

        #计算个人
        for key in user_count:
            user_detail={'name':key,'avg_time':0,'total':user_count[key]['total']}
            if user_count[key]['other_count']>0:
                user_detail['avg_time']=round(user_count[key]['avg_time']/user_count[key]['other_count'],2)
            return_json['user_list'].append(user_detail)

        return_json['user_list'] = list(reversed(sorted(return_json['user_list'], key=lambda x: x["avg_time"])))

        return {'code':200,'msg':return_json}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.get("/solve")
async def get_solve(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',token:str=''):
    '''
    遗留率
    '''
    try:
        sql_version = ['"{}"'.format(verion) for verion in version_list.split(',')]
        # 初始化搜索条件
        jql_param = 'project={} and issuetype=缺陷'.format(pro_code)
        if select_type == 'version': jql_param += ' and affectedVersion in ({})'.format(','.join(sql_version))
        if select_type == 'time': jql_param += ' and created >="{} 00:00" and created<= "{} 23:59"'.format(start_time[0:10],
                                                                                           end_time[0:10])

        jira_clt = jira_com.INKE_JIRA(ticket=token)
        bug_list = jira_clt.search_issues(jql_param, maxResults=2000)

        version_count,team_count,user_count,create_count={},{},{},{}

        return_json={'version_list':[],'team_list':[],'create_user_list':[],'user_list':[]}

        for bug in bug_list:
            #版本维度
            versions=bug.fields.versions

            if versions: solve_summary(versions[0].name,bug,version_count)



            '''团队维度数据'''
            belong = bug.fields.customfield_11302  # 影响版本
            components = bug.fields.components

            df_json = {"服务端": "服务端", "IOS": "iOS", "Android": "Android", "金融": "金融中台", "H5": "H5前端",
                       "后台": "运营后台", "运营后台": "运营后台", "IOS端": "iOS", "Android端": "Android", "运营后台端": "运营后台",
                       "H5端": "H5前端", "iOS端": "iOS", "Unity": "Unity3D", "ios": "iOS",
                       "安卓": "Android", "Unity3D": "Unity3D",
                       "Ios": "iOS", "h5": "H5前端", "Andorid": "Android", "管理后台": "运营后台", "小程序": "微信小程序","产运":"产运","其他":"其他"}

            team_name = ''
            if belong:
                team_name = belong.value
            else:
                if components != []:
                    if components[0].name in df_json.keys(): team_name = df_json[components[0].name]

            solve_summary(team_name, bug, team_count)


            '''经办人维度'''
            assignee = bug.fields.assignee
            assignee_name = ''
            if assignee: assignee_name = assignee.displayName
            solve_summary(assignee_name, bug, user_count)


            '''创建人维度'''
            creator = bug.fields.creator
            creator_name = ''
            if creator: creator_name = creator.displayName
            solve_summary(creator_name, bug, create_count)


        solve_percen(version_count,return_json['version_list'])  #计算版本
        solve_percen(team_count, return_json['team_list'])  # 计算团队
        solve_percen(user_count, return_json['user_list'])  # 计算经办人
        solve_percen(create_count, return_json['create_user_list'])  # 计算创建人


        return {'code':200,'msg':return_json}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


def solve_percen(count_info,list_info):
    for key in count_info:
        detail = {'name': key, 'resolved_count': count_info[key]['resolved_count'],
                  'unresolved_count': count_info[key]['unresolved_count'],
                  'invalid_count': count_info[key]['invalid_count'],
                  'total': count_info[key]['total'],
                  'resolved_percen': 0, 'unresolved_percen': 0, 'invalid_percen': 0}

        if count_info[key]['total'] > 0:
            detail['resolved_percen'] = round(count_info[key]['resolved_count'] / count_info[key]['total'] * 100,
                                              2)
            detail['unresolved_percen'] = round(
                count_info[key]['unresolved_count'] / count_info[key]['total'] * 100, 2)
            detail['invalid_percen'] = round(count_info[key]['invalid_count'] / count_info[key]['total'] * 100, 2)
        list_info.append(detail)


def solve_summary(name,bug,count_info):
    resolution = bug.fields.resolution  # 解决结果
    if name in count_info.keys() and name!='':
        count_info[name]['total'] += 1

        if resolution:
            # 已解决数
            if resolution.name in ('已修正', '不必改'):
                count_info[name]['resolved_count'] += 1
            # 未解决缺陷数
            if resolution.name in ('Unresolved', '未解决', '下版修复', '需求纳入版本计划'):
                count_info[name]['unresolved_count'] += 1
            # 无效BUG
            if resolution.name in ('需求如此', '重复提交'):
                count_info[name]['invalid_count'] += 1
        elif resolution == None:
            # 未解决数
            count_info[name]['unresolved_count'] += 1

    elif name not in count_info.keys() and name != '':

        count_info[name] = {'resolved_count': 0, 'invalid_count': 0, 'unresolved_count': 0,'total': 1}

        if resolution:
            # 已解决数
            if resolution.name in ('已修正', '不必改'):
                count_info[name]['resolved_count'] += 1
            # 未解决缺陷数
            if resolution.name in ('Unresolved', '未解决', '下版修复', '需求纳入版本计划'):
                count_info[name]['unresolved_count'] += 1
            # 无效BUG
            if resolution.name in ('需求如此', '重复提交'):
                count_info[name]['invalid_count'] += 1
        elif resolution == None:
            # 未解决数
            count_info[name]['unresolved_count'] += 1



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
#
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
#         '''按职能分组'''
#         pro_fun_reopen=db.query(pro.belong,func.count(pro.belong).label('total')).filter(*reopen_sql_param).filter(pro.reopen != 0).group_by(pro.belong).all()
#         pro_fun_reopen_json={item.belong: item.total for item in pro_fun_reopen}
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
#         return {'code': 200, 'msg':'数据已加载！','version_list':version_result,'pro_fun_list':pro_fun_reopen_json,'people_list':list(reversed(people_result))}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}
#
#
#
#
#
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
#         '''按职能分组'''
#         pro_fun_online=db.query(pro.belong,func.count(pro.belong).label('total')).filter(*online_sql_param).filter(pro.isonline != 0).group_by(pro.belong).all()
#         pro_fun_online_json={item.belong: item.total for item in pro_fun_online}
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
#             if people_detail['total'] != 0: people_detail['online_percen'] = round(
#                 people_detail['online_count'] / people_detail['total'] * 100,2)
#             people_result.append(people_detail)
#         people_result=sorted(people_result, key = lambda x: x["online_percen"])
#
#         return {'code': 200, 'msg':'数据已加载！','version_list':version_result,'pro_fun_list':pro_fun_online_json,'people_list':list(reversed(people_result))}
#
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}
#
#
#
#
# @router.get("/bug_avg_time")
# async def bug_avg_time(pro_code:str,version_list:str,start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
#     '''
#     平均解决周期
#     '''
#     #try:
#     pro=jira_model(pro_code)
#
#     version_result=[]
#     avg_sql_param=[]
#     v_list=[]
#     if select_type == 'version':
#         v_list=list(version_list.split(','))
#         avg_sql_param=[pro.affectedVersion.in_(v_list),pro.resolved!='']
#         version_list=db.query(pro.affectedVersion,func.count(pro.affectedVersion).label('total'))\
#             .filter(*avg_sql_param).group_by(pro.affectedVersion).all()
#         version_result ={item.affectedVersion:item.total for item in version_list}
#     else:
#         avg_sql_param=[pro.created.between(start_time,end_time),pro.resolved!='']
#         version_list = db.query(pro.affectedVersion,func.count(pro.affectedVersion).label('total'))\
#             .filter(*avg_sql_param).group_by(pro.affectedVersion).all()
#         v_list=[item.affectedVersion for item in version_list]
#         version_result = {item.affectedVersion: item.total for item in version_list}
#
#
#     '''按版本'''
#     return_version=[]
#     all_bug_list=db.query(pro).filter(*avg_sql_param).all()
#     for version in v_list:
#         version_detail = {'version_name': '', 'bug_count': 0, 'avg_time': 0.00}
#         version_detail['version_name']=version
#         version_detail['bug_count']=[0, version_result.get(version)][version_result.get(version) != None]
#
#         #计算平均时间
#         if version_detail['bug_count']!=0:
#             avg_count = 0
#             avg_total_time = 0
#             for bug in all_bug_list:
#                 if bug.affectedVersion==version:
#                     avg_count+=1
#                     avg_total_time+=get_time(str(bug.created),str(bug.resolved))
#             version_detail['avg_time']=round(avg_total_time/avg_count,2)
#         return_version.append(version_detail)
#
#
#     '''按职能分组'''
#     #根据职能分组
#     pro_fun_avg=db.query(pro.belong).filter(*avg_sql_param).group_by(pro.belong).all()
#     pro_fun_avg_json=[item.belong for item in pro_fun_avg]
#
#     #根据职能查询所有缺陷
#     pro_fun_bug_list=db.query(pro).filter(pro.belong.in_(pro_fun_avg_json),pro.resolved!='').all()
#
#     pro_fun_return={}
#     for pro_fun in pro_fun_avg:
#         time_count=0
#         count=0
#         for bug in pro_fun_bug_list:
#             if bug.belong==pro_fun.belong:
#                 count+=1
#                 time_count+=get_time(str(bug.created),str(bug.resolved))
#         pro_fun_return[pro_fun.belong]=round(time_count/count,2)
#
#
#     '''按人维度'''
#     avg_people = db.query(pro.assignee, func.count(pro.assignee).label('total')).filter(*avg_sql_param).group_by(
#         pro.assignee).all()
#     people_total = db.query(pro).filter(*avg_sql_param).all()
#     people_result = []
#     for people in avg_people:
#         people_detail = {'name': '', 'bug_count': 0, 'avg_time': 0}
#         people_detail['name'] = people.assignee
#         people_detail['bug_count'] = people.total
#
#         # 计算平均周期
#         people_time_count = 0
#         people_time = 0
#         for pr in people_total:
#             if pr.assignee == people.assignee:
#                 people_time_count += 1
#                 people_time += get_time(str(pr.created), str(pr.resolved))
#
#         people_detail['avg_time'] = round(people_time / people_time_count, 2)
#         people_result.append(people_detail)
#
#     people_result = sorted(people_result, key=lambda x: x["avg_time"])
#
#     return {'code': 200, 'msg':'数据已加载！','version_list':return_version,'pro_fun_list':pro_fun_return,'people_list':list(reversed(people_result))}
#
#     # except Exception as ex:
#     #     error_line = ex.__traceback__.tb_lineno
#     #     error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#     #     return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}
#
#
#
#
#
#
#
#
#
# '''-----------------------------------缺陷分布--------------------------------------'''
# @router.get("/version_trend")
# async def version_trend(pro_code:str, versions:str,db:Session=Depends(get_jira_db)):
#     '''
#     版本趋势图
#     '''
#     try:
#         pro = jira_model(pro_code)
#         versions = versions.split(',')
#         data = [[0 for j in range(len(versions))] for i in range(5)]
#         for idx, i in enumerate(versions):
#             res=db.query(pro.priority,func.count(pro.priority).label('num')).filter(pro.affectedVersion==i).group_by(pro.priority).all()
#             res=[{'priority':item.priority,'num':item.num} for item in res]
#             total = 0
#             for v in res:
#                 total = total + v['num']
#                 if v['priority'] == 'Medium':
#                     data[3][idx] = v['num']
#                     continue
#                 if v['priority'] == 'Low':
#                     data[4][idx] = v['num']
#                     continue
#                 if v['priority'] == 'High':
#                     data[2][idx] = v['num']
#                     continue
#                 data[1][idx] = v['num']
#             data[0][idx] = total
#         return {'code': 200, 'data': data}
#     except Exception as ex:
#         error_line = ex.__traceback__.tb_lineno
#         error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
#         return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}






