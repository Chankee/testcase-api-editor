#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：测试yongli接口

import math
import os
import random
from typing import List, Union

import xlrd
from fastapi import APIRouter, File, UploadFile
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import Session

from qa_dal import qa_uitls
from qa_dal.database import get_case_db
from qa_dal.models import TestCase, Version, Demand,CaseIndex
from qa_dal.testmanage import testcase_schemas
from uitls.redis_clt import redis_clt

router = APIRouter(
    prefix="/tm/caselist",
    tags=["测试管理-测试用例"]
)


@router.get("/tree",response_model=Union[List[testcase_schemas.VersionItem],testcase_schemas.VersionTree])
async def case_tree(pro_code:str,db:Session=Depends(get_case_db)):
    '''
    树形状态
    :param pro_code:
    :param db:
    :return:
    '''
    try:
        base_version_list= db.query(Version).filter(Version.pro_code==pro_code,Version.isdelete==0).order_by(Version.id.desc()).all()


        #所有版本的汇总
        version_total_list=db.query(TestCase.version_id,func.count(TestCase.id).label('total')).\
            filter(TestCase.pro_code==pro_code,TestCase.isdelete==0,TestCase.isrecovery==0).group_by(TestCase.version_id).all()
        version_total={version.version_id:version.total for version in version_total_list}

        #所有需求模块的汇总
        demanid_total_list = db.query(TestCase.demand_id, func.count(TestCase.id).label('total')). \
            filter(TestCase.pro_code == pro_code, TestCase.isdelete == 0, TestCase.isrecovery == 0).group_by(
            TestCase.demand_id).all()
        demanid_total={demand.demand_id:demand.total for demand in demanid_total_list}


        #查找所有子模块
        tag_list=db.query(TestCase.demand_id,TestCase.tag).\
            filter(TestCase.pro_code == pro_code, TestCase.isdelete == 0, TestCase.isrecovery == 0).group_by(TestCase.tag,TestCase.demand_id).all()
        tag_json={tag.demand_id:tag.tag for tag in tag_list}

        #数据分析
        version_item = {'id': 'version', 'name': '版本用例', 'value': {'type': 'version_base', 'id': 0}, 'total': 0,
                        'children': [],'leaf':True}
        release_item = {'id':'release','name':'发布性用例','value':{'type':'release_base','id':0},'total':0,'children': [],'leaf':True}
        result_list=[]
        for version in base_version_list:
            item={}

            if version.isrelease==0:
                # 版本用例
                item['id']='version{}'.format(str(version.id))
                item['name']=version.version_name
                item['value']={'type':'version','id':version.id,'version_id':version.id}
                item['total']=version_total.get(version.id,0)
                item['leaf'] =[False,True][item['total']>0]
                item['children']=[{'id':'demand{}'.format(str(demand.id)),
                                   'name':demand.demand_name,'value':{'type':'demand','id':demand.id,'version_id':version.id,'demand_id':demand.id},
                                   'leaf':[False,True][demanid_total.get(demand.id,0)>0 and tag_json.get(demand.id) not in (None,'')],
                                   'total':demanid_total.get(demand.id,0),'children':[]} for demand in version.demand_item]

                version_item['children'].append(item)
                version_item['total']+=item['total']
            else:
                #发布性用例
                release_item['total'] = version_total.get(version.id, 0)
                release_item['children'] = [{'id': 'release_demand{}'.format(str(demand.id)),
                                     'name': demand.demand_name, 'value': {'type': 'release_demand', 'id': demand.id,'version_id':version.id,'demand_id':demand.id},
                                     'leaf': [False, True][demanid_total.get(demand.id, 0) > 0 and tag_json.get(demand.id) not in (None,'')],
                                     'total': demanid_total.get(demand.id, 0),'children':[]} for demand in version.demand_item]

        result_list.append(version_item)
        result_list.append(release_item)

        return {'code':200,'msg':result_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/changesort")
async def changesort(item: testcase_schemas.TestSort, db:Session=Depends(get_case_db)):
    '''
    修改顺序
    '''
    try:

        base_info=db.query(TestCase).filter(TestCase.id==item.sort_num['base_id']).first()
        change_info = db.query(TestCase).filter(TestCase.id == item.sort_num['change_id']).first()
        base_num=base_info.sort_num
        change_num=change_info.sort_num
        base_sort_id=base_info.sort_id
        change_sort_id=change_info.sort_id

        if change_num == base_num:
            base_info.sort_id = change_sort_id
            change_info.sort_id = base_sort_id
        else:
            base_info.sort_num=change_num
            change_info.sort_num = base_num
        db.commit()

        return {'code':200,'msg':'操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/reviews")
async def review_case(item: testcase_schemas.TestCaseReview, db:Session=Depends(get_case_db)):
    '''
    用例评审
    :param case:
    :param db:
    :return:
    '''
    try:

        case_list = db.query(TestCase).filter(TestCase.id.in_(item.ids)).all()

        if len(case_list)==0: return {'code': 201, 'msg': '无效ID!'}

        for case in case_list:
            case.review_state = item.review_state

        db.commit()
        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/tree_detail")
async def tree_detail(demand_id:int,tag:str,db:Session=Depends(get_case_db)):
    try:
        result=db.query(TestCase.id,TestCase.case_name,TestCase.case_type)\
            .filter(TestCase.demand_id==demand_id,TestCase.isdelete==0,TestCase.isrecovery==0,TestCase.tag==tag).order_by(TestCase.id.desc()).all()

        result_list=[{'id':'case{}'.format(str(rl.id)),'name':rl.case_name,'value':{'id':rl.id,'type':'case','case_type':rl.case_type}} for rl in result]
        return {'code':200,'msg':result_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/list")
async def search_case_list(id_path:str='',pro_code:str='',case_name:str='',review_state:int=-1,create_name:str='',run_name:str='',case_level:str=''
        ,page_num:int=1,page_size:int=10,db:Session=Depends(get_case_db)):
    '''
    查询用例
    :param version_id:
    :param demand_id:
    :param pro_code:
    :param case_name:
    :param create_name:
    :param run_name:
    :param case_level:
    :param isrecovery:
    :param case_type:
    :param page_num:
    :param page_size:
    :param db:
    :return:
    '''
    try:

        sql_param_list = [TestCase.pro_code == pro_code,TestCase.isrecovery==0,TestCase.isdelete == 0]  # 基础搜索条件
        if case_name.__len__() > 0: sql_param_list.append(TestCase.case_name.like('%{}%'.format(case_name)))  # 追加条件
        if create_name.__len__() > 0: sql_param_list.append(TestCase.create_name == create_name)
        if review_state in (0,1,2): sql_param_list.append(TestCase.review_state == review_state)

        type_param={'activity':0,'version':1,'release':2}
        if id_path in type_param.keys():
            sql_param_list.append(TestCase.case_type==type_param[id_path])

        if len(id_path)>0 and id_path!='recovery' and id_path not in type_param.keys():
            sql_param_list.append(TestCase.index_id.like('{}%'.format(id_path)))

        if run_name.__len__() > 0:
            sql_param_list.append(or_(TestCase.android_name == run_name,
                                      TestCase.ios_name == run_name,
                                      TestCase.manage_name == run_name,
                                      TestCase.h5_name == run_name,
                                      TestCase.applet_name == run_name,
                                      TestCase.tester == run_name))

        if case_level in ('P0', 'P1', 'P2'): sql_param_list.append(TestCase.case_level == case_level)

        result_list=db.query(TestCase.id,TestCase.case_type,TestCase.case_name,TestCase.case_level,TestCase.front_info,
                             TestCase.case_step,TestCase.case_result,TestCase.review_state,TestCase.create_name,TestCase.isrecovery,
                             TestCase.recovery_people,TestCase.sort_num,TestCase.tester_remark,TestCase.index_id,CaseIndex.name,CaseIndex.level).\
            join(CaseIndex,CaseIndex.id_path==TestCase.index_id).filter(*sql_param_list).order_by(CaseIndex.sort.asc(),TestCase.sort_num.asc(),TestCase.sort_id.desc()).all()
        return qa_uitls.page_info(result_list, page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/recovery_list")
async def search_recovery_list(pro_code:str='',id_path:str='',
        case_name:str='',create_name:str='',recovery_people:str='',case_level:str=''
        ,page_num:int=1,page_size:int=10,db:Session=Depends(get_case_db)):
    '''
    查询回收用例
    :param pro_code:
    :param version_name:
    :param page_num:
    :param page_size:
    :param db:
    :return:
    '''
    try:

        sql_param_list = [TestCase.pro_code == pro_code, TestCase.isdelete == 0,TestCase.isrecovery == 1]  # 基础搜索条件

        if case_name.__len__() > 0: sql_param_list.append(TestCase.case_name.like('%{}%'.format(case_name)))  # 追加条件
        if create_name.__len__() > 0: sql_param_list.append(TestCase.create_name == create_name)
        if case_level in ('P0', 'P1', 'P2'): sql_param_list.append(TestCase.case_level == case_level)
        if recovery_people.__len__()>0: sql_param_list.append(TestCase.recovery_people == recovery_people)

        type_param = {'activity': 0, 'version': 1, 'release': 2}
        if id_path in type_param.keys():
            sql_param_list.append(TestCase.case_type == type_param[id_path])

        if len(id_path) > 0 and id_path != 'recovery' and id_path not in type_param.keys():
            sql_param_list.append(TestCase.index_id.like('{}%'.format(id_path)))

        result_list = db.query(TestCase,CaseIndex.name,CaseIndex.level).join(CaseIndex, CaseIndex.id_path == TestCase.index_id).filter(*sql_param_list).order_by(
            TestCase.index_id.desc(), TestCase.sort_num.asc(), TestCase.sort_id.desc()).all()

        return qa_uitls.page_info(result_list, page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/recovery_case")
async def recovery_case(item: testcase_schemas.TestCaseRecovery, db:Session=Depends(get_case_db)):
    '''
    批量放入回收站
    :param id_list:
    :param db:
    :return:
    '''
    try:

        case_list = db.query(TestCase).filter(TestCase.id.in_(item.id)).all()
        for case in case_list:
            if case == None: continue
            if item.type == 1:
                case.isrecovery = 1
                case.recovery_people = item.recovery_people
            else:
                case.isrecovery = 0
                case.recovery_people = ''
            db.commit()

        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()
        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/create")
async def add_case(case: testcase_schemas.TestCaseCreate, db:Session=Depends(get_case_db)):
    '''
    创建用例
    :param version:
    :param db:
    :return:
    '''
    try:
        case_item=case.dict()
        #判断是否发布性用例
        case_type_json={'activity':0,'version':1,'release':2}
        case_item['case_type']=case_type_json[case.version_demand[0]]
        case_item['index_id']=case.version_demand[-1]
        del case_item['version_demand']
        del case_item['sort_id']
        db_item = TestCase(**case_item)
        db.add(db_item)
        db.commit()

        #判断是否需要插入位置
        base_case=db.query(TestCase).filter(TestCase.id==case.sort_id).first()
        if base_case==None:
            db_item.sort_num = db_item.id
        else:
            db_item.sort_num = base_case.sort_num
        db_item.sort_id = db_item.id
        db.commit()

        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", case.pro_code)
        r.hdel("testcase_tree", case.pro_code)
        r.close()

        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/del")
async def recovery_case(item: testcase_schemas.TestCaseDel, db:Session=Depends(get_case_db)):
    '''
    批量删除
    :param id_list:
    :param db:
    :return:
    '''
    try:

        case_list = db.query(TestCase).filter(TestCase.id.in_(item.id)).all()
        for case in case_list:
            if case == None: continue
            case.isdelete = 1
            db.commit()

        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()

        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/detail")
async def get_case_detail(id:int,db:Session=Depends(get_case_db)):
    '''
    用例详情信息
    :param id:
    :param db:
    :return:
    '''
    try:
        type_json={0:'activity',1:'version',2:'release'}
        case_info=db.query(TestCase).filter(TestCase.id == id).first()
        detail_info=case_info.to_json()

        #获取父类
        id_path=detail_info['index_id'].split('_')

        detail_info['version_demand']=[type_json[detail_info['case_type']]]
        id_info = {0: id_path[0], 1: '{}_{}'.format(id_path[0],id_path[1]), 2: detail_info['index_id']}

        for i in range(0,len(id_path)):
            detail_info['version_demand'].append(id_info[i])

        return {'code': 200, 'msg':detail_info }
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/update")
async def update_case(item: testcase_schemas.TestCaseSave, db:Session=Depends(get_case_db)):
    '''
    修改用例信息
    :param version:
    :param db:
    :return:
    '''
    try:

        case = db.query(TestCase).filter(TestCase.id == item.id).first()
        if case == None: return {'code': 201, 'msg': '无效ID!'}

        case.case_name = item.case_name
        case.case_level = item.case_level
        case.front_info = item.front_info
        case.case_step = item.case_step
        case.case_result = item.case_result
        case.tester_remark = item.tester_remark
        case.index_id = item.version_demand[-1]
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/move_case")
async def move_case(item: testcase_schemas.TestCaseMove, db:Session=Depends(get_case_db)):
    '''
    移动版本用例和发布性用例
    :param case:
    :param db:
    :return:
    '''
    try:
        index_info = db.query(CaseIndex).filter(CaseIndex.id_path==item.version_demain[-1]).first()
        if index_info==None: return {'code':203,'msg':'目录不存在！'}
        case_list = db.query(TestCase).filter(TestCase.id.in_(item.case_id_list)).all() #所有用例信息

        # 版本用例移动
        if len(case_list)>0:
            for case in case_list:
                case.case_type = index_info.type
                case.index_id = item.version_demain[-1]
            db.commit()


        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()
        return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/release_move")
async def move_release_case(item: testcase_schemas.TestCaseMove, db:Session=Depends(get_case_db)):
    '''
    发布性用例内部移动
    :param case_item:
    :param db:
    :return:
    '''
    try:

        case_list = db.query(TestCase).filter(TestCase.id.in_(item.case_id_list)).all()  # 所有用例信息

        for case in case_list:

            if case == None: continue

            case.version_id = item.version_demain[0]
            case.demand_id = item.version_demain[1]
            db.commit()

        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/release_user")
def releasecase_user(case_item: testcase_schemas.ReleaseCaseUser,db:Session=Depends(get_case_db)):
    '''
    发布性用例批量修改测试
    :param db:
    :param case_item:
    :return:
    '''
    try:
        case_list = db.query(TestCase).filter(TestCase.id.in_(case_item.case_id_list),TestCase.isdelete==0,TestCase.isrecovery==0).all()
        for case in case_list:
            if case==None: continue
            case.tester=case_item.tester
            db.commit()

        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/update_version_user")
async def update_user(item: testcase_schemas.TestCaseUser, db:Session=Depends(get_case_db)):
    '''
    批量修改执行人
    :param id_list:
    :param db:
    :return:
    '''
    try:

        case_list = db.query(TestCase).filter(TestCase.id.in_(item.case_id_list)).all()
        user_list = []

        for case in case_list:
            user_detail = []
            if case == None: continue

            # 判断分配的人员是否已执行用例，已执行则不分配并提示
            if case.android_result in ('PASS', 'FAIL', 'NOWORK', 'BLOCK'):
                user_detail.append(
                    {'id': case.id, 'type': 'Android', 'name': case.android_name, 'result': case.android_result,
                     'rtime': case.android_runtime})
            else:
                if item.android_name.__len__()>0: case.android_name = item.android_name

            if case.ios_result in ('PASS', 'FAIL', 'NOWORK', 'BLOCK'):
                user_detail.append(
                    {'id': case.id, 'name': case.ios_name, 'result': case.ios_result, 'rtime': case.ios_runtime})
            else:
                if item.ios_name.__len__()>0: case.ios_name = item.ios_name

            if case.manage_result in ('PASS', 'FAIL', 'NOWORK', 'BLOCK'):
                user_detail.append({'id': case.id, 'name': case.manage_name, 'result': case.manage_result,
                                    'rtime': case.manage_runtime})
            else:
                if item.manage_name.__len__()>0: case.manage_name = item.manage_name

            if case.h5_result in ('PASS', 'FAIL', 'NOWORK', 'BLOCK'):
                user_detail.append(
                    {'id': case.id, 'name': case.h5_name, 'result': case.h5_result, 'rtime': case.h5_runtime})
            else:
                if item.h5_name.__len__()>0: case.h5_name = item.h5_name

            if case.server_result in ('PASS', 'FAIL', 'NOWORK', 'BLOCK'):
                user_detail.append({'id': case.id, 'name': case.server_name, 'result': case.server_result,
                                    'rtime': case.server_runtime})
            else:
                if item.server_name.__len__()>0: case.server_name = item.server_name

            if case.applet_result in ('PASS', 'FAIL', 'NOWORK', 'BLOCK'):
                user_detail.append({'id': case.id, 'name': case.applet_name, 'result': case.applet_result,
                                    'rtime': case.applet_runtime})
            else:
                if item.applet_name.__len__()>0: case.applet_name = item.applet_name

            if case.tester_result in ('PASS', 'FAIL'):
                user_detail.append(
                    {'id': case.id, 'name': case.tester, 'result': case.tester_result, 'rtime': case.tester_runtime})
            else:
                if item.tester.__len__()>0: case.tester = item.tester

            db.commit()
            if user_detail != []: user_list.append(user_detail)
        return {'code': 200, 'msg': '操作成功!', 'other': user_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/demand_case_list",response_model=Union[List[testcase_schemas.PlanDemand],testcase_schemas.PlanReturn])
async def get_demand_case_list(pro_code:str,db:Session=Depends(get_case_db)):
    '''
    需求模块用例
    :param id:
    :param db:
    :return:
    '''
    version=db.query(Version.id).filter(Version.pro_code==pro_code,Version.isdelete==0,Version.isrelease==1).first()
    demand_list=db.query(Demand).filter(Demand.pro_code==pro_code,Demand.isdelete==0,Demand.version_id==version.id).\
        order_by(Demand.id.desc()).all()

    result_list=[]
    for dl in demand_list:
        if len(dl.case_item) == 0: continue
        result_detail={}
        result_detail['label']=dl.demand_name
        result_detail['value']=dl.id
        result_detail['children']=[{'label':case.case_name,'value':case.id} for case in dl.case_item]
        result_list.append(result_detail)

    return {'code':200,'msg':result_list}



@router.post("/upload")
async def upload(file: UploadFile = File(...),pro_code:str=''):
    '''
    上传文档
    :param file:
    :return:
    '''
    try:
        file_name =str(math.floor(1e6 * random.random()))
        base_path=os.path.abspath(os.path.dirname(__file__)).replace('\\','/').replace('/test_manage','')
        file_data = await file.read()

        #获取文件后缀
        path=file.filename.split(".")[1]
        # if path not in ('xlsx','csv','xls'): return {'code':201,'msg':'请上传xlsx、csv、xls格式文件!'}
        file_path='{}/upload/testcase/{}'.format(base_path,'{}_{}.{}'.format(pro_code,file_name,path))

        #读取文件
        with open(file_path,"wb+") as fp:
            fp.write(file_data)
        fp.close()

        #获取列表
        wb = xlrd.open_workbook(filename=file_path)  # 读取excel文件
        sheetname = wb.sheet_names()

        return {'code':200,'msg':'上传成功！','return_file_name':file_path,'sheet_list':sheetname,'df_info':read_excel(wb,sheetname[0])}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code':500,'msg':'导入的用例模板格式有误，请检查格式或新下载用例模板！','err_msg':'接口报错，报错信息：{}'.format(error_info)}


def read_excel(wb,name):
    '''
    读取文件
    '''
    tb = wb.sheet_by_name(name)
    rowNum = tb.nrows
    if rowNum == 0: return []
    case_list=[]
    for i in range(rowNum):
        if i==0: continue
        case_info={}
        case_info['tag'] = tb.row_values(i)[0]
        case_info['case_name']=tb.row_values(i)[1]
        case_info['case_level'] = tb.row_values(i)[2]
        case_info['front_info'] = tb.row_values(i)[3]
        case_info['case_step'] = tb.row_values(i)[4]
        case_info['case_result'] = tb.row_values(i)[5]
        case_info['tester_remark'] = tb.row_values(i)[6]
        case_list.append(case_info)
    return case_list



@router.post("/switch_sheet")
async def switch_sheet(item:testcase_schemas.SwitchSheet):
    '''
    切换表单
    '''
    try:
        wb = xlrd.open_workbook(filename=item.file_path)  # 读取excel文件
        return {'code':200,'msg':read_excel(wb,item.sheet_name)}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code':500,'msg':'导入的用例模板格式有误，请检查格式或新下载用例模板！','err_msg':'接口报错，报错信息：{}'.format(error_info)}



@router.post("/import_case")
async def switch_sheet(item:testcase_schemas.ImportCaseItem,db:Session=Depends(get_case_db)):
    try:
        #目录控制
        index_name_list=db.query(CaseIndex).filter(CaseIndex.isdelete==0,CaseIndex.parent_id_path==item.version_demand[-1],CaseIndex.level==3).all()
        type=db.query(CaseIndex).filter(CaseIndex.id_path==item.version_demand[-1]).first()

        case_type=-1
        if type!=None: case_type=type.type
        excel_tag=set([case['tag'] for case in item.case_table])
        index_tag={index.name:index.id_path for index in index_name_list}
        index_json={}
        for tag in excel_tag:
            if tag=='':
                index_json[tag] = item.version_demand[-1]

            elif tag in index_tag.keys():
                # 判断目录是否存在
                index_json[tag]=index_tag[tag]

            elif tag not in index_tag.keys():
                #不存在则添加
                index_item={'name':tag,'parent_id_path':item.version_demand[-1],'type':case_type,'pro_code':item.pro_code,'level':3}
                db_item = CaseIndex(**index_item)
                db.add(db_item)
                db.commit()

                # 修改信息
                index_info = db.query(CaseIndex).filter(CaseIndex.id == db_item.id).first()
                index_id_path='{}_{}'.format(index_info.parent_id_path, index_info.id)
                index_info.id_path = index_id_path
                index_info.sort = index_info.id
                db.commit()
                index_json[tag]=index_id_path


        #合并数据
        case_info=item.dict()

        case_type_json = {'activity': 0, 'version': 1, 'release': 2}
        for case in case_info['case_table']:
            detail={}
            detail['case_name']=case['case_name']
            detail['case_level']=case['case_level']
            detail['front_info'] = case['front_info']
            detail['case_step'] = case['case_step']
            detail['case_result']=case['case_result']
            detail['tester_remark'] = case['tester_remark']

            detail['pro_code'] = case_info['pro_code']
            detail['create_name']=case_info['create_name']
            detail['case_type']=case_type_json[case_info['version_demand'][0]]
            if case['tag'] in index_json.keys():
                detail['index_id']=index_json[case['tag']]
            db_item=TestCase(**detail)
            db.add(db_item)

        db.commit()

        #更新排序号
        case_list=db.query(TestCase).filter(TestCase.sort_num==0).all()
        for case in case_list:
            case.sort_num=case.id
        db.commit()

        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()


        return {'code':200,'msg':'导入数据成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/copy_case")
async def copy_case(item:testcase_schemas.CopyCaseItem,db:Session=Depends(get_case_db)):
    '''
    复制用例
    '''
    try:
        case_list=db.query(TestCase).filter(TestCase.id.in_(item.case_id_list),TestCase.isrecovery==0,TestCase.isdelete==0).all()
        index_info=db.query(CaseIndex).filter(CaseIndex.id_path==item.id_path[-1]).first()
        for case in case_list:
            case_item=case.to_json()
            case_item['index_id']=item.id_path[-1]
            case_item['case_type']=index_info.type
            case_item['review_state']=0
            case_item['create_name']=item.create_name
            del case_item['id']

            db_item = TestCase(**case_item)
            db.add(db_item)

        db.commit()

        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()

        return {'code': 200, 'msg': '操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



