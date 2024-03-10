from fastapi import APIRouter
from fastapi import Depends
from qa_dal.sys import promodule_schemas
from qa_dal.database import get_api_db
from sqlalchemy.orm import Session
from qa_dal.models import ProModule,Api
from qa_dal import qa_uitls
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/promodule",
    tags=["系统配置-项目信息"]
)


@router.get("/list")
async def search_modulelist(pro_code:str='',module_name:str='',page_num:int=1,page_size:int=10,db: Session = Depends(get_api_db)):
    '''
    项目模块列表
    :param pro_code:
    :param module_name:
    :param tester:
    :param page_num:
    :param page_size:
    :param db:
    :return:
    '''
    try:

        sql_param_list = [ProModule.isdelete == 0]  # 基础搜索条件
        if pro_code.__len__() > 0: sql_param_list.append(ProModule.pro_code==pro_code)
        if module_name.__len__() > 0: sql_param_list.append(ProModule.module_name.like('%{}%'.format(module_name)))  # 追加条件

        return qa_uitls.page_info(db.query(ProModule).filter(*sql_param_list).order_by(ProModule.id.desc()).all(),page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def get_module_detail(id:int,db:Session = Depends(get_api_db)):
    '''
    项目模块详情
    :param id:
    :param Session:
    :return:
    '''
    try:
        return {'code':200,'msg':db.query(ProModule).filter(ProModule.id==id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/del")
async def del_module(item:promodule_schemas.ProModuleBase,db:Session = Depends(get_api_db)):
    try:
        promodule=db.query(ProModule).filter(ProModule.id==item.id).first()
        if promodule == None: return {'code': 201, 'msg': '无效ID!'}

        api_count= db.query(Api).filter(Api.pro_code==promodule.pro_code,Api.module_code==promodule.module_code,Api.isdelete==0).count()
        if api_count>0: return {'code': 202, 'msg': '该模块下已存在接口，不能删除!'}


        promodule.isdelete=-(promodule.id)
        db.commit()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.post("/save")
async def save_module(promodule_items:promodule_schemas.ProModuleSave,db:Session = Depends(get_api_db)):
    try:
        if promodule_items.id==0:
            db_item = ProModule(**promodule_items.dict())
            db.add(db_item)
            db.commit()
        else:

            promodule = db.query(ProModule).filter(ProModule.id == promodule_items.id).first()

            if promodule == None: return {'code': 201, 'msg': '无效ID!'}

            promodule.module_name = promodule_items.module_name
            promodule.remark = promodule_items.remark
            db.commit()

        return {'code': 200, 'msg': '操作成功!'}
    except IntegrityError:
        return {'code':201,'msg':'模块编号{}已存在,请重新输入!'.format(promodule_items.module_code)}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}








