from typing import List, Union

from fastapi import APIRouter, File, UploadFile
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import Session

from qa_dal import qa_uitls
from qa_dal.database import get_case_db
from qa_dal.models import TestCase,CaseIndex,PlanCase
from qa_dal.testmanage import caseindex_schemas
import json
import jsonpath
from uitls.redis_clt import redis_clt

router = APIRouter(
    prefix="/tm/caselist",
    tags=["测试管理-测试用例"]
)



@router.post("/saveindex")
async def saveindex(item: caseindex_schemas.SaveIndex, db:Session=Depends(get_case_db)):
    '''创建/编辑目录'''
    try:
        if item.id>0:
            index_content = db.query(CaseIndex).filter(CaseIndex.id == item.id).first()
            if index_content == None: return {'code': 201, 'msg': '未找到对应的目录！'}
            index_content.name=item.name
            index_content.remark=item.remark
            db.commit()
        else:
            #创建目录
            index_item = item.dict()
            if index_item['parent_id_path'] in ('activity','version','release'): index_item['parent_id_path']='0'
            del index_item['id']
            db_item = CaseIndex(**index_item)
            db.add(db_item)
            db.commit()

            # 0是第一层,修改数据
            index_info = db.query(CaseIndex).filter(CaseIndex.id == db_item.id).first()
            if index_info == None: return {'code': 201, 'msg': '未找到对应的目录！'}
            if index_item['parent_id_path'] == '0':
                index_info.id_path = str(index_info.id)
            else:
                index_info.id_path = '{}_{}'.format(index_info.parent_id_path, index_info.id)
            index_info.sort = index_info.id
            index_info.level = len(index_info.id_path.split('_'))
            db.commit()

        #删除缓存
        r=redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()

        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/selecttree")
async def selecttree(pro_code:str,isimport:int=-1, db: Session = Depends(get_case_db)):

    try:
        #判断是否已有缓存

        tree_list=[
            {
                'name': '活动用例',
                'id_path': 'activity',
                'type':0,
                'parent_id_path': '0',
                'level':0,
                'total':0,
                'children': []
            },
            {
                'name': '版本用例',
                'id_path': 'version',
                'type': 1,
                'parent_id_path': '0',
                'level': 0,
                'total':0,
                'children': []
            },
            {
                'name': '发布性用例',
                'id_path': 'release',
                'type':2,
                'parent_id_path': '0',
                'level': 0,
                'total':0,
                'children': []
            }
        ]


        #获取所有目录和总数据
        index_list = db.query(CaseIndex).filter(CaseIndex.pro_code == pro_code, CaseIndex.isdelete == 0).order_by(CaseIndex.sort.asc()).all()
        case_total= db.query(func.count(TestCase.id).label('total'),TestCase.index_id,TestCase.case_type).filter(TestCase.pro_code==pro_code,TestCase.isrecovery==0,TestCase.isdelete==0).group_by(TestCase.index_id,TestCase.case_type).all()
        #计算用例数
        total_json={}
        for case in case_total:
            if case.case_type not in (0,1,2): continue
            if case.index_id in (None,''): continue
            total_json[case.index_id]=case.total
            tree_list[case.case_type]['total']+=case.total


        format_tree = generate_tree(index_list, '0',total_json,isimport)

        #传入树形数据
        tre_type = {0: tree_list[0]['children'], 1: tree_list[1]['children'], 2: tree_list[2]['children']}
        for tree in format_tree:
            tre_type[tree['type']].append(tree)

        return {'code':200,'msg':tree_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/indextree")
async def indextree(pro_code:str, db: Session = Depends(get_case_db)):
    try:

        tree_list=[
            {
                'name': '活动用例',
                'id_path': 'activity',
                'type':0,
                'parent_id_path': '0',
                'level':0,
                'total':0,
                'id': 'activity',
                'children': []
            },
            {
                'name': '版本用例',
                'id_path': 'version',
                'type': 1,
                'parent_id_path': '0',
                'level': 0,
                'total':0,
                'id': 'version',
                'children': []
            },
            {
                'name': '发布性用例',
                'id_path': 'release',
                'type':2,
                'parent_id_path': '0',
                'level': 0,
                'total':0,
                'id': 'release',
                'children': []
            },
            {
                'name': '用例回收站',
                'type': 3,
                'id_path': 'recovery',
                'parent_id_path': '0',
                'level': -1,
                'total':db.query(TestCase.id).filter(TestCase.isrecovery==1,TestCase.isdelete==0,TestCase.pro_code==pro_code).count(),
                'children': []
            }
        ]


        #获取所有目录和总数据
        index_list = db.query(CaseIndex).filter(CaseIndex.pro_code == pro_code, CaseIndex.isdelete == 0).order_by(CaseIndex.sort.asc()).all()
        case_total= db.query(func.count(TestCase.id).label('total'),TestCase.index_id,TestCase.case_type).filter(TestCase.pro_code==pro_code,TestCase.isrecovery==0,TestCase.isdelete==0).group_by(TestCase.index_id,TestCase.case_type).all()
        #计算用例数
        total_json={}
        for case in case_total:
            if case.case_type not in (0,1,2): continue
            if case.index_id in (None,''): continue
            total_json[case.index_id]=case.total
            tree_list[case.case_type]['total']+=case.total


        format_tree = generate_tree(index_list, '0',total_json)

        #传入树形数据
        tre_type = {0: tree_list[0]['children'], 1: tree_list[1]['children'], 2: tree_list[2]['children']}
        for tree in format_tree:
            tre_type[tree['type']].append(tree)

        return {'code':200,'msg':tree_list}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def generate_tree(source, parent,total_json,isimport=-1):

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
        if item_json['id_path'] in total_dic:
            item_json['total'] = total_dic[item_json['id_path']]
        if isimport != -1 and item_json['level'] == 3: continue
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




@router.post("/move_index")
async def move_index(item: caseindex_schemas.MoveIndex, db:Session=Depends(get_case_db)):
    try:
        base_index=db.query(CaseIndex).filter(CaseIndex.id==item.base_id,CaseIndex.isdelete==0).first()
        target_index=db.query(CaseIndex).filter(CaseIndex.id==item.target_id,CaseIndex.isdelete==0).first()
        if base_index==None or target_index==None: return {'code':202,'msg':'目录不存在!'}

        if base_index.parent_id_path==target_index.parent_id_path:   #相同目录则交换顺序
            base_sort=base_index.sort
            target_sort=target_index.sort

            base_index.sort=target_sort
            target_index.sort=base_sort
            db.commit()
        else:
            #更新目录
            old_id_path=base_index.id_path
            old_parent_id_path=base_index.parent_id_path
            new_parent_id_path=target_index.parent_id_path

            # 更换顺序
            base_sort = base_index.sort
            target_sort = target_index.sort

            base_index.sort = target_sort
            target_index.sort = base_sort
            db.commit()

            #判断是否有用例
            if db.query(TestCase).filter(TestCase.index_id.like('{}%'.format(old_id_path))).count()>0:
                #连表查询，获取符合条件的目录和用例id
                join_id_list=db.query(CaseIndex.id,TestCase.id.label('case_id')).join(TestCase,TestCase.index_id==CaseIndex.id_path).filter(CaseIndex.id_path.like('{}%'.format(old_id_path)),CaseIndex.isdelete==0).all()
                case_id_sql=[]
                for jl in join_id_list:
                    case_id_sql.append(jl.case_id)


                update_index_list=db.query(CaseIndex).filter(CaseIndex.id_path.like('{}%'.format(old_id_path)),CaseIndex.isdelete==0).all()
                for up_index in update_index_list:
                    up_index.parent_id_path=up_index.parent_id_path.replace(old_parent_id_path,new_parent_id_path)
                    up_index.id_path=up_index.id_path.replace(old_parent_id_path,new_parent_id_path)
                    if up_index.type!=target_index.type: up_index.type=target_index.type
                db.commit()

                if len(case_id_sql) == 0: return {'code': 200, 'msg': '操作成功！'}

                #更新用例
                case_list=db.query(TestCase).filter(TestCase.id.in_(case_id_sql)).all()
                for case in case_list:
                    case.index_id=case.index_id.replace(old_parent_id_path,new_parent_id_path)
                    if case.case_type!=target_index.type: case.case_type=target_index.type
                db.commit()

            else:
                # 连表查询，获取符合条件的目录和用例id
                update_index_list = db.query(CaseIndex).filter(CaseIndex.id_path.like('{}%'.format(old_id_path)),CaseIndex.isdelete==0).all()

                for up_index in update_index_list:
                    up_index.parent_id_path = up_index.parent_id_path.replace(old_parent_id_path, new_parent_id_path)
                    up_index.id_path = up_index.id_path.replace(old_parent_id_path, new_parent_id_path)
                    if up_index.type != target_index.type: up_index.type = target_index.type
                db.commit()


        #删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()

        return {'code':200,'msg':'操作成功！'}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/del_index")
async def del_index(item: caseindex_schemas.DelIndex, db:Session=Depends(get_case_db)):
    try:
        #先删目录
        index_list=db.query(CaseIndex).filter(CaseIndex.id_path.like('{}%'.format(item.id_path)),CaseIndex.isdelete==0).all()
        for index in index_list:
            index.isdelete=1
        db.commit()

        #再删用例
        case_list=db.query(TestCase).filter(TestCase.index_id.like('{}%'.format(item.id_path)),TestCase.isdelete==0,TestCase.isrecovery==0).all()
        for case in case_list:
            case.isdelete=1
            case.isrecovery=1
            case.recovery_people = item.recovery_people
        db.commit()


        # 删除缓存
        r = redis_clt(1).r()
        r.hdel("testcase_select_tree", item.pro_code)
        r.hdel("testcase_tree", item.pro_code)
        r.close()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/get_children")
async def get_children(pro_code:str,id_path:str,db:Session=Depends(get_case_db)):
    result=[]
    total_json={}
    total_list=[]
    type_json={'activity':0,'version':1,'release':2}
    if id_path in type_json.keys():
        result=db.query(CaseIndex).filter(CaseIndex.type==type_json[id_path],CaseIndex.pro_code == pro_code,CaseIndex.level==1, CaseIndex.isdelete == 0).order_by(CaseIndex.sort.asc()).all()
        total_list= db.query(func.count(TestCase.id).label('total'),TestCase.index_id).filter(TestCase.case_type==type_json[id_path],TestCase.pro_code==pro_code,TestCase.isrecovery==0,TestCase.isdelete==0).group_by(TestCase.index_id).all()


    #统计第一层的总数
    if len(total_list)>0 and id_path in type_json.keys():
        for total in total_list:
            if total.index_id.split('_')[0] in total_json.keys():
                total_json[total.index_id.split('_')[0]]+=total.total
            else:
                total_json[total.index_id.split('_')[0]]: total.total


    result_list = []
    for item in result:
        item_json=item.to_json()
        item_json['total']=0
        item_json['leaf']=True
        if item_json['id_path'] in total_json.keys() and id_path in type_json.keys():
            if item_json['total']>0: item_json['total']=total_json[item_json['id_path']]
            item_json['leaf']=False

        result_list.append(item_json)

    return result_list





@router.get("/add_plan_tree2")
async def add_plan_tree2(plan_id:int=0,plan_version_id:int=0,del_myself:int=0,pro_code:str='',db:Session=Depends(get_case_db)):
    '''新增用例计划树型'''

    try:

        #获取计划里的用例
        plancase = db.query(PlanCase.case_id).filter(PlanCase.plan_id == plan_id, PlanCase.isdelete == 0).all()
        plancase_id=[case.case_id for case in plancase]

        # 自测用例删除
        if del_myself == 1:
            myself_list=db.query(PlanCase).filter(PlanCase.plan_version_id==plan_version_id,PlanCase.plan_type == '研发自测',PlanCase.isdelete==0).all()
            myself_case=[myself.case_id for myself in myself_list]

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
                'children': [],
                'leaf': True
            },
            {
                'id': 'version',
                'name': '版本用例',
                'id_path': 'version',
                'type': 1,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'children': [],
                'leaf': True
            },
            {
                'id': 'release',
                'name': '发布性用例',
                'id_path': 'release',
                'type': 2,
                'parent_id_path': '0',
                'level': 0,
                'total': 0,
                'children': [],
                'leaf': True
            }
        ]

        case_total = db.query(func.count(TestCase.id).label('total'), TestCase.case_type).filter(*sql_param).group_by(TestCase.case_type).all()

        for case in case_total:
            if case.case_type in (0,1,2):
                tree_list[case.case_type]['total']=case.total
                if case.total>0: tree_list[case.case_type]['leaf']=False


        return {'code': 200, 'msg': tree_list}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/add_plan_children")
async def add_plan_children(plan_id:int=0,id_path:str='',level:int=0,plan_version_id:int=0,del_myself:int=0,pro_code:str='',db:Session=Depends(get_case_db)):

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
        sql_param = [TestCase.isdelete == 0, TestCase.isrecovery == 0, TestCase.pro_code == pro_code]
        if len(plancase_id) > 0: sql_param.append(TestCase.id.not_in(plancase_id))

        type_json = {'activity': 0, 'version': 1, 'release': 2}
        index_param=[CaseIndex.pro_code == pro_code, CaseIndex.isdelete == 0]

        if id_path in type_json.keys():
            index_param.append(CaseIndex.type==type_json[id_path])
            index_param.append(CaseIndex.level==1)
            sql_param.append(TestCase.case_type==type_json[id_path])

        else:
            index_param.append(CaseIndex.parent_id_path==id_path)
            sql_param.append(TestCase.index_id.like('{}%'.format(id_path)))



        index_list = db.query(CaseIndex).filter(*index_param).order_by(CaseIndex.sort.asc()).all()

        case_total = db.query(func.count(TestCase.id).label('total'), TestCase.case_type,TestCase.index_id).filter(*sql_param).group_by(TestCase.index_id,TestCase.case_type).all()

        total_json={}

        for total in case_total:
            if total.index_id in ('',None): continue
            total_key=total.index_id.split('_')

            #第一层
            if level==1 and total_key[0] in total_json.keys():
                total_json[total_key[0]] += total.total
            else:
                total_json[total_key[0]]=total.total

            #第二层
            if level==2 and len(total_key)>1:
                key='{}_{}'.format(total_key[0],total_key[1])
                if key in total_json.keys():
                    total_json[key] += total.total
                else:
                    total_json[key] = total.total

            # 第三层
            if level == 3 and len(total_key) ==3:
                if total.index_id in total_json.keys():
                    total_json[total.index_id] += total.total
                else:
                    total_json[total.index_id] = total.total

        index_result=[]
        for index in index_list:
            if index.level !=level: continue
            index_item=index.to_json()
            index_item['total']=0
            index_item['leaf']=True
            if index.id_path in total_json.keys(): index_item['total']=total_json[index.id_path]
            if index_item['total']>0 and level!=3:index_item['leaf']=False
            index_result.append(index_item)

        return {'code':200,'msg':index_result}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}