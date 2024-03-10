from fastapi import APIRouter
from fastapi import Depends
from qa_dal.database import get_case_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from qa_dal.models import DingDing,DingDingRecord,User,MySelfRecord,TestPlan,PlanCase,Project
from typing import List, Optional
from pydantic import BaseModel
import common.jira_base as jira_com
import datetime
import requests

router = APIRouter(
    prefix="/base",
    tags=["基础数据"]
)



@router.get("/get_myself_conf")
async def get_myself_conf(version_name:str,plan_version_id:int,pro_code:str,type:int=1,db: Session = Depends(get_case_db),sysdb:Session = Depends(get_sso_db)):
    '''读取钉钉配置'''
    try:
        ding_conf=db.query(DingDing).filter(DingDing.pro_code==pro_code,DingDing.type==type).first()
        ding_token=''
        if ding_conf!=None: ding_token=ding_conf.token

        '''获取未执行人员列表'''
        user_list = []
        no_run = db.query(MySelfRecord.name).filter(MySelfRecord.plan_version_id == plan_version_id,MySelfRecord.isdelete == 0, MySelfRecord.result.in_(['未执行','未自测'])).group_by(MySelfRecord.name).all()

        if len(no_run) > 0:
            no_run = [run_name.name for run_name in no_run]
            user_list = sysdb.query(User).filter(User.user_name.in_(no_run), User.isdelete == 0).all()


        '''获取未执行数和百分比'''
        run_percen=0
        run_total=db.query(MySelfRecord).filter(MySelfRecord.plan_version_id==plan_version_id,MySelfRecord.result.in_(['PASS','FAIL','无工作量','未执行','未自测']),MySelfRecord.isdelete==0).count()
        no_run_total=db.query(MySelfRecord).filter(MySelfRecord.plan_version_id==plan_version_id,MySelfRecord.isdelete==0,MySelfRecord.result.in_(['未执行','未自测'])).count()
        if run_total>0:
            run_percen=round(100-(no_run_total/run_total*100),2)

        content=f'研发自测提醒：\n- 【版本】[{version_name}](http://gz-qa.inkept.cn/qa_view/#/test/plan/plan_list)\n- 【自测】用例总数{run_total}条，有{no_run_total}条用例未自测；执行总进度是{run_percen}%'.format(version_name,run_total,no_run_total,run_percen)


        return {'code':200,'msg':content,'user_list':user_list,'token':ding_token}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



class SendMysefl(BaseModel):
    token: Optional[str]
    atname: Optional[str]
    no_run_list: Optional[list]
    content:Optional[str]
    pro_code:Optional[str]
    send_name:Optional[str]
    version_name:Optional[str]

@router.post("/send_myself")
async def get_myself_conf(item:SendMysefl,db:Session = Depends(get_case_db)):
    '''发送自测提醒'''
    try:
        #判断发送人
        isall=False
        atname=''
        atname_list=[]
        if item.atname=='@所有人':
            isall=True
        else:
            if len(item.no_run_list)>0:
                atname = '\n- 【开发】'
                for no_run in item.no_run_list:
                    tel=list(no_run.split(','))
                    if '' not in tel:
                        atname_list.append(tel[1])
                        atname+='@{}'.format(tel[1])



        url = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(item.token)
        content = {
            "msgtype": "markdown",
            "markdown": {
                "title": "自测提醒",
                "text": item.content+atname
            },
            "at": {
                "atMobiles": atname_list,
                "isAtAll": isall
            }
        }

        result=requests.post(url, json=content).json()
        if result['errcode']==0:
            #判断更新token
            ding_conf=db.query(DingDing).filter(DingDing.pro_code==item.pro_code,DingDing.type==1).first()
            if ding_conf!=None:
                if ding_conf.token !=item.token:
                    ding_conf.token = item.token
                    db.commit()
            else:
                add_token = {'token':item.token,'pro_code':item.pro_code,'type':1,'daytoken':''}
                token_item = DingDing(**add_token)
                db.add(token_item)
                db.commit()

            #添加发送记录
            add_record = {'send_name':item.send_name,'pro_code': item.pro_code, 'type': 1,'content':item.content+atname,'version_name':item.version_name}
            record_item = DingDingRecord(**add_record)
            db.add(record_item)
            db.commit()
            return {'code':200,'msg':'发送成功！'}
        else:
            return {'code':203,'msg':'钉钉发送失败，具体信息：{}'.format(result['errmsg'])}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/get_dayreport_conf")
async def get_myself_conf(version_name:str,plan_version_id:int,pro_code:str,ticket:str='STXIqosyXMnlFqTrltRgKLqRExkXpfMNOGq',type:int=1,db:Session = Depends(get_case_db),sysdb:Session = Depends(get_sso_db)):
    try:
        '''读取钉钉配置'''
        ding_conf = db.query(DingDing).filter(DingDing.pro_code == pro_code, DingDing.type == type).first()
        ding_token = ''
        jira_panel_url=''
        if ding_conf != None:
            ding_token = ding_conf.daytoken
            jira_panel_url = ding_conf.jira_panel_url

        '''获取版本里非100%的计划，当前100%除外'''
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        plan_list=db.query(TestPlan).filter(TestPlan.plan_version_id==plan_version_id,TestPlan.isdelete==0).order_by(TestPlan.id.desc()).all()
        plan_return_list=[]
        for plan in plan_list:
            if plan.type=='研发自测':
                myself_detail = {'plan_id': plan.id, 'plan_name': plan.name, 'type': plan.type, 'run_percen': 0}
                myself_total = db.query(MySelfRecord).filter(MySelfRecord.plan_id == plan.id, MySelfRecord.isdelete == 0,MySelfRecord.check_result.in_(['PASS','FAIL','未验收'])).count()
                myself_run_total = db.query(MySelfRecord).filter(MySelfRecord.plan_id == plan.id, MySelfRecord.isdelete == 0,MySelfRecord.check_result.in_(['PASS','FAIL'])).count()
                if myself_total==0: continue
                myself_detail['run_percen'] = round(myself_run_total / myself_total * 100, 2)

                # 过滤非当天100%的计划
                if myself_detail['run_percen'] == 100:
                    myself_last_day = db.query(MySelfRecord.check_time).filter(MySelfRecord.plan_id == plan.id,
                                                                  MySelfRecord.check_result.in_(['PASS', 'FAIL']),
                                                                  MySelfRecord.isdelete == 0).order_by(MySelfRecord.check_time.desc()).first()
                    if str(myself_last_day.check_time)[0:10] != today: continue

                plan_return_list.append(myself_detail)


            else:
                #测试计划/生产验证/线上回归
                detail={'plan_id':plan.id,'plan_name':plan.name,'type':plan.type,'run_percen':0}
                plan_total=db.query(PlanCase).filter(PlanCase.plan_id==plan.id,PlanCase.isdelete==0,PlanCase.tester!='').count()
                run_total=db.query(PlanCase).filter(PlanCase.plan_id==plan.id,PlanCase.result.in_(['PASS','FAIL','BLOCK']),PlanCase.isdelete==0).count()
                if plan_total==0: continue  #没有用例则跳过
                detail['run_percen']=round(run_total/plan_total*100,2)

                #过滤非当天100%的计划
                if detail['run_percen']==100:
                    last_day=db.query(PlanCase.run_time).filter(PlanCase.plan_id==plan.id,PlanCase.result.in_(['PASS','FAIL','BLOCK']),PlanCase.isdelete==0).order_by(PlanCase.run_time.desc()).first()
                    if str(last_day.run_time)[0:10]!=today: continue

                plan_return_list.append(detail)


        '''获取jira'''
        jira_clt = jira_com.INKE_JIRA(ticket=ticket)
        jira_id=sysdb.query(Project.jira_id).filter(Project.pro_code==pro_code).first().jira_id
        jql = 'issuetype not in (Epic, Story) and project={} and affectedVersion ={}'.format(jira_id,version_name)
        bug_list = jira_clt.search_issues(jql, maxResults=1000)
        no_resolution_count = 0
        no_resolution_name=[]
        no_check_count=0
        no_check_name=[]
        for bug in bug_list:
            if bug.fields.status:
                #统计未解决
                if bug.fields.status.name in ('开放','InProcess','Reopened'):
                    no_resolution_count+=1
                    if bug.fields.assignee: no_resolution_name.append(bug.fields.assignee.displayName)

                #统计已解决
                elif bug.fields.status.name =='已解决':
                    no_check_count+=1
                    if bug.fields.reporter: no_check_name.append(bug.fields.reporter.displayName)

        #追加计划进度内容
        plan_content=''
        for plan in plan_return_list:
            plan_content+='\n- '+'【{}】测试进度{}%'.format(plan['plan_name'],plan['run_percen'])


        #追加jira内容
        resolution_name=''
        if len(no_resolution_name)>0:
            resolution_name='[{}]()个，{}'.format(no_resolution_count,','.join(set(no_resolution_name)))
        else:
            resolution_name='[0]()个'

        check_name=''
        if len(no_check_name)>0:
            check_name='[{}]()个，{}'.format(no_check_count,','.join(set(no_check_name)))
        else:
            check_name='[0]()个'


        content=f'{today}测试进度提醒：\n- 【版本】{version_name}{plan_content}\n- 【未解决Bug】{resolution_name}\n- 【未验证Bug】{check_name}\n- 【今日阻塞】\n- 【明日计划】'.format(today,version_name,plan_content,resolution_name,check_name)
        return {'code':200,'msg':content,'token':ding_token,'jira_panel_url':jira_panel_url}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




class SendDayReport(BaseModel):
    token: Optional[str]
    content:Optional[str]
    pro_code:Optional[str]
    send_name:Optional[str]
    version_name:Optional[str]
    jira_panel_url:Optional[str]


@router.post("/send_dayreport")
async def send_dayreport(item:SendDayReport,db:Session = Depends(get_case_db)):
    '''发送日报'''
    try:
        item.content=item.content.replace('()个','({})个'.format(item.jira_panel_url))
        url = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(item.token)
        content = {
            "msgtype": "markdown",
            "markdown": {
                "title": "版本日报",
                "text": item.content
            },
            "at": {
                "atMobiles": [],
                "isAtAll": False
            }
        }

        result=requests.post(url, json=content).json()
        if result['errcode']==0:
            #判断更新token
            ding_conf=db.query(DingDing).filter(DingDing.pro_code==item.pro_code,DingDing.type==1).first()
            if ding_conf!=None:
                if ding_conf.daytoken !=item.token: ding_conf.daytoken = item.token
                if ding_conf.jira_panel_url !=item.jira_panel_url: ding_conf.jira_panel_url=item.jira_panel_url
                db.commit()
            else:
                add_token = {'token':'','daytoken':item.token,'pro_code':item.pro_code,'type':1,'jira_panel_url':item.jira_panel_url}
                token_item = DingDing(**add_token)
                db.add(token_item)
                db.commit()

            #添加发送记录
            add_record = {'send_name':item.send_name,'pro_code': item.pro_code, 'type': 1,'content':item.content,'version_name':item.version_name}
            record_item = DingDingRecord(**add_record)
            db.add(record_item)
            db.commit()
            return {'code':200,'msg':'发送成功！'}
        else:
            return {'code':203,'msg':'钉钉发送失败，具体信息：{}'.format(result['errmsg'])}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





