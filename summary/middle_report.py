from sqlalchemy import func
from fastapi import APIRouter
from fastapi import Depends
from qa_dal.database import get_case_db,get_jira_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from qa_dal.models import jira_model,User,Delay,TestCase,Version
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from decimal import Decimal
from dateutil.parser import parse

import common.jira_base as jira_com

router = APIRouter(
    prefix="/summary/report",
    tags=["质量月报"]
)


@router.get("/middle/total")
async def get_total(start_time:str='',end_time:str='',select_type:str='',token:str=''):
    jql_param = 'type=缺陷 and created >={} and created<= {}'.format(start_time[0:10],end_time[0:10])

    jira_clt = jira_com.INKE_JIRA(ticket=token)
    bug_list = jira_clt.search_issues(jql_param, maxResults=1000)

    # 清洗数据
    h5_df_json = {"H5": "H5前端", "H5端": "H5前端", "h5": "H5前端",'H5前端':'H5前端'}
    manage_df_json = {"后台": "运营后台", "运营后台": "运营后台", "运营后台端": "运营后台", "管理后台": "运营后台"}
    finance_df_json = {"金融": "金融中台",'金融中台':'金融中台'}

    select_json={'H5前端':h5_df_json,'运营后台':manage_df_json,'金融中台':finance_df_json}

    #返回结果
    result={'bug_detail_total':0,'bug_detail':[],'bug_reopen':[],'bug_avg_time':[],'bug_dalay':[],'bug_online':[]}

    bug_detail = {}
    bug_reopen = {}
    bug_avg_time = {}
    bug_dalay = {}
    bug_online = {}

    for bug in bug_list:

        bug_info_list = []
        belong = bug.fields.customfield_11302
        components = bug.fields.components
        if select_type not in select_json.keys(): continue

        #清洗数据
        if belong:
            if belong.value in select_json[select_type].keys():
                bug_info_list.clear()
                bug_info_list.append(bug)

        elif components:
            if components[0].name in select_json[select_type].keys() and len(bug_info_list)==0:
                bug_info_list.clear()
                bug_info_list.append(bug)


        if len(bug_info_list)==0: continue

        '''bug情况-个人维度'''
        middle_bug_detail(bug_info_list,bug_detail)

        '''bug情况-'''

    return bug_detail


def middle_bug_detail(bug_info_list,bug_detail):
    bug_info = bug_info_list[0]
    # bug情况-个人维度
    bug_level_list = {'Highest': 1, 'High': 1, 'Medium': 1, 'Low': 1, 'Lowest': 1}
    assignee = bug_info.fields.assignee
    priority = bug_info.fields.priority

    # 判断经办人和用例等级赋值
    if assignee and priority:
        if assignee.displayName in bug_detail.keys():
            bug_detail[assignee.displayName]['total'] += 1
            bug_detail[assignee.displayName][priority.name] += bug_level_list[priority.name]
        elif assignee.displayName not in bug_detail.keys():
            bug_detail[assignee.displayName] = {'Highest': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Lowest': 0, 'total': 1}
            bug_detail[assignee.displayName][priority.name] += bug_level_list[priority.name]




@router.get("/middle/reopen")
async def get_open(start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
    '''
    重开率统计
    '''
    try:
        pro=jira_model('middleground')

        sql_param=[pro.created.between(start_time, end_time),pro.belong==select_type]


        '''按人维度'''
        reopen_people=db.query(pro.assignee,func.count(pro.assignee).label('total')).filter(*sql_param).group_by(pro.assignee).filter(pro.reopen != 0).all()
        people_json = {item.assignee: item.total for item in reopen_people}

        #所有缺陷
        people_total_list = db.query(pro.assignee, func.count(pro.assignee).label('total')).filter(*sql_param).group_by(pro.assignee).all()
        people_total_json = {item.assignee: item.total for item in people_total_list}

        #所有人员
        people_list=db.query(pro.assignee).filter(*sql_param).group_by(pro.assignee).all()

        people_result = []
        for people in people_list:
            people_detail={'name':'','reopen_count':0,'total':0,'reopen_percen':0.0}
            people_detail['name']=people.assignee
            people_detail['reopen_count']=[0, people_json.get(people.assignee)][people_json.get(people.assignee) != None]
            people_detail['total']=[0, people_total_json.get(people.assignee)][people_total_json.get(people.assignee) != None]
            if people_detail['total'] != 0: people_detail['reopen_percen'] = round(people_detail['reopen_count'] / people_detail['total'] * 100,2)
            people_result.append(people_detail)
        people_result=sorted(people_result, key = lambda x: x["reopen_percen"])

        return {'code': 200, 'msg':'数据已加载！','people_list':list(reversed(people_result))}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/middle/bug_avg_time")
async def bug_avg_time(start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
    '''
    平均解决周期
    '''
    try:
        pro=jira_model('middleground')

        sql_param = [pro.created.between(start_time, end_time), pro.belong == select_type,pro.resolved!=None]


        '''按人维度'''
        avg_people=db.query(pro.assignee,func.count(pro.assignee).label('total')).filter(*sql_param).group_by(pro.assignee).all()
        people_total=db.query(pro).filter(*sql_param).all()
        people_result = []
        for people in avg_people:
            people_detail={'name':'','bug_count':0,'avg_time':0}
            people_detail['name']=people.assignee
            people_detail['bug_count']=people.total

            #计算平均周期
            people_time_count=0
            people_time=0
            for pr in people_total:
                if pr.assignee == people.assignee:
                    people_time_count+=1
                    people_time+=get_time(str(pr.created),str(pr.resolved))

            people_detail['avg_time']=round(people_time/people_time_count,2)
            people_result.append(people_detail)

        people_result=sorted(people_result, key = lambda x: x["avg_time"])

        return {'code': 200, 'msg':'数据已加载！','people_list':list(reversed(people_result))}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



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



@router.get("/middle/bug_detail")
async def bug_detail(start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
    try:
        pro = jira_model('middleground')

        sql_param = [pro.created.between(start_time, end_time), pro.belong == select_type]

        #按端划分
        pro_fun_list = db.query(pro.belong, func.count(pro.belong).label('total')).filter(
            *sql_param).group_by(pro.belong).all()
        pro_fun_json = {item.belong:item.total for item in pro_fun_list}


        #按个人维度
        user_list=db.query(pro).filter(*sql_param).group_by(pro.assignee).all()
        bug_list=db.query(pro).filter(*sql_param).all()

        bug_return=[]
        for user in user_list:
            detail={'name':user.assignee,'High':0,'Medium':0,'Low':0,'total':0}
            for bug in bug_list:
                if user.assignee != bug.assignee: continue
                if user.priority =='High': detail['High']+=1
                if user.priority == 'Medium': detail['Medium'] += 1
                if user.priority == 'Low': detail['Low'] += 1
                detail['total']+=1
            bug_return.append(detail)
        bug_return = sorted(bug_return, key=lambda x: x["total"])

        return {'code':200,'pro_fun':pro_fun_json,'bug_list':list(reversed(bug_return))}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.get("/middle/online")
async def get_online(start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
    '''
    线上bug率
    '''
    try:
        pro = jira_model('middleground')

        sql_param = [pro.created.between(start_time, end_time), pro.belong == select_type]


        '''按人维度'''
        online_people=db.query(pro.assignee,func.count(pro.assignee).label('total')).filter(*sql_param).group_by(pro.assignee).filter(pro.isonline != 0).all()
        people_json = {item.assignee: item.total for item in online_people}

        #所有缺陷
        people_total_list = db.query(pro.assignee, func.count(pro.assignee).label('total')).filter(*sql_param).group_by(pro.assignee).all()
        people_total_json = {item.assignee: item.total for item in people_total_list}

        #所有人员
        people_list=db.query(pro.assignee).filter(*sql_param).group_by(pro.assignee).all()

        people_result = []
        for people in people_list:
            people_detail={'name':'','online_count':0,'total':0,'online_percen':0.0}
            people_detail['name']=people.assignee
            people_detail['online_count']=[0, people_json.get(people.assignee)][people_json.get(people.assignee) != None]
            people_detail['total']=[0, people_total_json.get(people.assignee)][people_total_json.get(people.assignee) != None]
            if people_detail['total'] != 0: people_detail['online_percen'] = round(people_detail['online_count'] / people_detail['total'] * 100,2)
            people_result.append(people_detail)
        people_result=sorted(people_result, key = lambda x: x["online_percen"])

        return {'code': 200, 'msg':'数据已加载！','people_list':list(reversed(people_result))}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/middle/delay")
async def get_delay(start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db),casedb:Session=Depends(get_case_db)):
    '''
    延期提测情况
    '''
    try:
        pro = jira_model('middleground')

        #获取影响版本
        group_version = db.query(pro.affectedVersion).filter(pro.created.between(start_time, end_time),pro.belong == select_type)\
            .group_by(pro.affectedVersion).all()
        version_list = [item.affectedVersion for item in group_version]

        group_user = db.query(pro.assignee).filter(pro.belong == select_type).\
            group_by(pro.assignee).all()
        user_list=[item.assignee for item in group_user]

        result=casedb.query(Delay).filter(Delay.version_name.in_(version_list),Delay.user_name.in_(user_list),Delay.isdelete==0).order_by(Delay.user_name.desc()).all()

        return {'code':200,'msg':result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/middle/selfcase")
async def get_selfcase(start_time:str='',end_time:str='',select_type:str='',sys_db:Session=Depends(get_sso_db),case_db:Session=Depends(get_case_db)):


    # 查询所有开发人员
    test_fun = {'androiddev': (TestCase.android_name, TestCase.android_result,TestCase.android_runtime),
                'iosdev': (TestCase.ios_name, TestCase.ios_result,TestCase.ios_runtime),
                'managedev': (TestCase.manage_name, TestCase.manage_result,TestCase.manage_runtime),
                'appletdev': (TestCase.applet_name, TestCase.applet_result,TestCase.applet_runtime),
                'h5dev': (TestCase.h5_name, TestCase.h5_result,TestCase.h5_runtime),
                'serverdev': (TestCase.server_name, TestCase.server_result,TestCase.server_runtime),
                'tester': (TestCase.tester,TestCase.tester_result,TestCase.tester_result)}

    user_list = sys_db.query(User).filter(User.group_name==select_type).all()


    '''个人自测通过率'''
    user_return_list=[]
    pass_percen_list=[]

    user_total_list=[]
    for user in user_list:
        user_detail={'name':user.user_name,'total':0,'pass_count':0,'fail_count':0,'pass_percen':0}
        user_return_list.append(user.user_name)
        user_detail['total'] = case_db.query(TestCase).filter(test_fun[user.pro_fun][0] == user.user_name,test_fun[user.pro_fun][1].in_(['PASS', 'FAIL']),
                                                         test_fun[user.pro_fun][2].between(start_time, end_time)).count()

        user_detail['pass_count'] = case_db.query(TestCase).filter(test_fun[user.pro_fun][0] == user.user_name,test_fun[user.pro_fun][1]=='PASS',test_fun[user.pro_fun][2].between(start_time,end_time)).count()

        if user_detail['total']!=0: user_detail['pass_percen']=round(user_detail['pass_count']/user_detail['total']*100,2)
        user_detail['fail_count']=user_detail['total']-user_detail['pass_count']
        pass_percen_list.append(user_detail['pass_percen'])
        user_total_list.append(user_detail)

    user_total_list = sorted(user_total_list, key=lambda x: x["pass_percen"])

    return {'code':200,'user_list':user_return_list,'pass_percen_list':pass_percen_list,'user_total_list':list(reversed(user_total_list))}




@router.get("/middle/daily_percen")
async def daily_percen(start_time:str='',end_time:str='',select_type:str='',db:Session=Depends(get_jira_db)):
    '''
    日结率
    '''
    try:
        pro = jira_model('middleground')

        sql_param = [pro.created.between(start_time, end_time), pro.belong == select_type]

        result_list=[]
        '''按人维度'''
        all_user = db.query(pro.assignee).filter(*sql_param).group_by(pro.assignee).all()
        for user in all_user:
            user_detail = {'name': user.assignee, 'avg_percen': 0.00,'date_total': 0}

            # 符合当天
            user_date_ok = db.query(func.substring(pro.created, 1, 10).label('date'), func.count(pro.id).label('total')) \
                .filter(*sql_param).filter(func.substring(pro.created, 1, 10) == func.substring(pro.resolved, 1, 10),
                        pro.assignee == user.assignee).group_by(func.substring(pro.created, 1, 10)).all()
            user_date_json = {date_bug.date: date_bug.total for date_bug in user_date_ok}

            # 超过1天
            date_bug_no = db.query(pro).filter(pro.assignee == user.assignee).all()

            for all_bug in date_bug_no:
                c_time = str(all_bug.created)[0:10]
                if all_bug.resolved == None: continue

                if c_time == str(all_bug.resolved)[0:10]: continue

                create_time = parse(str(all_bug.created))
                resolved = parse(str(all_bug.resolved))

                # 判断是否小于24小时
                if ((resolved - create_time).total_seconds()) / 3600 < 24:
                    if c_time in user_date_json.keys():
                        user_date_json[c_time] += 1
                    else:
                        user_date_json[c_time] = 1

            # 总数
            user_date_total = db.query(func.substring(pro.created, 1, 10).label('date'),func.count(pro.id).label('total')) \
                .filter(*sql_param).filter(pro.assignee == user.assignee).group_by(func.substring(pro.created, 1, 10)).all()
            user_total_json = {date_bug.date: date_bug.total for date_bug in user_date_total}

            ok_total = 0
            for key,value in user_total_json.items():
                ok_count,ok_percen=0,0
                user_detail['date_total']+=1
                if user_date_json.get(key)!=None: ok_count=user_date_json.get(key)
                ok_percen=(ok_count/user_total_json[key])*100
                ok_total+=ok_percen

            if user_detail['date_total']!=0:user_detail['avg_percen']=round(ok_total/user_detail['date_total'],2)
            result_list.append(user_detail)

        result_list = sorted(result_list, key=lambda x: x["avg_percen"])
        result_list = list(reversed(result_list))
        return {'code':200,'msg':result_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



