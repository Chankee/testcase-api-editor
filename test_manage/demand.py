from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import demand_schemas
from qa_dal.database import get_case_db
from sqlalchemy.orm import Session
from qa_dal import qa_uitls
from qa_dal.models import Demand,Version,TestCase

router = APIRouter(
    prefix="/tm/demand",
    tags=["测试管理-需求模块"]
)


@router.get("/list")
async def search_demand_list(version_id:int=0,pro_code:str='',demand_name:str='',tester:str='',page_num:int=1,page_size:int=10,db:Session=Depends(get_case_db)):
    '''
    查询需求模块
    :param pro_code:
    :param demand_name:
    :param tester:
    :param page_num:
    :param page_size:
    :param db:
    :return:
    '''
    try:
        sql_param_list = [Demand.pro_code == pro_code, Demand.isdelete == 0]  # 基础搜索条件
        if version_id > 0: sql_param_list.append(Demand.version_id == version_id)
        if demand_name.__len__() > 0: sql_param_list.append(Demand.demand_name.like('%{}%'.format(demand_name)))  # 追加条件
        if tester.__len__() > 0: sql_param_list.append(Demand.tester == tester)

        return qa_uitls.page_info(db.query(Demand).filter(*sql_param_list).order_by(Demand.id.desc()).all(), page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/save")
async def add_demand(demand_items: demand_schemas.DemandSave, db:Session=Depends(get_case_db)):
    '''
    创建/编辑需求模型
    :param demand:
    :param db:
    :return:
    '''
    try:
        if demand_items.id==0:
            db_item = Demand(**demand_items.dict())
            db.add(db_item)
            db.commit() #创建

        else:

            demand = db.query(Demand).filter(Demand.id == demand_items.id).first()

            if demand == None: return {'code': 201, 'msg': '无效ID!'}

            demand.demand_name = demand_items.demand_name
            demand.module_code = demand_items.module_code
            demand.tester = demand_items.tester
            demand.issuspend = demand_items.issuspend
            demand.plan_start = demand_items.plan_start
            demand.plan_end = demand_items.plan_end
            demand.version_id = demand_items.version_id
            demand.jira_num = demand_items.jira_num
            demand.jira_state = demand_items.jira_state
            demand.remark = demand_items.remark
            db.commit() #编辑

        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get("/detail")
async def get_demand_detail(id:int,db:Session=Depends(get_case_db)):
    '''
    需求模块详情
    :param id:
    :param db:
    :return:
    '''
    try:
        return {'code': 200, 'msg': db.query(Demand).filter(Demand.id == id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/del")
async def del_demand(demand: demand_schemas.DemandBase, db:Session=Depends(get_case_db)):
    '''
    修改需求模块
    :param demand:
    :param db:
    :return:
    '''
    try:

        demand = db.query(Demand).filter(Demand.id == demand.id).first()
        if demand == None: return {'code': 201, 'msg': '无效ID!'}

        if db.query(TestCase).filter(TestCase.demand_id==demand.id,TestCase.isdelete==0,TestCase.isrecovery==0).count()>0: return {'code': 203, 'msg': '需求下已存在用例,不能删除!'}

        demand.isdelete = 1
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



def update_reality_time(db:Session,id:int,time_info:str,type:str):
    '''
    修改时间
    :param db:
    :param item:
    :param type:
    :return:
    '''
    demand = db.query(Demand).filter(Demand.id == id).first()
    if demand and type=='start':
        demand.reality_start=time_info
        db.commit()
    elif demand and type=='end':
        demand.reality_end=time_info
        db.commit()