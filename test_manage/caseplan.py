from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import plan_schemas
from qa_dal.database import get_case_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from sqlalchemy import or_,func,and_
import common.jira_base as jira_com


from qa_dal import qa_uitls
from qa_dal.models import TestPlan,Version,TestCase,MySelfRecord,Demand,PlanCase,User,PlanVersion,CaseIndex
import datetime
import jsonpath

router = APIRouter(
    prefix="/tm/caseplan",
    tags=["测试管理-测试计划"]
)


@router.get("/list")
async def search_plan_list(pro_code:str='',keyvalue:str='',page_num:int=1,page_size:int=10,db:Session=Depends(get_case_db)):

    try:
        '''搜索计划列表'''
        sql_param_list = [TestPlan.pro_code == pro_code, TestPlan.isdelete == 0]  # 基础搜索条件

        #获取符合条件计划
        plan_list=db.query(TestPlan).filter(*sql_param_list).order_by(TestPlan.id.desc()).all()
        plan_json ={}

        for plan in plan_list:
            plan_info = plan.to_json()
            plan_info['run_name']=[]
            plan_info['join_plan_id']=eval(plan.join_plan_id)
            plan_info['state']='未开始'
            plan_info['start_time']=''
            plan_info['end_time']=''
            plan_info['tester_summary']=[]
            plan_info['myself_summary']=[]

            # 更新开始、结束时间、状态、执行人
            tester_list = db.query(PlanCase.tester).filter(PlanCase.plan_id==plan.id,PlanCase.isdelete==0).group_by(PlanCase.tester).all()
            tester_list = [tester.tester for tester in tester_list]
            dev_list = db.query(MySelfRecord.name).filter(MySelfRecord.plan_id==plan.id,MySelfRecord.isdelete==0).group_by(MySelfRecord.name).all()
            dev_list=[dev.name for dev in dev_list]
            plan_info['run_name']=tester_list+dev_list

            # 计算统计
            if plan.type in ('生产验证', '发布性验证'):
                plan_info['tester_summary'] = test_summary(plan.id, db)

                #获取开始时间
                start_time=db.query(PlanCase.run_time).filter(PlanCase.isdelete==0,PlanCase.plan_id==plan.id,PlanCase.run_time!='').order_by(PlanCase.run_time.asc()).first()
                if start_time!=None:
                    plan_info['start_time']=str(start_time.run_time).replace('T',' ')
                    plan_info['state']='进行中'

                #获取状态
                run_count=db.query(PlanCase).filter(PlanCase.result.not_in(['PASS','FAIL','BLOCK']),PlanCase.isdelete==0,PlanCase.plan_id==plan.id).count()
                total_run_count=db.query(PlanCase).filter(PlanCase.isdelete==0,PlanCase.plan_id==plan.id).count()
                if run_count==0 and total_run_count>0:
                    plan_info['state']='已完成'
                    end_time = db.query(PlanCase.run_time).filter(PlanCase.isdelete==0,PlanCase.plan_id==plan.id,PlanCase.run_time!='').order_by(PlanCase.run_time.asc()).first()
                    if end_time != None: plan_info['end_time'] = str(end_time.run_time).replace('T',' ')

            elif plan.type=='研发自测':
                plan_info['tester_summary'] = myselfsummary([plan.id], db)['check']
                plan_info['myself_summary'] = myselfsummary([plan.id], db)['myself']

                #获取开始时间
                start_time = db.query(MySelfRecord.check_time).filter(MySelfRecord.isdelete == 0,MySelfRecord.plan_id == plan.id,MySelfRecord.check_time!='').order_by(MySelfRecord.check_time.asc()).first()
                if start_time != None:
                    plan_info['start_time'] = str(start_time.check_time).replace('T',' ')
                    plan_info['state'] = '进行中'

                #获取状态和结束时间
                run_count=db.query(MySelfRecord).filter(MySelfRecord.check_result.not_in(['PASS','FAIL','无工作量']), MySelfRecord.isdelete == 0,MySelfRecord.plan_id == plan.id).count()
                total_run_count=db.query(MySelfRecord).filter(MySelfRecord.isdelete == 0,MySelfRecord.plan_id == plan.id).count()
                if run_count==0 and total_run_count>0:
                    plan_info['state']='已完成'
                    end_time=db.query(MySelfRecord.check_time).filter(MySelfRecord.isdelete == 0,MySelfRecord.plan_id == plan.id,MySelfRecord.check_time!='').order_by(MySelfRecord.check_time.desc()).first()
                    if end_time!=None: plan_info['end_time']=str(end_time.check_time).replace('T',' ')

            else:
                join_plan_id=list(plan.join_plan_id)
                join_myself_summary={}
                if len(join_plan_id)>0:
                    join_myself_summary=myselfsummary([join_plan_id], db)['check']
                plan_info['tester_summary'] = test_summary(plan.id, db,1.5,'-1',join_myself_summary)


                # 获取开始时间
                start_time = db.query(PlanCase.run_time).filter(PlanCase.isdelete == 0, PlanCase.plan_id == plan.id,
                                                                PlanCase.run_time != '').order_by(PlanCase.run_time.asc()).first()

                if start_time != None:
                    plan_info['start_time'] = str(start_time.run_time).replace('T', ' ')
                    plan_info['state'] = '进行中'

                # 获取状态
                run_count = db.query(PlanCase).filter(PlanCase.result.not_in(['PASS', 'FAIL', 'BLOCK']),
                                                      PlanCase.isdelete == 0, PlanCase.plan_id == plan.id).count()
                total_run_count = db.query(PlanCase).filter(PlanCase.isdelete == 0, PlanCase.plan_id == plan.id).count()
                if run_count == 0 and total_run_count > 0:
                    plan_info['state'] = '已完成'
                    end_time = db.query(PlanCase.run_time).filter(PlanCase.isdelete == 0, PlanCase.plan_id == plan.id,
                                                                  PlanCase.run_time != '').order_by(
                        PlanCase.run_time.asc()).first()
                    if end_time != None: plan_info['end_time'] = str(end_time.run_time).replace('T', ' ')

            #过滤条件
            if len(keyvalue)>0:
                if_kekvalue=[keyvalue not in plan_info['name'],keyvalue not in plan_info['run_name'],plan_info['type']!=keyvalue,plan_info['state']!=keyvalue]
                if False not in if_kekvalue: continue


            if plan.plan_version_id in plan_json.keys():
                plan_json[plan.plan_version_id]['plan_list'].append(plan_info)
                plan_json[plan.plan_version_id]['version_summary']['total']+=plan_info['tester_summary']['total']
                plan_json[plan.plan_version_id]['version_summary']['pass'] += plan_info['tester_summary']['pass']
                plan_json[plan.plan_version_id]['version_summary']['fail'] += plan_info['tester_summary']['fail']
                plan_json[plan.plan_version_id]['version_summary']['norun'] += plan_info['tester_summary']['norun']
                plan_json[plan.plan_version_id]['version_summary']['block'] += plan_info['tester_summary']['block']

            else:
                plan_json[plan.plan_version_id]={'plan_list':[plan_info],'version_summary':{'total': 0, 'pass': 0, 'fail': 0,'block':0,'norun': 0, 'pass_percen': 0, 'fail_percen': 0,'block_percen':0,'norun_percen': 0, 'pass_width': '0px', 'fail_width': '0px', 'norun_width': '0px','block_width':'0px'}}
                plan_json[plan.plan_version_id]['version_summary']['total'] += plan_info['tester_summary']['total']
                plan_json[plan.plan_version_id]['version_summary']['pass'] += plan_info['tester_summary']['pass']
                plan_json[plan.plan_version_id]['version_summary']['fail'] += plan_info['tester_summary']['fail']
                plan_json[plan.plan_version_id]['version_summary']['norun'] += plan_info['tester_summary']['norun']
                plan_json[plan.plan_version_id]['version_summary']['block'] += plan_info['tester_summary']['block']

        #获取所有版本
        version_list=db.query(PlanVersion).filter(PlanVersion.pro_code==pro_code,PlanVersion.isdelete==0).order_by(PlanVersion.id.desc()).all()


        version_result_list=[]
        for version in version_list:
            version_info = version.to_json()
            version_info['plan_list']=[]
            version_info['version_summary']={'total': 0, 'pass': 0, 'fail': 0,'block':0,'norun': 0, 'pass_percen': 0, 'fail_percen': 0,'block_percen':0,'norun_percen': 0, 'pass_width': '0px', 'fail_width': '0px', 'norun_width': '0px','block_width':'0px'}
            if version.id in plan_json.keys():
                version_info['plan_list']=plan_json[version.id]['plan_list']
                version_info['version_summary'] =plan_json[version.id]['version_summary']

                #计算版本统计
                version_total=version_info['version_summary']['total']

                if version_total>0:
                    version_info['version_summary']['pass_percen'] = round(version_info['version_summary']['pass'] / version_total * 100)
                    version_info['version_summary']['fail_percen'] = round(version_info['version_summary']['fail'] / version_total * 100)
                    version_info['version_summary']['norun_percen'] = round(version_info['version_summary']['norun'] / version_total * 100)
                    version_info['version_summary']['block_percen'] = round(version_info['version_summary']['block'] / version_total * 100)


                    version_info['version_summary']['pass_width'] = str(round(version_info['version_summary']['pass_percen'] * 1.5)) + 'px'
                    version_info['version_summary']['fail_width'] = str(round(version_info['version_summary']['fail_percen'] * 1.5)) + 'px'
                    version_info['version_summary']['norun_width'] = str(round(version_info['version_summary']['norun_percen'] * 1.5)) + 'px'
                    version_info['version_summary']['block_width'] = str(round(version_info['version_summary']['block_percen'] * 1.5)) + 'px'


                if len(keyvalue)>0: version_result_list.append(version_info)

            if len(keyvalue)==0: version_result_list.append(version_info)

        return qa_uitls.page_info(version_result_list, page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/plancase_list")
async def plancase_list(plan_id:int=0,run_name:str='-1',state:str='-1',case_level:str='-1',id_path:str='',page_num:int=1,page_size:int=50,db:Session=Depends(get_case_db)):
    '''执行测试、线上验证'''
    try:
        sql_param=[PlanCase.isdelete==0,PlanCase.plan_id==plan_id,CaseIndex.isdelete==0]

        type_param={'activity':0,'version':1,'release':2}
        if id_path in type_param.keys():
            sql_param.append(TestCase.case_type==type_param[id_path])
        if id_path not in type_param.keys() and id_path not in ('plan','',None):
            sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))

        if case_level!='-1': sql_param.append(TestCase.case_level==case_level)

        state_json={'norun':PlanCase.result.in_(['',None,'未执行']),'noname':PlanCase.tester.in_(['',None]),'PASS':PlanCase.result=='PASS','FAIL':PlanCase.result=='FAIL','BLOCK':PlanCase.result=='BLOCK'}

        if state in state_json.keys(): sql_param.append(state_json[state])

        if run_name not in ('-1',-1):sql_param.append(PlanCase.tester==run_name)

        plancase_list = db.query(TestCase.case_name,TestCase.isrecovery,TestCase.isdelete,TestCase.case_type,TestCase.id, TestCase.front_info, TestCase.case_step,
                                 TestCase.case_result, TestCase.case_level, PlanCase.id.label('plancase_id'),
                                 PlanCase.tester,PlanCase.result,PlanCase.plan_id,PlanCase.result_remark,
                                 PlanCase.case_id,PlanCase.bug,CaseIndex.name).join(TestCase, TestCase.id == PlanCase.case_id).join(CaseIndex,CaseIndex.id_path==TestCase.index_id)\
            .filter(*sql_param).order_by(CaseIndex.sort.asc(),TestCase.sort_num.asc(), TestCase.sort_id.desc()).all()

        result=qa_uitls.page_info(plancase_list, page_num, page_size)
        result['noname']=db.query(PlanCase).filter(PlanCase.plan_id==plan_id,PlanCase.isdelete==0,PlanCase.tester.in_(['',None])).count()

        #统计进度
        summary_count={'total':len(result['msg']),'PASS':0,'FAIL':0,'BLOCK':0,'NORUN':0,'pass_percen':0,'fail_percen':0,'block_percen':0,'pass_width':0,'fail_width':0,'block_width':0}
        tester_total=summary_count['total']

        for case in result['msg']:
            if case.result in summary_count.keys(): summary_count[case.result]+=1
            if case.result in (None,'','未执行'): summary_count['NORUN']+=1


        if tester_total>0:
            summary_count['pass_percen'] = round(summary_count['PASS'] / tester_total * 100)
            summary_count['fail_percen'] = round(summary_count['FAIL'] / tester_total * 100)
            summary_count['block_percen'] = round(summary_count['BLOCK'] / tester_total * 100)

        summary_count['pass_width'] = str(round(summary_count['pass_percen'] * 1.5)) + 'px'
        summary_count['fail_width'] = str(round(summary_count['fail_percen'] * 1.5)) + 'px'
        summary_count['block_width'] = str(round(summary_count['block_percen'] * 1.5)) + 'px'

        result['tester_summary']=summary_count

        return result

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/testercaselist")
async def testercaselist(plan_id:int=0,state:str='-1',run_name:str='-1',id_path:str='',case_level:str='-1',page_num:int=1,page_size:int=50,db:Session=Depends(get_case_db),sysdb:Session=Depends(get_sso_db)):
    try:
        #获取run_name身份
        # 获取用例列表
        join_case_json = {}
        base_case_list = []

        join_myself_list = db.query(MySelfRecord).filter(MySelfRecord.plan_id == plan_id,
                                                         MySelfRecord.isdelete == 0).all()

        # 获取自测结果、测试结果、研发评论、测试人员/统计
        for myself in join_myself_list:
            if myself.case_id not in base_case_list: base_case_list.append(myself.case_id)

            # 过滤条件
            if run_name != '-1' and myself.name != run_name and myself.check_name != run_name: continue
            if state != '-1' and state in ('PASS', 'FAIL') and myself.check_result != state: continue
            if state != '-1' and state in ('待沟通', '无工作量', '未自测') and myself.result != state: continue
            if state != '-1' and state == '未执行' and myself.check_result != '未验收': continue
            if state == 'BLOCK': continue

            if myself.case_id in join_case_json.keys():
                join_case_json[myself.case_id]['dev_record'].append({'name': myself.name, 'result': myself.result})
                join_case_json[myself.case_id]['test_record'].append(
                    {'name': myself.name, 'result': myself.check_result})

                if len(myself.result_remark) > 0:
                    join_case_json[myself.case_id]['dev_remark'].append(
                        {'name': myself.name, 'remark': myself.result_remark})

                # 计算验收结果统计
                if myself.check_result in join_case_json[myself.case_id]['summary_count'].keys():
                    join_case_json[myself.case_id]['summary_count']['total'] += 1
                    join_case_json[myself.case_id]['summary_count'][myself.check_result] += 1

            else:
                join_case_json[myself.case_id] = {'dev_record': [{'name': myself.name, 'result': myself.result}],
                                                  'test_record': [{'name': myself.name, 'result': myself.check_result}],
                                                  'dev_remark': [],
                                                  'tester': myself.check_name, 'plan_id': myself.plan_id,
                                                  'summary_count': {'total': 0, 'PASS': 0, 'FAIL': 0,
                                                                    '未验收': 0}}

                if len(myself.result_remark) > 0:
                    join_case_json[myself.case_id]['dev_remark'].append(
                        {'name': myself.name, 'remark': myself.result_remark})

                # 计算统计
                if myself.check_result in join_case_json[myself.case_id]['summary_count'].keys():
                    join_case_json[myself.case_id]['summary_count']['total'] += 1
                    join_case_json[myself.case_id]['summary_count'][myself.check_result] += 1

        sql_param = [PlanCase.plan_id == plan_id, PlanCase.isdelete == 0]

        # 判断条件
        if case_level != '-1': sql_param.append(TestCase.case_level == case_level)

        type_param = {'activity': 0, 'version': 1, 'release': 2}

        if id_path in type_param.keys():
            sql_param.append(TestCase.case_type == type_param[id_path])
        if id_path not in type_param.keys() and id_path not in ('plan', '', None):
            sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))

        plan_case_list = db.query(TestCase.case_name, TestCase.isrecovery, TestCase.isdelete, TestCase.case_type,
                                  TestCase.id, TestCase.front_info, TestCase.case_step,
                                  TestCase.case_result, TestCase.case_level, PlanCase.id.label('plancase_id'),
                                  PlanCase.plan_type,
                                  PlanCase.tester, PlanCase.result, PlanCase.plan_id, PlanCase.result_remark,
                                  PlanCase.case_id, PlanCase.bug, CaseIndex.name, CaseIndex.level).join(TestCase,
                                                                                                        TestCase.id == PlanCase.case_id).join(
            CaseIndex, CaseIndex.id_path == TestCase.index_id).filter(*sql_param).order_by(CaseIndex.sort.asc(),
                                                                                           TestCase.sort_num.asc(),
                                                                                           TestCase.sort_id.desc()).all()

        join_case_list = []
        summary_count = {'total': 0, 'NORUN': 0, 'PASS': 0, 'FAIL': 0,'pass_percen': 0, 'fail_percen': 0,'pass_width': 0, 'fail_width': 0}

        noname_case_list = []

        for plancase in plan_case_list:

            plancase_item = {
                'case_name': plancase.case_name,
                'isrecovery': plancase.isrecovery,
                'isdelete': plancase.isdelete,
                'case_type': '',
                'id': plancase.id,
                'front_info': plancase.front_info, 'case_step': plancase.case_step, 'case_result': plancase.case_result,
                'case_level': plancase.case_level, 'plancase_id': plancase.plancase_id,
                'tester': plancase.tester, 'result': plancase.result, 'plan_id': plancase.plan_id,
                'result_remark': plancase.result_remark, 'case_id': plancase.case_id,
                'bug': plancase.bug, 'name': plancase.name, 'dev_result': [], 'tester_result': [],
                'level': plancase.level, 'plan_type': plancase.plan_type, 'dev_remark': []
            }

            # 判断是否自测用例
            if plancase.case_id in join_case_json.keys():
                plancase_item['plan_type'] = '研发自测'
                plancase_item['dev_result'] = join_case_json[plancase.id]['dev_record']
                plancase_item['tester_result'] = join_case_json[plancase.id]['test_record']
                plancase_item['tester'] = join_case_json[plancase.id]['tester']
                plancase_item['dev_remark'] = join_case_json[plancase.id]['dev_remark']

                # 累计总数
                summary_count['total'] += join_case_json[plancase.id]['summary_count']['total']
                summary_count['NORUN'] += join_case_json[plancase.id]['summary_count']['未验收']
                summary_count['PASS'] += join_case_json[plancase.id]['summary_count']['PASS']
                summary_count['FAIL'] += join_case_json[plancase.id]['summary_count']['FAIL']
                join_case_list.append(plancase_item)

            else:
                if plancase.case_id in base_case_list: continue
                if run_name != '-1' and plancase.tester != run_name: continue
                if state != '-1' and state in ('PASS', 'FAIL', 'BLOCK') and plancase.result != state: continue
                if state != '-1' and state in ('无工作量', '未自测', '待沟通'): continue

                plancase_item['plan_type'] = '研发自测'
                join_case_list.append(plancase_item)

            if plancase_item['tester'] in ('', None, '未分配'):
                noname_case_list.append(plancase_item)

            if len(plancase_item['dev_result']) == 0:
                noname_case_list.append(plancase_item)

        if run_name == '-1' and state == 'noname':
            join_case_list = noname_case_list

        result = qa_uitls.page_info(join_case_list, page_num, page_size)
        result['noname_count'] = len(noname_case_list)

        # 计算通过率
        tester_total = summary_count['total']
        if tester_total > 0:
            summary_count['pass_percen'] = round(summary_count['PASS'] / tester_total * 100)
            summary_count['fail_percen'] = round(summary_count['FAIL'] / tester_total * 100)

            summary_count['pass_width'] = str(round(summary_count['pass_percen'] * 1.5)) + 'px'
            summary_count['fail_width'] = str(round(summary_count['fail_percen'] * 1.5)) + 'px'

        result['summary_count'] = summary_count

        return result

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/devcaselist")
async def devcaselist(plan_id:int=0,state:str='-1',run_name:str='-1',id_path:str='',case_level:str='-1',page_num:int=1,page_size:int=50,db:Session=Depends(get_case_db)):
    try:
        # 获取用例列表
        join_case_json = {}
        base_case_list = []

        join_myself_list = db.query(MySelfRecord).filter(MySelfRecord.plan_id==plan_id,MySelfRecord.isdelete == 0).all()

        # 获取自测结果、测试结果、研发评论、测试人员/统计
        for myself in join_myself_list:
            if myself.case_id not in base_case_list: base_case_list.append(myself.case_id)

            # 过滤条件
            if run_name != '-1' and myself.name != run_name and myself.check_name != run_name: continue
            if state != '-1' and state in ('PASS', 'FAIL') and myself.check_result != state: continue
            if state != '-1' and state in ('待沟通', '无工作量', '未自测') and myself.result != state: continue
            if state != '-1' and state == '未执行' and myself.check_result != '未验收': continue
            if state == 'BLOCK': continue

            if myself.case_id in join_case_json.keys():
                join_case_json[myself.case_id]['dev_record'].append({'name': myself.name, 'result': myself.result})
                join_case_json[myself.case_id]['test_record'].append({'name': myself.name, 'result': myself.check_result})

                if len(myself.result_remark) > 0:
                    join_case_json[myself.case_id]['dev_remark'].append({'name': myself.name, 'remark': myself.result_remark})

                # 计算自测结果统计
                if myself.result in join_case_json[myself.case_id]['summary_count'].keys():
                    join_case_json[myself.case_id]['summary_count']['total'] += 1
                    join_case_json[myself.case_id]['summary_count'][myself.result] += 1

            else:
                join_case_json[myself.case_id] = {'dev_record': [{'name': myself.name, 'result': myself.result}],
                                                  'test_record': [{'name': myself.name, 'result': myself.check_result}],
                                                  'dev_remark': [],
                                                  'tester': myself.check_name, 'plan_id': myself.plan_id,
                                                  'summary_count': {'total': 0,'已自测':0,'待沟通':0,'未自测':0,'无工作量':0}}

                if len(myself.result_remark) > 0:
                    join_case_json[myself.case_id]['dev_remark'].append(
                        {'name': myself.name, 'remark': myself.result_remark})

                # 计算统计
                if myself.result in join_case_json[myself.case_id]['summary_count'].keys():
                    join_case_json[myself.case_id]['summary_count']['total'] += 1
                    join_case_json[myself.case_id]['summary_count'][myself.result] += 1

        sql_param = [PlanCase.plan_id==plan_id, PlanCase.isdelete == 0]

        # 判断条件
        if case_level != '-1': sql_param.append(TestCase.case_level == case_level)

        type_param = {'activity': 0, 'version': 1, 'release': 2}

        if id_path in type_param.keys():
            sql_param.append(TestCase.case_type == type_param[id_path])
        if id_path not in type_param.keys() and id_path not in ('plan', '', None):
            sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))

        plan_case_list = db.query(TestCase.case_name, TestCase.isrecovery, TestCase.isdelete, TestCase.case_type,
                                  TestCase.id, TestCase.front_info, TestCase.case_step,
                                  TestCase.case_result, TestCase.case_level, PlanCase.id.label('plancase_id'),
                                  PlanCase.plan_type,
                                  PlanCase.tester, PlanCase.result, PlanCase.plan_id, PlanCase.result_remark,
                                  PlanCase.case_id, PlanCase.bug, CaseIndex.name, CaseIndex.level).join(TestCase,
                                                                                                        TestCase.id == PlanCase.case_id).join(
            CaseIndex, CaseIndex.id_path == TestCase.index_id).filter(*sql_param).order_by(CaseIndex.sort.asc(),
                                                                                           TestCase.sort_num.asc(),
                                                                                           TestCase.sort_id.desc()).all()



        join_case_list = []
        summary_count = {'total': 0, 'NORUN': 0, 'PASS': 0, 'FAIL': 0, 'NOWORK': 0, 'pass_percen': 0, 'fail_percen': 0,
                         'nowork_percen': 0,'pass_width': 0, 'fail_width': 0, 'nowork_width': 0}

        noname_case_list = []

        for plancase in plan_case_list:

            plancase_item = {
                'case_name': plancase.case_name,
                'isrecovery': plancase.isrecovery,
                'isdelete': plancase.isdelete,
                'case_type': '',
                'id': plancase.id,
                'front_info': plancase.front_info, 'case_step': plancase.case_step, 'case_result': plancase.case_result,
                'case_level': plancase.case_level, 'plancase_id': plancase.plancase_id,
                'tester': plancase.tester, 'result': plancase.result, 'plan_id': plancase.plan_id,
                'result_remark': plancase.result_remark, 'case_id': plancase.case_id,
                'bug': plancase.bug, 'name': plancase.name, 'dev_result': [], 'tester_result': [],
                'level': plancase.level, 'plan_type': plancase.plan_type, 'dev_remark': []
            }

            # 判断是否自测用例
            if plancase.case_id in join_case_json.keys():
                plancase_item['plan_type'] = '研发自测'
                plancase_item['dev_result'] = join_case_json[plancase.id]['dev_record']
                plancase_item['tester_result'] = join_case_json[plancase.id]['test_record']
                plancase_item['tester'] = join_case_json[plancase.id]['tester']
                plancase_item['dev_remark'] = join_case_json[plancase.id]['dev_remark']

                # 累计总数
                summary_count['total'] += join_case_json[plancase.id]['summary_count']['total']
                summary_count['NORUN'] += join_case_json[plancase.id]['summary_count']['未自测']
                summary_count['PASS'] += join_case_json[plancase.id]['summary_count']['已自测']
                summary_count['FAIL'] += join_case_json[plancase.id]['summary_count']['待沟通']
                summary_count['NOWORK'] += join_case_json[plancase.id]['summary_count']['无工作量']
                join_case_list.append(plancase_item)

            else:
                if plancase.case_id in base_case_list: continue
                if run_name != '-1' and plancase.tester != run_name: continue
                if state != '-1' and state in ('PASS', 'FAIL', 'BLOCK') and plancase.result != state: continue
                if state != '-1' and state in ('无工作量', '未自测', '待沟通'): continue

                plancase_item['plan_type'] = '研发自测'
                join_case_list.append(plancase_item)


            if plancase_item['tester'] in ('',None,'未分配'):
                noname_case_list.append(plancase_item)

            if len(plancase_item['dev_result'])==0:
                noname_case_list.append(plancase_item)

        if run_name=='-1' and state=='noname':
            join_case_list=noname_case_list

        result = qa_uitls.page_info(join_case_list, page_num, page_size)
        result['noname_count'] = len(noname_case_list)

        # 计算通过率
        tester_total = summary_count['total']
        if tester_total > 0:
            summary_count['pass_percen'] = round(summary_count['PASS'] / tester_total * 100)
            summary_count['fail_percen'] = round(summary_count['FAIL'] / tester_total * 100)
            summary_count['nowork_percen'] = round(summary_count['NOWORK'] / tester_total * 100)

            summary_count['pass_width'] = str(round(summary_count['pass_percen'] * 1.5)) + 'px'
            summary_count['fail_width'] = str(round(summary_count['fail_percen'] * 1.5)) + 'px'
            summary_count['nowork_width'] = str(round(summary_count['nowork_percen'] * 1.5)) + 'px'

        result['summary_count'] = summary_count


        return result
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/df_dev")
async def df_dev(plan_id:int=0,case_id_list:str='',db:Session=Depends(get_case_db)):
    '''获取交集的开发人员'''
    try:
        dev_list=db.query(MySelfRecord).filter(MySelfRecord.case_id.in_([case_id_list]),MySelfRecord.isdelete==0,MySelfRecord.plan_id==plan_id).all()
        dev_name=[dev.name for dev in dev_list]
        return {'code':200,'msg':list(set(dev_name))}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/dev_runname")
async def dev_runname(item:plan_schemas.DevRunName,db:Session=Depends(get_case_db)):
    '''批量分配开发人员'''
    try:
        #获取分配记录表
        record_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id==item.plan_id,MySelfRecord.case_id.in_(item.case_id_list),MySelfRecord.isdelete==0).all()

        record_json={}
        for record in record_list:
            if record.case_id in record_json:
                record_json[record.case_id].append(record.name)
            else:
                record_json[record.case_id]=[record.name]


        #获取要添加人员
        add_json=[]
        del_json={}
        for case_id in item.case_id_list:
            if case_id in record_json.keys():
                add_set=set(item.name_list).difference(set(record_json[case_id]))    #对比是否有新加的名字

                if len(add_set)>0:
                    add_json += [{'case_id': case_id, 'plan_id': item.plan_id, 'name': dev_name, 'pro_code': item.pro_code,'plan_version_id':item.plan_version_id}
                                 for dev_name in add_set]

                del_set = set(record_json[case_id]).difference(item.name_list)     #对比要删除的名字
                if len(del_set)>0:
                    for del_name in del_set:
                        if case_id in del_json.keys():
                            del_json[case_id].append(del_name)
                        else:
                            del_json[case_id]=[del_name]
            else:
                add_json+=[{'case_id':case_id,'plan_id':item.plan_id,'name':dev_name,'pro_code':item.pro_code,'plan_version_id':item.plan_version_id} for dev_name in item.name_list]


        #添加数据
        for name_item in add_json:

            #获取测试人员名称
            plancase= db.query(PlanCase).filter(PlanCase.plan_id==name_item['plan_id'],PlanCase.case_id==name_item['case_id'],PlanCase.isdelete==0).first()
            if plancase!=None:
                if plancase.tester not in ('',None):
                    name_item['check_name']=plancase.tester

            db_item = MySelfRecord(**name_item)
            db.add(db_item)
        db.commit()

        # 删除数据
        for rc in record_list:
            if rc.case_id not in del_json.keys(): continue
            if rc.name not in del_json[rc.case_id]: continue
            rc.isdelete = 1
        db.commit()

        return {'code':200,'msg':'操作成功！','add':add_json,'del':del_json}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/plan_add_case")
async def plan_add_case(item:plan_schemas.AddCase,db:Session=Depends(get_case_db)):
    '''测试计划加入用例'''
    try:
        plan_case=db.query(PlanCase).filter(PlanCase.plan_id==item.plan_id,PlanCase.isdelete==0).all()
        plan_case_id=[case.case_id for case in plan_case]

        case_list = db.query(TestCase.id).filter(TestCase.id.in_(item.case_id_list),TestCase.isdelete==0,TestCase.isrecovery==0).all()

        #新增用例
        if len(case_list)>0:
            for case in case_list:
                if case.id in plan_case_id: continue
                case_item={'pro_code':item.pro_code,'plan_id':item.plan_id,'case_id':case.id,'plan_type':item.plan_type,'plan_version_id':item.plan_version_id,'tester':item.tester}
                db_item = PlanCase(**case_item)
                db.add(db_item)
            db.commit()

        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/dev_run")
async def dev_run(item:plan_schemas.DevRun,db:Session=Depends(get_case_db)):
    '''
    批量执行自测用例
    '''
    try:
        record_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id==item.plan_id,MySelfRecord.case_id.in_(item.case_id_list),MySelfRecord.name==item.run_name,MySelfRecord.isdelete==0).all()
        now_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if len(record_list)>0:
            for rc in record_list:
                rc.result=item.result
                rc.run_time = now_time
            db.commit()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/tester_myselfrun")
async def tester_myselfrun(item:plan_schemas.TesterMyselfRun,db:Session=Depends(get_case_db),sysdb:Session=Depends(get_sso_db)):
    '''测试批量验收自测用例'''

    #根据职能获取开发名称
    try:
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        run_name_list=[]
        # 判断是否为全部
        if item.pro_fun=='full':
            full_record_list = db.query(MySelfRecord).filter(MySelfRecord.plan_id == item.plan_id,MySelfRecord.case_id.in_(item.case_id_list),MySelfRecord.isdelete == 0).all()
            if len(full_record_list) > 0:
                for rc in full_record_list:
                    plan_case = db.query(PlanCase).filter(PlanCase.plan_id == rc.plan_id, PlanCase.case_id == rc.case_id,PlanCase.isdelete == 0).first()
                    #判断是否未分配测试人员
                    if plan_case!=None:
                        run_name_list.append(plan_case.tester)
                        if plan_case.tester == item.run_name:
                            rc.check_result = item.result
                            rc.check_time = now_time
                            rc.check_name = item.run_name
                db.commit()

        else:
            user_name_list=sysdb.query(User).filter(User.pro_fun==item.pro_fun,User.isdelete==0,User.pro_code_list.like('%{}%'.format(item.pro_code))).all()
            if len(user_name_list)==0: return {'code':'203','msg':'勾选用例的开发职能不匹配！'}

            user_name=[user.user_name for user in user_name_list]
            record_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id==item.plan_id,MySelfRecord.case_id.in_(item.case_id_list),MySelfRecord.name.in_(user_name),MySelfRecord.isdelete==0).all()

            if len(record_list)>0:
                for rc in record_list:
                    plan_case = db.query(PlanCase).filter(PlanCase.plan_id == rc.plan_id, PlanCase.case_id == rc.case_id,PlanCase.isdelete == 0).first()
                    #判断是否未分配测试人员
                    if rc.check_name==item.run_name and plan_case!=None:
                        run_name_list.append(plan_case.tester)
                        if plan_case.tester == item.run_name:
                            rc.check_result = item.result
                            rc.check_time = now_time
                            rc.check_name = item.run_name

            db.commit()

        if item.run_name not in run_name_list: return {'code':201,'msg':'非本人操作或未分配!'}
        if item.run_name in run_name_list:
            if len(set(run_name_list))>1: return {'code':200,'msg':'部分用例操作成功!'}

        return {'code': 200, 'msg': '操作成功！',}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/tester_myself_runname")
async def tester_myself_runname(item:plan_schemas.TesterRunName,db:Session=Depends(get_case_db)):
    '''批量分配自测测试人员'''
    try:
        #修改计划用例
        plan_case_list=db.query(PlanCase).filter(PlanCase.id.in_(item.plancase_id_list),PlanCase.isdelete==0).all()
        if len(plan_case_list)>0:
            for case in plan_case_list:
                if case.tester!=item.tester:
                    case.tester = item.tester
                    case.result = ''
                    case.result_remark = ''
                    case.run_time = None
            db.commit()


        #修改自测记录
        record_list= db.query(MySelfRecord).filter(MySelfRecord.plan_id==item.plan_id,MySelfRecord.case_id.in_(item.case_id_list),MySelfRecord.isdelete==0).all()
        if len(record_list)>0:
            for rc in record_list:
                if rc.check_name!=item.tester:
                    rc.check_name = item.tester
                    rc.check_result = '未验收'
                    rc.check_remark = ''
                    rc.check_time = None
            db.commit()


        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/tester_run")
async def tester_run(item:plan_schemas.TesterRun,db:Session=Depends(get_case_db)):
    '''批量执行测试计划/线上验证/发布性计划'''
    try:
        plan_case_list=db.query(PlanCase).filter(PlanCase.id.in_(item.plancase_id_list),PlanCase.isdelete==0,PlanCase.tester==item.tester).all()

        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if len(plan_case_list)>0:
            for case in plan_case_list:
                case.result = item.result
                case.run_time = now_time
            db.commit()
        else:
            return {'code':201,'msg':'非本人执行！'}

        if len(plan_case_list)!=len(item.plancase_id_list) and len(plan_case_list)>0: return {'code': 200, 'msg': '部分用例执行成功！'}

        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/tester_run_one")
async def tester_run_one(item:plan_schemas.TesterRunOne,db:Session=Depends(get_case_db)):
    '''测试执行单个用例'''
    try:

        case_info=db.query(PlanCase).filter(PlanCase.plan_id==item.plan_id,PlanCase.case_id==item.case_id,PlanCase.isdelete==0).first()
        if case_info==None: return {'code':203,'msg':'无效ID！'}
        case_info.result=item.result

        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        case_info.result=item.result
        case_info.result_remark=item.result_remark
        case_info.run_time=now_time
        case_info.bug = item.bug
        db.commit()
        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def generate_tree(source, parent,total_json):
    '''格式化树形'''
    # 移出计算total的双重for循环
    total_dic = {}
    for key in total_json:
        if key in (None, ''): continue
        key_split = list(key.split('_'))
        l = len(key_split)
        if key_split[0] in total_dic.keys():
            total_dic[key_split[0]] += total_json[key]
        else:
            total_dic[key_split[0]] = total_json[key]

        if l > 1 and '{}_{}'.format(key_split[0], key_split[1]) in total_dic.keys():
            total_dic['{}_{}'.format(key_split[0], key_split[1])] += total_json[key]
        else:
            total_dic['{}_{}'.format(key_split[0], key_split[1])] = total_json[key]
        if l > 2 and key in total_dic.keys():
            total_dic[key] += total_json[key]
        else:
            total_dic[key] = total_json[key]
    # 取消递归，遍历存储数据
    dic_item = {}
    for item in source:
        item_json = item.to_json()
        item_json['total'] = 0
        item_json['inplan'] = False
        item_json['children'] = []
        if item_json['id_path'] in total_dic:
            item_json['total'] = total_dic[item_json['id_path']]
        if item_json['total']>0: item_json['inplan']=True
        if item_json["parent_id_path"] in dic_item.keys():
            dic_item[item_json["parent_id_path"]].append(item_json)
        else:
            dic_item[item_json["parent_id_path"]] = [item_json]
    # 构造树结构
    tree = dic_item[parent]
    for i in tree:
        if i["id_path"] in dic_item:
            i["children"] = dic_item[i["id_path"]]
        else:
            i["children"] = []
        for j in i["children"]:
            if j["id_path"] in dic_item:
                j["children"] = dic_item[j["id_path"]]
            else:
                j["children"] = []
    return tree




@router.get("/add_plan_tree")
async def add_plan_tree(plan_id:int=0,plan_version_id:int=0,del_myself:int=0,pro_code:str='',db:Session=Depends(get_case_db)):
    '''新增用例计划树型'''

    try:

        #获取计划里的用例
        plancase = db.query(PlanCase.case_id).filter(PlanCase.plan_id == plan_id, PlanCase.isdelete == 0).all()
        plancase_id=[case.case_id for case in plancase]

        # 自测用例删除
        if del_myself == 1:
            myself_list=db.query(PlanCase).filter(PlanCase.plan_version_id==plan_version_id,PlanCase.plan_type == '研发自测',PlanCase.isdelete==0).all()
            myself_case=[myself.case_id for myself in myself_list]
            return myself_list
            plancase_id+=myself_case
            plancase_id=list(set(plancase_id))

        #获取用例列表
        sql_param = [TestCase.isdelete == 0, TestCase.isrecovery == 0,TestCase.pro_code==pro_code]
        if len(plancase_id)>0:sql_param.append(TestCase.id.not_in(plancase_id))

        tree_list = [
            {
                'id': 'activity',
                'name': '活动用例',
                'id_path': 'activity',
                'type': 0,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'children': []
            },
            {
                'id': 'version',
                'name': '版本用例',
                'id_path': 'version',
                'type': 1,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'children': []
            },
            {
                'id': 'release',
                'name': '发布性用例',
                'id_path': 'release',
                'type': 2,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'children': []
            }
        ]

        # 获取所有目录和总数据
        index_list = db.query(CaseIndex).filter(CaseIndex.pro_code == pro_code, CaseIndex.isdelete == 0).order_by(CaseIndex.sort.asc()).all()

        case_total = db.query(func.count(TestCase.id).label('total'), TestCase.index_id, TestCase.case_type).filter(*sql_param).group_by(TestCase.index_id,TestCase.case_type).all()
        # 计算用例数
        total_json = {}
        for case in case_total:
            if case.case_type not in (0, 1, 2): continue
            if case.index_id in (None, ''): continue
            total_json[case.index_id] = case.total
            tree_list[case.case_type]['total'] += case.total

        format_tree = generate_tree(index_list, '0', total_json)

        # 传入树形数据
        tre_type = {0: tree_list[0]['children'], 1: tree_list[1]['children'], 2: tree_list[2]['children']}
        for tree in format_tree:
            tre_type[tree['type']].append(tree)

        return {'code': 200, 'msg': tree_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}








@router.get("/add_plan_list")
async def add_plan_list(plan_id:int=0,pro_code:str='',del_myself:int=0,plan_version_id:int=0,id_path:str='',keyword:str='',page_num:int=1,page_size:int=50,db:Session=Depends(get_case_db)):
    try:
        # 获取计划里的用例
        plancase = db.query(PlanCase.case_id).filter(PlanCase.plan_id == plan_id, PlanCase.isdelete == 0).all()
        plancase_id = [case.case_id for case in plancase]

        # 自测用例删除
        if del_myself == 1:
            myself_list = db.query(PlanCase).filter(PlanCase.plan_version_id == plan_version_id,
                                                    PlanCase.plan_type == '研发自测', PlanCase.isdelete == 0).all()
            myself_case = [myself.case_id for myself in myself_list]
            plancase_id += myself_case
            plancase_id = list(set(plancase_id))

        # 获取用例列表
        type_param={'activity':0,'version':1,'release':2}
        sql_param = [TestCase.isdelete == 0, TestCase.isrecovery == 0, TestCase.pro_code == pro_code]
        if len(plancase_id) > 0: sql_param.append(TestCase.id.not_in(plancase_id))
        if len(id_path)>0 and id_path not in type_param.keys(): sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))
        if len(id_path) > 0 and id_path in type_param.keys(): sql_param.append(TestCase.case_type==type_param[id_path])

        case_list=db.query(TestCase.case_type,TestCase.id,TestCase.case_level,TestCase.case_name,TestCase.case_step,TestCase.case_result,TestCase.front_info,CaseIndex.name,CaseIndex.level).join(CaseIndex,CaseIndex.id_path==TestCase.index_id).\
            filter(*sql_param).order_by(CaseIndex.sort.asc(),TestCase.sort_num.asc(),TestCase.sort_id.desc()).all()

        case_result=[]
        if len(keyword)>0:
            for case in case_list:
                if_kekvalue = [keyword not in case.case_name,keyword != case.case_level]
                if False not in if_kekvalue: continue
                case_result.append(case)

        if len(keyword)>0: case_list=case_result

        return qa_uitls.page_info(case_list, page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/plan_tree_dev")
async def plan_tree(pro_code:str='',pro_fun:str='dev',run_name:str='-1',plan_id:int=0,plan_name:str='',state:str='-1',case_level:str='-1',db:Session=Depends(get_case_db)):
    '''计划树型'''
    try:

        base_tree=[{'id':'plan','name':plan_name,'total':0,'id_path':'plan','level':0,'inplan':True,'children':[]}]

        #获取分配的自测用例
        myself_sql=[MySelfRecord.plan_id == plan_id,MySelfRecord.isdelete==0]

        if run_name!='-1':myself_sql.append(or_(MySelfRecord.check_name==run_name,MySelfRecord.name==run_name))
        if state in ('已自测','未自测','待沟通','无工作量'): myself_sql.append(MySelfRecord.result==state)
        if state in ('PASS','FAIL','BLOCK'): myself_sql.append(MySelfRecord.check_result==state)

        if state=='noname':
            myself_list = db.query(PlanCase.case_id).filter(PlanCase.case_id.notin_(db.query(MySelfRecord.case_id).filter(MySelfRecord.isdelete==0,MySelfRecord.plan_id==plan_id)),
                                                            PlanCase.isdelete==0,PlanCase.plan_id==plan_id).all()
        else:
            myself_list = db.query(MySelfRecord.case_id).filter(*myself_sql).group_by(MySelfRecord.case_id).all()

        check_myself_list=[myself.case_id for myself in myself_list]

        #获取总自测用例
        plan_sql=[PlanCase.plan_id==plan_id,PlanCase.isdelete==0]
        if state=='noname' and len(check_myself_list)>0: plan_sql.append(PlanCase.case_id.in_(check_myself_list))
        plancase_list=db.query(PlanCase).filter(*plan_sql).all()

        if len(plancase_list) == 0: return {'code': 200, 'msg': base_tree}

        case_id_list=[]

        for plancase in plancase_list:
            if run_name!='-1' and len(check_myself_list)>0 and plancase.case_id not in check_myself_list: continue
            if state in ('已自测','未自测','待沟通','无工作量','PASS','FAIL','BLOCK') and plancase.case_id not in check_myself_list: continue
            if state =='noname' and len(check_myself_list)>0 and plancase.case_id in check_myself_list: continue
            if state == 'noname' and len(check_myself_list)==0: continue
            if 'dev' not in pro_fun and plancase.tester!=run_name and run_name!='-1': continue

            case_id_list.append(plancase.case_id)


        # 获取用例列表
        sql_param = [TestCase.id.in_(case_id_list)]
        if case_level!='-1': sql_param.append(TestCase.case_level==case_level)

        tree_list = [
            {
                'id': 'activity',
                'name': '活动用例',
                'id_path': 'activity',
                'type': 0,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'inplan':False,
                'children': []
            },
            {
                'id': 'version',
                'name': '版本用例',
                'id_path': 'version',
                'type': 1,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'icon' : 'el-icon-notebook-1',
                'inplan': False,
                'children': []
            },
            {
                'id': 'release',
                'name': '发布性用例',
                'id_path': 'release',
                'type': 2,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'inplan': False,
                'children': []
            }
        ]

        # 获取所有目录和总数据
        index_list = db.query(CaseIndex).filter(CaseIndex.pro_code == pro_code,CaseIndex.isdelete==0).order_by(
            CaseIndex.sort.asc()).all()

        case_total = db.query(func.count(TestCase.id).label('total'), TestCase.index_id, TestCase.case_type,CaseIndex.id_path).join(CaseIndex,CaseIndex.id_path==TestCase.index_id).filter(
            *sql_param,CaseIndex.isdelete==0).group_by(TestCase.index_id, TestCase.case_type,CaseIndex.id_path).all()

        # 计算用例数
        total_json = {}
        for case in case_total:
            if case.case_type not in (0, 1, 2): continue
            if case.index_id in (None, ''): continue
            total_json[case.index_id] = case.total
            tree_list[case.case_type]['total'] += case.total

        format_tree = generate_tree(index_list, '0', total_json)

        # 传入树形数据
        tree_type = {0: tree_list[0]['children'], 1: tree_list[1]['children'], 2: tree_list[2]['children']}
        for tree in format_tree:
            tree_type[tree['type']].append(tree)


        for tree in tree_list:
            if tree['total']>0:
                tree['inplan']=True
                base_tree[0]['total']+=tree['total']
                base_tree[0]['children'].append(tree)


        return {'code': 200, 'msg':base_tree}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/plan_tree")
async def plan_tree(pro_code:str='',run_name:str='-1',plan_id:int=0,plan_name:str='',state:str='-1',case_level:str='-1',db:Session=Depends(get_case_db)):
    '''计划树型'''
    try:
        base_tree=[{'id':'plan','name':plan_name,'total':0,'id_path':'plan','level':0,'inplan':True,'children':[]}]
        plan_sql=[PlanCase.plan_id == plan_id,PlanCase.isdelete==0]

        if run_name!='-1':plan_sql.append(PlanCase.tester==run_name)
        if state in ('PASS','FAIL','BLOCK'): plan_sql.append(PlanCase.result==state)
        if state =='norun': plan_sql.append(PlanCase.result.in_(['',None,'未执行']))
        if state =='noname': plan_sql.append(PlanCase.tester.in_(['',None]))

        plancase_list = db.query(PlanCase).filter(*plan_sql).all()


        if len(plancase_list) == 0: return {'code': 200, 'msg': base_tree}

        case_id_list=[case.case_id for case in plancase_list]

        # 获取用例列表
        sql_param = [TestCase.id.in_(case_id_list)]
        if case_level!='-1': sql_param.append(TestCase.case_level == case_level)

        tree_list = [
            {
                'id': 'activity',
                'name': '活动用例',
                'id_path': 'activity',
                'type': 0,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'inplan':False,
                'children': []
            },
            {
                'id': 'version',
                'name': '版本用例',
                'id_path': 'version',
                'type': 1,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'icon' : 'el-icon-notebook-1',
                'inplan': False,
                'children': []
            },
            {
                'id': 'release',
                'name': '发布性用例',
                'id_path': 'release',
                'type': 2,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'inplan': False,
                'children': []
            }
        ]

        # 获取所有目录和总数据
        index_list = db.query(CaseIndex).filter(CaseIndex.pro_code == pro_code,CaseIndex.isdelete==0).order_by(
            CaseIndex.sort.asc()).all()

        case_total = db.query(func.count(TestCase.id).label('total'), TestCase.index_id, TestCase.case_type,CaseIndex.id_path).join(CaseIndex,CaseIndex.id_path==TestCase.index_id).filter(
            *sql_param,CaseIndex.isdelete==0).group_by(TestCase.index_id, TestCase.case_type,CaseIndex.id_path).all()

        # 计算用例数
        total_json = {}
        for case in case_total:
            if case.case_type not in (0, 1, 2): continue
            if case.index_id in (None, ''): continue
            total_json[case.index_id] = case.total
            tree_list[case.case_type]['total'] += case.total

        format_tree = generate_tree(index_list, '0', total_json)

        # 传入树形数据
        tree_type = {0: tree_list[0]['children'], 1: tree_list[1]['children'], 2: tree_list[2]['children']}
        for tree in format_tree:
            tree_type[tree['type']].append(tree)


        for tree in tree_list:
            if tree['total']>0:
                tree['inplan']=True
                base_tree[0]['total']+=tree['total']
                base_tree[0]['children'].append(tree)


        return {'code': 200, 'msg':base_tree}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del_plan_case")
async def del_plan_case(item:plan_schemas.DelPlanCase,db:Session=Depends(get_case_db)):
    '''删除计划里的用例'''
    try:
        plan_case=db.query(PlanCase).filter(PlanCase.plan_id==item.plan_id,PlanCase.case_id.in_(item.case_id_list),PlanCase.isdelete==0).all()
        record_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id==item.plan_id,MySelfRecord.isdelete==0,MySelfRecord.case_id.in_(item.case_id_list)).all()
        if len(plan_case)>0:
            for case in plan_case:
                case.isdelete=1
            db.commit()

        if len(record_list)>0:
            for rc in record_list:
                rc.isdelete=1
            db.commit()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.post("/dev_one_run")
async def dev_one_run(item:plan_schemas.RunOneMySelf,db:Session=Depends(get_case_db)):
    '''开发执行单挑自测用例'''
    try:
        record_info=db.query(MySelfRecord).filter(MySelfRecord.plan_id==item.plan_id,MySelfRecord.case_id==item.case_id,MySelfRecord.name==item.run_name,MySelfRecord.isdelete==0).first()
        if record_info==None: return {'code':201,'msg':'非执行人本人！'}


        record_info.result=item.result
        record_info.result_remark=item.result_remark
        record_info.run_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.commit()
        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/dev_list")
async def dev_list(plan_id:int,case_id:int,db:Session=Depends(get_case_db)):
    '''用例详情---开发列表'''
    try:

        record_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id==plan_id,MySelfRecord.case_id==case_id,MySelfRecord.isdelete==0).all()
        return {'code':200,'msg':record_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/tester_onerun_myself")
async def tester_onerun_myself(item:plan_schemas.TestRunMyself,db:Session=Depends(get_case_db)):
    try:
        record_list = db.query(MySelfRecord).filter(MySelfRecord.plan_id == item.plan_id,MySelfRecord.case_id==item.case_id,
                                                    MySelfRecord.isdelete == 0).all()
        plancase_info=db.query(PlanCase).filter(PlanCase.plan_id==item.plan_id,PlanCase.case_id==item.case_id,PlanCase.isdelete==0).first()
        if plancase_info==None: return {'code':203,'msg':'该用例未分配测试！'}

        if len(record_list)>0:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for rc in record_list:
                if rc.name in item.run_json.keys() and item.tester== plancase_info.tester:
                    rc.check_result=item.run_json[rc.name]
                    rc.check_name = item.tester
                    rc.check_time = now_time
            db.commit()

        if item.bug not in (None,''):
            plancase_info.bug=item.bug
            db.commit()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.get("/myself_summary")
async def myself_summary(plan_id:int=0,isinit:int=0,run_name:str='-1',db:Session=Depends(get_case_db)):
    '''自测用例统计'''
    try:

        summary=myselfsummary(plan_id,db,1.5,run_name)

        if isinit == 1 and summary['myself']['total'] == 0: summary = myselfsummary(plan_id, db, 1.5,'-1')

        return {'code':200,'msg':'操作成功！','myself':summary['myself'],'check':summary['check']}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def myselfsummary(plan_id,db,summary_size=1.5,runname='-1'):
    '''自测用例统计'''
    sql_param=[MySelfRecord.plan_id.in_(plan_id), MySelfRecord.isdelete == 0]
    if runname!='-1':sql_param.append(or_(MySelfRecord.name==runname,MySelfRecord.check_name==runname))

    record_list = db.query(MySelfRecord.result,MySelfRecord.check_result,MySelfRecord.name,MySelfRecord.check_name).filter(*sql_param).all()
    myself_json = {'total': 0, 'pass': 0, 'fail': 0, 'nowork': 0, 'norun': 0, 'pass_percen': 0,'block':0,
                   'fail_percen': 0,'nowork_percen': 0, 'norun_percen': 0,'block_percen':0,'pass_width': '0px', 'fail_width': '0px','norun_width': '0px', 'nowork_width': '0px'}
    tester_json = {'total': 0, 'pass': 0, 'fail': 0, 'norun': 0, 'pass_percen': 0, 'fail_percen': 0,'block':0,'block_percen':0,
                   'pass_width': '0px', 'fail_width': '0px', 'norun_width': '0px'}

    # 统计数量
    result_json = {'PASS': 'pass', 'FAIL': 'fail', '无工作量': 'nowork'}
    for rc in record_list:
        if rc.name not in ('', None):
            myself_json['total'] += 1
            if rc.result in result_json.keys():
                myself_json[result_json[rc.result]] += 1
            else:
                myself_json['norun'] += 1

        if rc.check_name not in ('', None):
            tester_json['total'] += 1
            if rc.check_result in result_json.keys():
                tester_json[result_json[rc.check_result]] += 1
            else:
                tester_json['norun'] += 1

    # 计算百分比
    myself_total = myself_json['total']
    if myself_total > 0:
        myself_json['pass_percen'] = round(myself_json['pass'] / myself_total * 100)
        myself_json['fail_percen'] = round(myself_json['fail'] / myself_total * 100)
        myself_json['nowork_percen'] = round(myself_json['nowork'] / myself_total * 100)
        myself_json['norun_percen'] = round(myself_json['norun'] / myself_total * 100)

        myself_json['pass_width'] = str(round(myself_json['pass_percen'] * summary_size)) + 'px'
        myself_json['fail_width'] = str(round(myself_json['fail_percen'] * summary_size)) + 'px'
        myself_json['nowork_width'] = str(round(myself_json['nowork_percen'] * summary_size)) + 'px'
        myself_json['norun_width'] = str(round(myself_json['norun_percen'] * summary_size)) + 'px'

    tester_total = tester_json['total']
    if tester_total > 0:
        tester_json['pass_percen'] = round(tester_json['pass'] / tester_total * 100)
        tester_json['fail_percen'] = round(tester_json['fail'] / tester_total * 100)
        tester_json['norun_percen'] = round(tester_json['norun'] / tester_total * 100)

        tester_json['pass_width'] = str(round(tester_json['pass_percen'] * summary_size)) + 'px'
        tester_json['fail_width'] = str(round(tester_json['fail_percen'] * summary_size)) + 'px'
        tester_json['norun_width'] = str(round(tester_json['norun_percen'] * summary_size)) + 'px'

    return {'myself': myself_json, 'check': tester_json}



@router.get("/tester_summary")
async def tester_summary(plan_id:int=0,isinit:int=0,run_name:str='-1',db:Session=Depends(get_case_db)):
    '''测试计划统计'''
    try:
        result=test_summary(plan_id,db,1.5,run_name)
        if isinit==1 and result['total']==0: result = test_summary(plan_id, db, 1.5, '')
        return {'code':200,'msg':'操作成功！','tester_summary':result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/plan_detail")
async def plan_detail(id:int=0,db:Session=Depends(get_case_db)):
    '''计划详情'''
    try:
        plan_info = db.query(TestPlan).filter(TestPlan.id == id).first()
        plan_info = plan_info.to_json()
        plan_info['join_plan_id'] = eval(plan_info['join_plan_id'])
        return {'code':200,'msg':plan_info}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def test_summary(plan_id,db,summary_size=1.5,run_name='-1',join_summary={}):
    '''测试计划统计'''
    sql_param=[PlanCase.plan_id == plan_id, PlanCase.isdelete == 0]
    if run_name!='-1': sql_param.append(PlanCase.tester==run_name)
    summary_list = db.query(PlanCase).filter(*sql_param).all()

    summary_json = {'total': 0, 'pass': 0, 'fail': 0,'block':0, 'norun': 0, 'pass_percen': 0,'block_percen':0, 'fail_percen': 0,
                    'pass_width': '0px', 'fail_width': '0px', 'norun_width': '0px','block_width':'0px'}

    if 'total' in join_summary.keys(): summary_json=join_summary

    result_json = {'PASS': 'pass', 'FAIL': 'fail','BLOCK':'block'}
    for sm in summary_list:
        if sm.tester not in ('', None):
            summary_json['total'] += 1
            if sm.result in result_json.keys():
                summary_json[result_json[sm.result]] += 1
            else:
                summary_json['norun'] += 1

    # 计算百分比
    summary_size = 1.5
    summary_total = summary_json['total']
    if summary_total > 0:
        summary_json['pass_percen'] = round(summary_json['pass'] / summary_total * 100)
        summary_json['fail_percen'] = round(summary_json['fail'] / summary_total * 100)
        summary_json['norun_percen'] = round(summary_json['norun'] / summary_total * 100)
        summary_json['block_percen'] = round(summary_json['block'] / summary_total * 100)

        summary_json['pass_width'] = str(round(summary_json['pass_percen'] * summary_size)) + 'px'
        summary_json['fail_width'] = str(round(summary_json['fail_percen'] * summary_size)) + 'px'
        summary_json['norun_width'] = str(round(summary_json['norun_percen'] * summary_size)) + 'px'
        summary_json['block_width'] = str(round(summary_json['block_percen'] * summary_size)) + 'px'


    return summary_json


@router.post("/save_planversion")
async def save_planversion(item:plan_schemas.SavePlanVersion,db:Session=Depends(get_case_db)):
    '''保存计划版本'''
    try:
        if item.id == 0:
            db_item = PlanVersion(**item.dict())
            db.add(db_item)
            db.commit()

        else:
            version = db.query(PlanVersion).filter(PlanVersion.id == item.id).first()

            if version == None: return {'code': 201, 'msg': '无效ID!'}

            version.version_name = item.version_name
            db.commit()

        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del_planversion")
async def del_planversion(item:plan_schemas.DelPlanVersion,db:Session=Depends(get_case_db)):
    '''删除计划版本'''
    try:
        version_info=db.query(PlanVersion).filter(PlanVersion.id==item.id).first()
        if version_info==None: return {'code':201,'msg':'无效ID！'}

        if db.query(TestPlan).filter(TestPlan.plan_version_id==item.id,TestPlan.isdelete==0).count()>0: return {'code':203,'msg':'该版本下存在测试计划，不能删除！'}
        version_info.isdelete =1
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/save_plan")
async def save_plan(item:plan_schemas.SavePlan,db:Session=Depends(get_case_db)):
    '''保存计划'''
    try:
        if item.id == 0:
            item_json=item.dict()
            item_json['join_plan_id'] = str(item_json['join_plan_id'])
            db_item = TestPlan(**item_json)
            db.add(db_item)
            db.commit()

        else:
            plan = db.query(TestPlan).filter(TestPlan.id == item.id).first()

            if plan == None: return {'code': 201, 'msg': '无效ID!'}

            plan.name = item.name
            plan.join_plan_id = str(item.join_plan_id)
            db.commit()

        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/del_plan")
async def del_plan(item:plan_schemas.DelPlanVersion,db:Session=Depends(get_case_db)):
    '''删除计划'''
    try:
        plan_info=db.query(TestPlan).filter(TestPlan.id==item.id).first()
        if plan_info==None: return {'code':201,'msg':'无效ID！'}

        if db.query(PlanCase).filter(PlanCase.plan_id==item.id,PlanCase.isdelete==0).count()>0: return {'code':203,'msg':'该版本下存在用例，不能删除！'}
        plan_info.isdelete =1
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/case_bug_list")
async def case_bug_list(plan_id:int,case_id:int,token:str='',run_name:str='',db:Session=Depends(get_case_db)):
    '''获取用例详情'''
    try:
        case_info = db.query(TestCase.id,TestCase.case_step,TestCase.case_name,TestCase.front_info,TestCase.case_level,TestCase.tester_remark,TestCase.case_result,PlanCase.plan_id,PlanCase.result,PlanCase.result_remark,PlanCase.bug).join(TestCase,TestCase.id==PlanCase.case_id).filter(PlanCase.plan_id==plan_id,PlanCase.case_id == case_id,PlanCase.isdelete==0).first()
        if case_info == None: return {'code': 203, 'msg': '无效ID!'}

        bug_result_list = []
        try:
            if case_info.bug not in ('',None):
                jira_clt = jira_com.INKE_JIRA(ticket=token)
                jql='key in ({})'.format(case_info.bug)
                bug_list = jira_clt.search_issues(jql, maxResults=2000)
                for bug in bug_list:
                    detail={'id':bug.key,'title':bug.fields.summary,'assignee':'','report_name':'','level':'','created':bug.fields.created[0:10],'status':bug.fields.status}

                    if bug.fields.assignee: detail['assignee']=bug.fields.assignee.displayName
                    if bug.fields.reporter: detail['report_name'] = bug.fields.reporter.displayName
                    if bug.fields.priority: detail['level'] = bug.fields.priority.name
                    if bug.fields.status: detail['status'] = bug.fields.status.name

                    bug_result_list.append(detail)
        except Exception as ex:
            bug_result_list = []

        record=db.query(MySelfRecord).filter(MySelfRecord.case_id==case_id,MySelfRecord.name==run_name,MySelfRecord.isdelete==0,MySelfRecord.plan_id==plan_id).first()
        record_info = {'result': '', 'result_remark': ''}
        if record!=None:
            record_info['result']=record.result
            record_info['result_remark']=record.result_remark

        return {'code':200,'msg':case_info,'bug_list':bug_result_list,'record_info':record}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/plan_version_list")
async def plan_version_list(pro_code:str,db:Session=Depends(get_case_db)):
    '''获取统计版本号'''
    try:

        version_list=db.query(PlanVersion).filter(PlanVersion.pro_code==pro_code,PlanVersion.isdelete==0).order_by(PlanVersion.id.desc()).all()
        return {'code':200,'msg':version_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/plan_summary")
async def plan_summary(version_id:int,db:Session=Depends(get_case_db)):
    '''计算统计'''
    try:
        record_list=db.query(MySelfRecord.name,MySelfRecord.check_result,TestCase.index_id.label('demand_id'),CaseIndex.parent_id_path,CaseIndex.name.label('demand_name'),CaseIndex.level).join(TestCase,MySelfRecord.case_id==TestCase.id).join(CaseIndex,CaseIndex.id_path==TestCase.index_id).filter(MySelfRecord.isdelete==0,MySelfRecord.plan_version_id==version_id,MySelfRecord.check_result.in_(['PASS','FAIL','未验收'])).all()

        #获取需求
        demand_json={}
        for item in record_list:
            rc={'name':item.name,'check_result':item.check_result,'demand_id':item.demand_id,'parent_id_path':item.parent_id_path,'demand_name':item.demand_name,'level':item.level}

            if rc['level']==3:
                rc['demand_name']=db.query(CaseIndex.name).filter(CaseIndex.id_path==rc['parent_id_path']).first().name

            if rc['demand_name'] in demand_json.keys():
                demand_json[rc['demand_name']]['total'] += 1
                if rc['check_result'] == 'PASS': demand_json[rc['demand_name']]['pass'] += 1

                # 统计名称
                if rc['name'] in demand_json[rc['demand_name']].keys():
                    demand_json[rc['demand_name']][rc['name']]['total'] += 1
                    if rc['check_result'] == 'PASS': demand_json[rc['demand_name']][rc['name']]['pass'] += 1
                    if rc['check_result'] == 'FAIL': demand_json[rc['demand_name']][rc['name']]['fail'] += 1
                else:
                    demand_json[rc['demand_name']][rc['name']] = {'total': 0, 'pass': 0, 'fail': 0}
                    demand_json[rc['demand_name']][rc['name']]['total'] += 1
                    if rc['check_result'] == 'PASS': demand_json[rc['demand_name']][rc['name']]['pass'] += 1
                    if rc['check_result'] == 'FAIL': demand_json[rc['demand_name']][rc['name']]['fail'] += 1

            else:
                demand_json[rc['demand_name']]={'total':0,'pass':0}
                demand_json[rc['demand_name']]['total']+=1
                if rc['check_result']=='PASS': demand_json[rc['demand_name']]['pass']+=1

                #统计名称
                if rc['name'] in demand_json[rc['demand_name']].keys():
                    demand_json[rc['demand_name']][rc['name']]['total'] += 1
                    if rc['check_result'] == 'PASS': demand_json[rc['demand_name']][rc['name']]['pass'] += 1
                    if rc['check_result'] == 'FAIL': demand_json[rc['demand_name']][rc['name']]['fail'] += 1
                else:
                    demand_json[rc['demand_name']][rc['name']]={'total':0,'pass':0,'fail':0}
                    demand_json[rc['demand_name']][rc['name']]['total']+=1
                    if rc['check_result'] == 'PASS': demand_json[rc['demand_name']][rc['name']]['pass'] += 1
                    if rc['check_result'] == 'FAIL': demand_json[rc['demand_name']][rc['name']]['fail'] += 1


        result_list=[]
        for key in demand_json.keys():

            for name in demand_json[key].keys():
                if name not in ('total', 'pass'):
                    detail = {'demand_name': key, 'demand_percen': 0, 'name': name,
                              'total': demand_json[key][name]['total'], 'pass': demand_json[key][name]['pass'],
                              'fail': demand_json[key][name]['fail'], 'pass_percen': 0}
                    if detail['total']>0: detail['pass_percen']=round(detail['pass']/detail['total']*100,2)
                    if demand_json[key]['total'] > 0: detail['demand_percen'] = round(demand_json[key]['pass'] / demand_json[key]['total'] * 100, 2)
                    result_list.append(detail)

        return {'code':200,'msg':result_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/update_case_dev")
async def del_plan(item:plan_schemas.UpdateDev,db:Session=Depends(get_case_db)):
    '''修改开发人员名称'''
    try:
        record_list=db.query(MySelfRecord).filter(MySelfRecord.case_id.in_(item.case_id_list),MySelfRecord.plan_id==item.plan_id,MySelfRecord.name==item.run_name,MySelfRecord.isdelete==0).all()
        plas_record_list = db.query(MySelfRecord).filter(MySelfRecord.case_id.in_(item.case_id_list),
                                                    MySelfRecord.plan_id == item.plan_id,
                                                    MySelfRecord.isdelete == 0).all()
        name_json={}
        for record in plas_record_list:
            if record.name in name_json.keys():
                name_json[record.name].append(record.case_id)
            else:
                name_json[record.name]=[]
                name_json[record.name].append(record.case_id)

        isrepeat=0
        if len(record_list) >0:
            for rc in record_list:
                if item.updev_name in name_json.keys():
                    if rc.case_id in name_json[item.updev_name]:
                        isrepeat=1
                        continue

                if rc.name==item.updev_name: continue
                rc.name=item.updev_name
                rc.result = '未自测'
                rc.result_remark = ''
            db.commit()

        if isrepeat==0:
            return {'code':200,'msg':'操作成功！'}
        else:
            return {'code': 200, 'msg':'部分用例的开发人员有重复，请联系测试人员重新分配！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



#/*---------------------统计------------------------*/

@router.get("/select_plan")
async def select_plan(plan_version_id:int,db:Session=Depends(get_case_db)):
    try:
        plan_version_list=db.query(TestPlan).filter(TestPlan.plan_version_id == plan_version_id,TestPlan.isdelete==0).order_by(TestPlan.id.desc()).all()
        return {'code':200,'msg':plan_version_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/dev_summary")
async def dev_summary(plan_version_id:int,plan_id:int,db:Session=Depends(get_case_db)):
    '''开发执行情况'''
    try:
        sql_param=[MySelfRecord.isdelete==0,MySelfRecord.plan_version_id==plan_version_id]
        if plan_id!=-1:sql_param.append(MySelfRecord.plan_id==plan_id)
        dev_case_list=db.query(MySelfRecord).filter(*sql_param).all()

        dev_json={'未分配':{'pass':0,'fail':0,'norun':0,'nowork':0,'total':len(dev_case_list)}}
        norun_total=0
        for dev in dev_case_list:
            if dev.name in dev_json.keys():
                dev_json[dev.name]['total'] += 1
                if dev.result == 'PASS': dev_json[dev.name]['pass'] += 1
                if dev.result == 'FAIL': dev_json[dev.name]['fail'] += 1
                if dev.result == '未自测':dev_json[dev.name]['norun'] += 1
                if dev.result == '无工作量': dev_json[dev.name]['nowork'] += 1
                if dev.result in (None, ''): norun_total += 1
            else:
                dev_json[dev.name]={'pass':0,'fail':0,'norun':0,'nowork':0,'block':0,'total':0}
                dev_json[dev.name]['total']+=1
                if dev.result == 'PASS': dev_json[dev.name]['pass']+=1
                if dev.result == 'FAIL': dev_json[dev.name]['fail'] += 1
                if dev.result == '未自测':dev_json[dev.name]['norun'] += 1
                if dev.result == '无工作量': dev_json[dev.name]['nowork']+=1
                if dev.result in (None,''):norun_total+=1

        dev_json['未分配']['norun']=norun_total

        #计算统计率
        result_list={'pass':[],'fail':[],'norun':[],'nowork':[]}
        name_list=[]
        for key in dev_json:
            total=dev_json[key]['total']
            name_list.append(key)
            #名称
            # if total>0:
            #     if key!='未分配':
            #         run_count=dev_json[key]['pass']+dev_json[key]['fail']+dev_json[key]['nowork']
            #         name_list.append('{} [{}%]'.format(key,str(round(run_count/total*100,2))))
            #     else:
            #         name_list.append('{} [{}%]'.format(key, str(round(dev_json[key]['norun'] / total * 100, 2))))
            # else:
            #     name_list.append('{} [0%]'.format(key))

            if total>0:
                result_list['pass'].append(dev_json[key]['pass'])
                result_list['fail'].append(dev_json[key]['fail'])
                result_list['norun'].append(dev_json[key]['norun'])
                result_list['nowork'].append(dev_json[key]['nowork'])
            else:
                result_list['pass'].append(0)
                result_list['fail'].append(0)
                result_list['norun'].append(0)
                result_list['nowork'].append(0)

        return {'code':200,'msg':result_list,'name':name_list}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





@router.get("/test_summary")
async def test_summary2(plan_version_id:int,plan_id:int,db:Session=Depends(get_case_db)):
    '''测试执行情况'''
    try:
        sql_param=[PlanCase.isdelete==0,PlanCase.plan_version_id==plan_version_id]

        sql_param2=[MySelfRecord.isdelete==0,MySelfRecord.plan_version_id==plan_version_id]

        if plan_id != -1:
            sql_param.append(PlanCase.plan_id == plan_id)
            sql_param2.append(MySelfRecord.plan_id == plan_id)

        plancase_list = db.query(PlanCase).filter(*sql_param).all()

        myself_list=db.query(MySelfRecord).filter(*sql_param2).all()

        tester_json = {'未分配': {'pass': 0, 'fail': 0, 'norun': 0,'block':0, 'total': 0}}
        norun_total = 0

        for plancase in plancase_list:
            if plancase.plan_type == '研发自测': continue
            if plancase.tester in tester_json.keys():
                tester_json[plancase.tester]['total'] += 1
                if plancase.result == 'PASS': tester_json[plancase.tester]['pass'] += 1
                if plancase.result == 'FAIL': tester_json[plancase.tester]['fail'] += 1
                if plancase.result == 'BLOCK': tester_json[plancase.tester]['block'] += 1
                if plancase.result in ('',None) and plancase.tester not in ('',None): tester_json[plancase.tester]['norun'] += 1
                if plancase.result in (None, '','未执行') and plancase.tester in ('', None): norun_total += 1
            else:
                tester_json[plancase.tester] = {'pass': 0, 'fail': 0, 'norun': 0, 'block': 0, 'total': 0}
                tester_json[plancase.tester]['total'] += 1
                if plancase.result == 'PASS': tester_json[plancase.tester]['pass'] += 1
                if plancase.result == 'FAIL': tester_json[plancase.tester]['fail'] += 1
                if plancase.result == 'BLOCK': tester_json[plancase.tester]['block'] += 1
                if plancase.result in ('',None) and plancase.tester not in ('',None): tester_json[plancase.tester]['norun'] += 1
                if plancase.result in (None, '','未执行') and plancase.tester in ('',None): norun_total += 1


        #累计自测用例
        for myself in myself_list:
            if myself.check_name in tester_json.keys():
                tester_json[myself.check_name]['total'] += 1
                if myself.check_result == 'PASS': tester_json[myself.check_name]['pass'] += 1
                if myself.check_result == 'FAIL': tester_json[myself.check_name]['fail'] += 1
                if myself.check_result == 'BLOCK': tester_json[myself.check_name]['block'] += 1
                if myself.check_result == '未验收': tester_json[myself.check_name]['norun'] += 1
                if myself.check_result in (None, ''): norun_total += 1
            else:
                tester_json[myself.check_name] = {'pass': 0, 'fail': 0, 'norun': 0, 'block': 0, 'total': 0}
                tester_json[myself.check_name]['total'] += 1
                if myself.check_result == 'PASS': tester_json[myself.check_name]['pass'] += 1
                if myself.check_result == 'FAIL': tester_json[myself.check_name]['fail'] += 1
                if myself.check_result == 'BLOCK': tester_json[myself.check_name]['block'] += 1
                if myself.check_result == '未验收': tester_json[myself.check_name]['norun'] += 1
                if myself.check_result in (None, ''): norun_total += 1

        tester_json['未分配']['norun'] = norun_total


        # 计算统计
        result_list = {'pass': [], 'fail': [], 'block': [], 'norun': []}
        name_list = []
        for key in tester_json:
            if key in ('',None): continue
            name_list.append(key)

            result_list['pass'].append(tester_json[key]['pass'])
            result_list['fail'].append(tester_json[key]['fail'])
            result_list['norun'].append(tester_json[key]['norun'])
            result_list['block'].append(tester_json[key]['block'])

        return {'code': 200, 'msg': result_list, 'name': name_list,'aa':norun_total}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/demand_summary")
async def demand_summary(plan_id:int,db:Session=Depends(get_case_db)):
    try:
        demand_json = {}
        name_list=[]
        result_list = {'pass': [], 'fail': [], 'block': [], 'norun': []}
        plan_type=db.query(TestPlan.type).filter(TestPlan.id==plan_id).first()

        if plan_type.type=='研发自测':
            record_list = db.query(MySelfRecord.check_result,MySelfRecord.result,
                                   CaseIndex.parent_id_path, CaseIndex.name.label('demand_name'), CaseIndex.level).join(
                TestCase, MySelfRecord.case_id == TestCase.id).join(CaseIndex,CaseIndex.id_path == TestCase.index_id).filter(
                MySelfRecord.isdelete == 0, MySelfRecord.plan_id == plan_id).all()


            for item in record_list:
                rc = {'check_result': item.check_result,'parent_id_path': item.parent_id_path, 'demand_name': item.demand_name, 'level': item.level,'result':item.result}

                if rc['level'] == 3: rc['demand_name'] = db.query(CaseIndex.name).filter(CaseIndex.id_path == rc['parent_id_path']).first().name

                if rc['demand_name'] in demand_json.keys():

                    if rc['result'] == 'PASS': demand_json[rc['demand_name']]['dev_pass'] += 1
                    if rc['result'] == 'FAIL': demand_json[rc['demand_name']]['dev_fail'] += 1
                    if rc['result'] == '无工作量': demand_json[rc['demand_name']]['dev_nowork'] += 1
                    if rc['result'] in ('未执行','未自测'): demand_json[rc['demand_name']]['dev_norun'] += 1

                    if rc['check_result'] == 'PASS': demand_json[rc['demand_name']]['test_pass'] += 1
                    if rc['check_result'] == 'FAIL': demand_json[rc['demand_name']]['test_fail'] += 1
                    if rc['check_result'] == '未验收': demand_json[rc['demand_name']]['test_norun'] += 1

                else:

                    demand_json[rc['demand_name']]={'dev_pass':0,'dev_fail':0,'dev_block':0,'dev_nowork':0,'dev_norun':0,'test_pass':0,'test_fail':0,'test_block':0,'test_norun':0}
                    if rc['result'] == 'PASS': demand_json[rc['demand_name']]['dev_pass'] += 1
                    if rc['result'] == 'FAIL': demand_json[rc['demand_name']]['dev_fail'] += 1
                    if rc['result'] == '无工作量': demand_json[rc['demand_name']]['dev_nowork'] += 1
                    if rc['result'] in ('未执行','未自测'): demand_json[rc['demand_name']]['dev_norun'] += 1

                    if rc['check_result'] == 'PASS': demand_json[rc['demand_name']]['test_pass'] += 1
                    if rc['check_result'] == 'FAIL': demand_json[rc['demand_name']]['test_fail'] += 1
                    if rc['check_result'] == '未验收': demand_json[rc['demand_name']]['test_norun'] += 1

            #统计数据
            for key in demand_json:
                name_list.append('{}（开发）'.format(key))

                result_list['pass'].append(demand_json[key]['dev_pass'])
                result_list['fail'].append(demand_json[key]['dev_fail'])
                result_list['norun'].append(demand_json[key]['dev_norun'])
                result_list['block'].append(demand_json[key]['dev_block'])


                name_list.append('{}（测试）'.format(key))

                result_list['pass'].append(demand_json[key]['test_pass'])
                result_list['fail'].append(demand_json[key]['test_fail'])
                result_list['norun'].append(demand_json[key]['test_norun'])
                result_list['block'].append(demand_json[key]['test_block'])


        else:

            #非自测的用例
            record_list = db.query(PlanCase.tester,PlanCase.result,CaseIndex.parent_id_path, CaseIndex.name.label('demand_name'), CaseIndex.level).join(
                TestCase, PlanCase.case_id == TestCase.id).join(CaseIndex,CaseIndex.id_path == TestCase.index_id).filter(
                PlanCase.isdelete == 0, PlanCase.plan_id == plan_id).all()


            for item in record_list:
                rc = {'tester':item.tester,'parent_id_path': item.parent_id_path, 'demand_name': item.demand_name, 'level': item.level,'result':item.result}

                if rc['level'] == 3: rc['demand_name'] = db.query(CaseIndex.name).filter(CaseIndex.id_path == rc['parent_id_path']).first().name

                if rc['demand_name'] in demand_json.keys():

                    if rc['result'] == 'PASS': demand_json[rc['demand_name']]['test_pass'] += 1
                    if rc['result'] == 'FAIL': demand_json[rc['demand_name']]['test_fail'] += 1
                    if rc['result'] == 'BLOCK': demand_json[rc['demand_name']]['test_block'] += 1
                    if rc['result'] in ('', None) and rc['tester'] not in ('', None): demand_json[rc['demand_name']]['test_norun'] += 1
                    if rc['result'] in ('', None,'未执行','未自测') and rc['tester'] in ('', None): demand_json[rc['demand_name']]['test_norun'] += 1
                else:

                    demand_json[rc['demand_name']]={'test_pass':0,'test_fail':0,'test_block':0,'test_norun':0}

                    if rc['result'] == 'PASS': demand_json[rc['demand_name']]['test_pass'] += 1
                    if rc['result'] == 'FAIL': demand_json[rc['demand_name']]['test_fail'] += 1
                    if rc['result'] == 'BLOCK': demand_json[rc['demand_name']]['test_block'] += 1
                    if rc['result'] in ('',None) and rc['tester'] not in ('',None): demand_json[rc['demand_name']]['test_norun'] += 1
                    if rc['result'] in ('', None, '未执行','未自测') and rc['tester'] in ('', None): demand_json[rc['demand_name']][
                        'test_norun'] += 1

            # 统计数据
            for key in demand_json:
                name_list.append(key)

                result_list['pass'].append(demand_json[key]['test_pass'])
                result_list['fail'].append(demand_json[key]['test_fail'])
                result_list['norun'].append(demand_json[key]['test_norun'])
                result_list['block'].append(demand_json[key]['test_block'])


        return {'code': 200, 'msg': result_list, 'name': name_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}





