from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import plan_schemas
from qa_dal.database import get_case_db,get_api_db
from sqlalchemy.orm import Session
from sqlalchemy import or_,func,and_
import common.jira_base as jira_com


from qa_dal import qa_uitls
from qa_dal.models import TestPlan,TestCase,MySelfRecord,PlanCase,User,PlanVersion,CaseIndex
import datetime
import jsonpath

router = APIRouter(
    prefix="/tm/caseplan",
    tags=["测试管理-测试计划"]
)

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


@router.get("/testplancase_list")
async def testplancase_list(plan_versin_id:int=0,plan_id:int=0,run_name:str='-1',state:str='-1',case_level:str='-1',isinit:int='0',id_path:str='',page_num:int=1,page_size:int=50,db:Session=Depends(get_case_db)):
    '''测试计划用例列表'''
    try:

        sql_param=[PlanCase.plan_id==plan_id,PlanCase.isdelete==0,CaseIndex.isdelete==0]

        type_param={'activity':0,'version':1,'release':2}

        if id_path in type_param.keys():
            sql_param.append(TestCase.case_type==type_param[id_path])
        if id_path not in type_param.keys() and id_path not in ('plan','',None):
            sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))

        if case_level!='-1': sql_param.append(TestCase.case_level==case_level)

        state_json={'norun':PlanCase.result.in_(['',None]),'noname':PlanCase.tester.in_(['',None]),'PASS':PlanCase.result=='PASS','FAIL':PlanCase.result=='FAIL','BLOCK':PlanCase.result=='BLOCK'}
        if state in state_json.keys(): sql_param.append(state_json[state])

        if run_name not in ('-1',-1):sql_param.append(PlanCase.tester==run_name)

        plancase_list = db.query(TestCase.case_name,TestCase.isrecovery,TestCase.isdelete,TestCase.case_type,TestCase.id, TestCase.front_info, TestCase.case_step,
                                 TestCase.case_result, TestCase.case_level, PlanCase.id.label('plancase_id'),
                                 PlanCase.tester,PlanCase.result,PlanCase.plan_id,PlanCase.result_remark,
                                 PlanCase.case_id,PlanCase.bug,CaseIndex.name,CaseIndex.level).join(TestCase, TestCase.id == PlanCase.case_id).join(CaseIndex,CaseIndex.id_path==TestCase.index_id).filter(*sql_param).order_by(CaseIndex.sort.asc(),TestCase.sort_num.asc(), TestCase.sort_id.desc()).all()

        #初次化没找到则重新获取
        if isinit==1 and len(plancase_list)==0:
            plancase_list = db.query(TestCase.case_name, TestCase.isrecovery, TestCase.isdelete, TestCase.case_type,
                                     TestCase.id, TestCase.front_info, TestCase.case_step,
                                     TestCase.case_result, TestCase.case_level, PlanCase.id.label('plancase_id'),
                                     PlanCase.tester, PlanCase.result, PlanCase.plan_id,
                                     PlanCase.result_remark,PlanCase.case_id, PlanCase.bug, CaseIndex.name,CaseIndex.level).join(
                TestCase, TestCase.id == PlanCase.case_id).join(CaseIndex,
                                                                CaseIndex.id_path == TestCase.index_id).filter(PlanCase.isdelete==0,PlanCase.plan_id==plan_id,CaseIndex.isdelete == 0).order_by(CaseIndex.sort.asc(),
                                                                                             TestCase.sort_num.asc(),
                                                                                             TestCase.sort_id.desc()).all()

        #获取自测用例
        myself_list=db.query(MySelfRecord).filter(MySelfRecord.plan_version_id==plan_versin_id,MySelfRecord.isdelete==0).all()

        myself_json={}
        new_result=[]
        if len(myself_list)>0:

            for myself in myself_list:

                # 获取开发自测结果和测试验收结果
                if myself.case_id in myself_json.keys():
                    myself_json[myself.plan_id][myself.case_id]['dev'].append(
                        {'name': myself.name, 'result': myself.result})
                    myself_json[myself.plan_id][myself.case_id]['tester'].append(
                        {'name': myself.name, 'result': myself.check_result})
                else:
                    myself_json[myself.plan_id][myself.case_id] = {
                        'dev': [{'name': myself.name, 'result': myself.result}],
                        'tester': [{'name': myself.name, 'result': myself.check_result}]}



            for plancase in plancase_list:
                plancase_item={
                    'case_name':plancase.case_name,
                    'isrecovery':plancase.isrecovery,
                    'isdelete': plancase.isdelete,
                    'case_type':'',
                    'id':plancase.id,
                    'front_info':plancase.front_info,'case_step':plancase.case_step,'case_result':plancase.case_result,'case_level':plancase.case_level,'plancase_id':plancase.plancase_id,
                    'tester':plancase.tester,'result':plancase.result,'plan_id':plancase.plan_id,'result_remark':plancase.result_remark,'case_id':plancase.case_id,'result_remark':plancase.result_remark,
                    'bug':plancase.bug,'name':plancase.name,'dev_result':[],'tester_result':[], 'level':plancase.level
                }
                if plancase.plan_id in myself_json.keys():
                    plancase_item['case_type']='研发自测'
                    if plancase.id in myself_json[plancase.plan_id].keys():
                        plancase_item['dev_result']=myself_json[plancase.plan_id][plancase.id]['dev']
                        plancase_item['tester_result'] = myself_json[plancase.plan_id][plancase.id]['tester']
                else:
                    plancase_item['case_type'] = '测试执行'

                new_result.append(plancase_item)

        result=qa_uitls.page_info(plancase_list, page_num, page_size)
        result['noname']=db.query(PlanCase).filter(PlanCase.plan_id==plan_id,PlanCase.isdelete==0,PlanCase.tester.in_(['',None])).count()

        return result

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
    sql_param=[MySelfRecord.plan_id == plan_id, MySelfRecord.isdelete == 0]
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



def test_summary(plan_id,db,summary_size=1.5,run_name='-1'):
    '''测试计划统计'''
    sql_param=[PlanCase.plan_id == plan_id, PlanCase.isdelete == 0]
    if run_name!='-1': sql_param.append(PlanCase.tester==run_name)
    summary_list = db.query(PlanCase).filter(*sql_param).all()
    summary_json = {'total': 0, 'pass': 0, 'fail': 0,'block':0, 'norun': 0, 'pass_percen': 0,'block_percen':0, 'fail_percen': 0,
                    'pass_width': '0px', 'fail_width': '0px', 'norun_width': '0px','block_width':'0px'}

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



