from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import plan_schemas
from qa_dal.database import get_case_db,get_api_db,get_sso_db
from sqlalchemy.orm import Session
from sqlalchemy import or_,func,and_
import common.jira_base as jira_com


from qa_dal import qa_uitls
from qa_dal.models import TestPlan,TestCase,MySelfRecord,PlanCase,User,PlanVersion,CaseIndex
import datetime
import jsonpath

router = APIRouter(
    prefix="/tm/join",
    tags=["测试管理-测试关联"]
)



@router.post("/join_tester_myselfrun")
async def join_tester_myselfrun(item:plan_schemas.JoinTesterMyselfRun,db:Session=Depends(get_case_db),sysdb:Session=Depends(get_sso_db)):
    '''测试批量验收自测用例'''

    #根据职能获取开发名称
    try:
        if len(item.join_case_json['myself_case'])>0:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            run_name_list=[]
            # 判断是否为全部
            sql_param=[MySelfRecord.plan_id.in_(item.join_plan_id),MySelfRecord.case_id.in_(item.join_case_json['myself_case']),MySelfRecord.isdelete == 0]
            if item.pro_fun=='full':
                full_record_list = db.query(MySelfRecord).filter(*sql_param).all()
                if len(full_record_list) > 0:
                    for rc in full_record_list:
                        if rc.check_name == item.run_name:
                            rc.check_result = item.result
                            rc.check_time = now_time
                            rc.check_name = item.run_name
                    db.commit()

            else:
                user_name_list=sysdb.query(User).filter(User.pro_fun==item.pro_fun,User.isdelete==0,User.pro_code_list.like('%{}%'.format(item.pro_code))).all()
                if len(user_name_list)==0: return {'code':'203','msg':'勾选用例的开发职能不匹配！'}

                user_name=[user.user_name for user in user_name_list]
                sql_param.append(MySelfRecord.name.in_(user_name))
                record_list=db.query(MySelfRecord).filter(*sql_param).all()

                if len(record_list)>0:
                    for rc in record_list:
                        #判断测试人员是否相等
                        if rc.check_name==item.run_name:
                            rc.check_result = item.result
                            rc.check_time = now_time
                            rc.check_name = item.run_name

                db.commit()


        if len(item.join_case_json['testcase'])>0:
            plan_case_list = db.query(PlanCase).filter(PlanCase.plan_id==item.plan_id,PlanCase.case_id.in_(item.join_case_json['testcase']), PlanCase.isdelete == 0,
                                                       PlanCase.tester == item.run_name).all()

            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if len(plan_case_list) > 0:
                for case in plan_case_list:
                    case.result = item.result
                    case.run_time = now_time
                db.commit()
            else:
                return {'code': 201, 'msg': '非本人执行！'}

        return {'code': 200, 'msg': '操作成功！',}

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


@router.get("/join_case_list")
async def join_case_list(join_plan_id:str='',plan_id:int=0,run_name:str='-1',state:str='-1',case_level:str='-1',id_path:str='',page_num:int=1,page_size:int=50,db:Session=Depends(get_case_db)):
    '''自测用例+测试用例'''
    try:
        #判断是否有关联的ID
        join_case_json = {}
        base_case_list = []
        if len(join_plan_id)>0:
            join_myself_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id.in_(join_plan_id.split(',')),MySelfRecord.isdelete==0).all()

            #获取自测结果、测试结果、研发评论、测试人员/统计
            for myself in join_myself_list:
                if myself.case_id not in base_case_list: base_case_list.append(myself.case_id)

                #过滤条件
                if run_name!='-1' and myself.name!=run_name and myself.check_name!=run_name: continue
                if state!='-1' and state in ('PASS','FAIL') and myself.check_result!=state: continue
                if state != '-1' and state in ('待沟通', '无工作量','未自测') and myself.result != state: continue
                if state != '-1' and state=='未执行' and myself.check_result!='未验收': continue
                if state =='BLOCK': continue

                if myself.case_id in join_case_json.keys():
                    join_case_json[myself.case_id]['dev_record'].append({'name':myself.name,'result':myself.result})
                    join_case_json[myself.case_id]['test_record'].append({'name':myself.name,'result':myself.check_result})
                    if len(myself.result_remark)>0:
                        join_case_json[myself.case_id]['dev_remark'].append({'name':myself.name,'remark':myself.result_remark})

                    # 计算统计
                    if myself.check_result in join_case_json[myself.case_id]['summary_count'].keys():
                        join_case_json[myself.case_id]['summary_count']['total'] += 1
                        join_case_json[myself.case_id]['summary_count'][myself.check_result] += 1

                else:
                    join_case_json[myself.case_id]={'dev_record':[{'name':myself.name,'result':myself.result}],
                                                    'test_record':[{'name':myself.name,'result':myself.check_result}],
                                                    'dev_remark':[],
                                                    'tester':myself.check_name,'plan_id':myself.plan_id,'summary_count':{'total':0,'未验收':0,'PASS':0,'FAIL':0,'BLOCK':0}}

                    if len(myself.result_remark)>0:
                        join_case_json[myself.case_id]['dev_remark'].append({'name':myself.name,'remark':myself.result_remark})

                    #计算统计
                    if myself.check_result in join_case_json[myself.case_id]['summary_count'].keys():
                        join_case_json[myself.case_id]['summary_count']['total']+=1
                        join_case_json[myself.case_id]['summary_count'][myself.check_result]+=1


        #获取所有计划的数据
        all_plan_id=join_plan_id.split(',')
        all_plan_id.append(plan_id)

        sql_param=[PlanCase.plan_id.in_(all_plan_id),PlanCase.isdelete==0]

        #判断条件
        if case_level!='-1': sql_param.append(TestCase.case_level==case_level)

        type_param = {'activity': 0, 'version': 1, 'release': 2}

        if id_path in type_param.keys():
            sql_param.append(TestCase.case_type == type_param[id_path])
        if id_path not in type_param.keys() and id_path not in ('plan', '', None):
            sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))


        plan_case_list = db.query(TestCase.case_name, TestCase.isrecovery, TestCase.isdelete, TestCase.case_type,
                                 TestCase.id, TestCase.front_info, TestCase.case_step,
                                 TestCase.case_result, TestCase.case_level, PlanCase.id.label('plancase_id'),PlanCase.plan_type,
                                 PlanCase.tester, PlanCase.result, PlanCase.plan_id, PlanCase.result_remark,
                                 PlanCase.case_id, PlanCase.bug, CaseIndex.name, CaseIndex.level).join(TestCase,TestCase.id == PlanCase.case_id).join(CaseIndex, CaseIndex.id_path == TestCase.index_id).filter(*sql_param).order_by(CaseIndex.sort.asc(),
                                                                                           TestCase.sort_num.asc(),
                                                                                           TestCase.sort_id.desc()).all()

        join_case_list=[]
        summary_count={'total':0,'NORUN':0,'PASS':0,'FAIL':0,'BLOCK':0,'pass_percen':0,'fail_percen':0,'block_percen':0,'pass_width':0,'fail_width':0,'block_width':0}
        noname_case_list=[]
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
                'level': plancase.level,'plan_type':plancase.plan_type,'dev_remark':[]
            }

            #判断是否自测用例
            if str(plancase.plan_id) in join_plan_id.split(','):
                if plancase.case_id in join_case_json.keys() and plancase.plan_id == join_case_json[plancase.id]['plan_id']:

                    plancase_item['plan_type']='研发自测'
                    plancase_item['dev_result']=join_case_json[plancase.id]['dev_record']
                    plancase_item['tester_result'] = join_case_json[plancase.id]['test_record']
                    plancase_item['tester'] = join_case_json[plancase.id]['tester']
                    plancase_item['dev_remark'] = join_case_json[plancase.id]['dev_remark']

                    #累计总数
                    summary_count['total']+=join_case_json[plancase.id]['summary_count']['total']
                    summary_count['NORUN'] += join_case_json[plancase.id]['summary_count']['未验收']
                    summary_count['PASS'] += join_case_json[plancase.id]['summary_count']['PASS']
                    summary_count['FAIL'] += join_case_json[plancase.id]['summary_count']['FAIL']
                    summary_count['BLOCK'] += join_case_json[plancase.id]['summary_count']['BLOCK']
                    join_case_list.append(plancase_item)

                else:
                    if plancase.case_id in base_case_list: continue
                    if run_name != '-1' and plancase.tester != run_name: continue
                    if state != '-1' and state in ('PASS', 'FAIL', 'BLOCK') and plancase.result != state: continue
                    if state != '-1' and state in ('无工作量', '未自测', '待沟通'): continue

                    plancase_item['plan_type'] = '研发自测'
                    join_case_list.append(plancase_item)


            #判断是否测试用例
            if plancase.plan_id == plan_id:
                #删除重复用例，优先显示自测用例
                if plancase.case_id in join_case_json.keys():
                    case_info=db.query(PlanCase).filter(PlanCase.id==plancase.id).first()
                    case_info.isdelete=1
                    db.commit()
                    continue

                #过滤条件
                if run_name!='-1' and plancase.tester!=run_name: continue
                if state!='-1' and state in ('PASS','FAIL','BLOCK') and plancase.result!=state: continue
                if state != '-1' and state=='未执行' and plancase.result not in ('',None,'未执行'): continue
                if state!='-1' and state in ('无工作量','未自测','待沟通'): continue


                plancase_item['plan_type'] = '测试执行'
                join_case_list.append(plancase_item)

                # 累计总数
                summary_count['total'] += 1
                if plancase.result in summary_count.keys():
                    summary_count[plancase.result]+=1

                if plancase.result in ('未执行','',None,'未验收'):
                    summary_count['NORUN'] += 1

            if plancase_item['tester'] in ('',None,'未分配'):
                noname_case_list.append(plancase_item)

            if len(plancase_item['dev_result'])==0 and plancase_item['plan_type']=='研发自测':
                noname_case_list.append(plancase_item)

        if run_name=='-1' and state=='noname':
            join_case_list=noname_case_list

        result=qa_uitls.page_info(join_case_list, page_num, page_size)
        result['noname_count']=len(noname_case_list)

        #计算通过率
        tester_total=summary_count['total']
        if tester_total >0:
            summary_count['pass_percen'] = round(summary_count['PASS'] / tester_total * 100)
            summary_count['fail_percen'] = round(summary_count['FAIL'] / tester_total * 100)
            summary_count['block_percen'] = round(summary_count['BLOCK'] / tester_total * 100)

            summary_count['pass_width'] = str(round(summary_count['pass_percen'] * 1.5)) + 'px'
            summary_count['fail_width'] = str(round(summary_count['fail_percen'] * 1.5)) + 'px'
            summary_count['block_width'] = str(round(summary_count['block_percen'] * 1.5)) + 'px'

        result['summary_count'] = summary_count

        return result

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}







@router.get("/join_plan_tree")
async def join_plan_tree(pro_code:str='',run_name:str='',join_plan_id:str='',plan_id:int=0,state:str='-1',case_level:str='-1',plan_name:str='',db:Session=Depends(get_case_db)):
    '''计划树型'''
    try:
        base_tree=[{'id':'plan','name':plan_name,'total':0,'id_path':'plan','level':0,'inplan':True,'children':[]}]
        join_planid=join_plan_id.split(',')
        join_id=join_planid
        join_id.append(str(plan_id))

        #自测用例的内容
        join_caseid_list=[]
        myself_sql = [MySelfRecord.plan_id.in_(join_planid), MySelfRecord.isdelete == 0]
        if len(join_plan_id)>0:

            if run_name != '-1': myself_sql.append(or_(MySelfRecord.check_name == run_name, MySelfRecord.name == run_name))
            if state in ('已自测', '未自测', '待沟通', '无工作量'): myself_sql.append(MySelfRecord.result == state)
            if state in ('PASS', 'FAIL', 'BLOCK'): myself_sql.append(MySelfRecord.check_result == state)
            if state=='norun':myself_sql.append(MySelfRecord.check_result.in_('未验收','',None))

            myself_list = db.query(MySelfRecord.case_id).filter(*myself_sql).group_by(MySelfRecord.case_id).all()

            join_caseid_list = [myself.case_id for myself in myself_list]

        #测试用例的内容
        plan_sql=[PlanCase.plan_id==plan_id ,PlanCase.isdelete==0]

        if run_name!='-1':plan_sql.append(PlanCase.tester==run_name)
        if state in ('PASS', 'FAIL', 'BLOCK'):plan_sql.append(PlanCase.result==state)


        plancase_list = db.query(PlanCase).filter(*plan_sql).all()
        if state in ('已自测', '未自测', '待沟通', '无工作量'): plancase_list=[]


        for plancase in plancase_list:
            if state=='norun' and plancase.result not in ('',None,'未执行'): continue

            join_caseid_list.append(plancase.case_id)


        if len(join_caseid_list) == 0: return {'code': 200, 'msg': base_tree}


        # 获取用例列表
        sql_param = [TestCase.id.in_(join_caseid_list)]
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









@router.post("/join_tester_myself_runname")
async def join_tester_myself_runname(item:plan_schemas.JoinTesterRunName,db:Session=Depends(get_case_db)):
    '''联合分配测试人员'''
    try:
        #修改计划用例
        join_planid=item.join_plan_id
        join_planid.append(item.plan_id)
        join_case_id=list(set(item.join_case_json['myself_case']+item.join_case_json['testcase']))
        plan_case_list=db.query(PlanCase).filter(PlanCase.plan_id.in_(join_planid),PlanCase.case_id.in_(join_case_id),PlanCase.isdelete==0).all()

        if len(plan_case_list)>0:
            for case in plan_case_list:
                if case.tester!=item.tester:
                    case.tester = item.tester
                    case.result = ''
                    case.result_remark = ''
                    case.run_time = None
            db.commit()


        #修改自测记录
        record_list= db.query(MySelfRecord).filter(MySelfRecord.plan_id.in_(item.join_plan_id),MySelfRecord.case_id.in_(item.join_case_json['myself_case']),MySelfRecord.isdelete==0).all()
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




@router.post("/join_del_plan_case")
async def join_del_plan_case(item:plan_schemas.JoinDelPlanCase,db:Session=Depends(get_case_db)):
    '''删除计划里的用例'''
    try:

        plan_case=db.query(PlanCase).filter(PlanCase.plan_id==item.plan_id,PlanCase.case_id.in_(item.join_case_json['testcase']),PlanCase.isdelete==0).all()

        myself_plan_case = db.query(PlanCase).filter(PlanCase.plan_id.in_(item.join_plan_id),PlanCase.case_id.in_(list(set(item.join_case_json['myself_case']))),PlanCase.isdelete==0).all()
        record_list=db.query(MySelfRecord).filter(MySelfRecord.plan_id.in_(item.join_plan_id),MySelfRecord.isdelete==0,MySelfRecord.case_id.in_(item.join_case_json['myself_case'])).all()

        if len(plan_case)>0:
            for case in plan_case:
                case.isdelete=1
            db.commit()


        if len(myself_plan_case)>0:
            for case in myself_plan_case:
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




@router.get("/join_plan_tree2")
async def join_plan_tree2(run_name: str = '', join_plan_id: str = '', plan_id: int = 0,
                          state: str = '-1', case_level: str = '-1', plan_name: str = '',
                          db: Session = Depends(get_case_db)):
    '''计划树型'''
    try:
        base_tree = [{'id': 'plan', 'name': plan_name, 'total': 0, 'id_path': 'plan', 'level': 0, 'inplan': True,'leaf':False,
                      'children': []}]
        join_planid = join_plan_id.split(',')
        join_id = join_planid
        join_id.append(str(plan_id))

        # 自测用例的内容
        join_caseid_list = []
        myself_sql = [MySelfRecord.plan_id.in_(join_planid), MySelfRecord.isdelete == 0]
        if len(join_plan_id) > 0:

            if run_name != '-1': myself_sql.append(
                or_(MySelfRecord.check_name == run_name, MySelfRecord.name == run_name))
            if state in ('已自测', '未自测', '待沟通', '无工作量'): myself_sql.append(MySelfRecord.result == state)
            if state in ('PASS', 'FAIL', 'BLOCK'): myself_sql.append(MySelfRecord.check_result == state)
            if state == 'norun': myself_sql.append(MySelfRecord.check_result.in_('未验收', '', None))

            myself_list = db.query(MySelfRecord.case_id).filter(*myself_sql).group_by(MySelfRecord.case_id).all()

            join_caseid_list = [myself.case_id for myself in myself_list]

        # 测试用例的内容
        plan_sql = [PlanCase.plan_id == plan_id, PlanCase.isdelete == 0]

        if run_name != '-1': plan_sql.append(PlanCase.tester == run_name)
        if state in ('PASS', 'FAIL', 'BLOCK'): plan_sql.append(PlanCase.result == state)

        plancase_list = db.query(PlanCase).filter(*plan_sql).all()
        if state in ('已自测', '未自测', '待沟通', '无工作量'): plancase_list = []

        for plancase in plancase_list:
            if state == 'norun' and plancase.result not in ('', None, '未执行'): continue

            join_caseid_list.append(plancase.case_id)

        if len(join_caseid_list) == 0: return {'code': 200, 'msg': base_tree}

        # 获取用例列表
        sql_param = [TestCase.id.in_(join_caseid_list)]
        if case_level != '-1': sql_param.append(TestCase.case_level == case_level)

        tree_list = [
            {
                'id': 'activity',
                'name': '活动用例',
                'id_path': 'activity',
                'type': 0,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'inplan': False,
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
                'icon': 'el-icon-notebook-1',
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

        case_total = db.query(func.count(TestCase.id).label('total'), TestCase.case_type,
                              CaseIndex.id_path).join(CaseIndex, CaseIndex.id_path == TestCase.index_id).filter(
            *sql_param, CaseIndex.isdelete == 0).group_by(TestCase.case_type).all()

        for case in case_total:
            if case.case_type in (0, 1, 2):
                tree_list[case.case_type]['total'] = case.total
                if case.total > 0: tree_list[case.case_type]['leaf'] = False
                base_tree[0]['total']+=case.total


        return {'code': 200, 'msg': base_tree}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}

