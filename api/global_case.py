import json

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from uitls.log import LOG
from qa_dal.models import GlobalCase
from qa_dal.api import global_case_schemas
from qa_dal.database import get_api_db

router = APIRouter(
    prefix="/api/global_case",
    tags=["全局用例"]
)


@router.get('/list')
def get_list(pro_code, db: Session = Depends(get_api_db)):
    '''
      查询全局变量
      :param case_id: 全局用例的id
      :db:
      :return:
      '''
    try:
        result = db.query(GlobalCase).filter(GlobalCase.pro_code == pro_code, GlobalCase.isdelete == 0).all()
        return {'code': 200, 'msg': '获取成功', 'data': result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get('/get_select_case')
def get_select_case(case_id, db: Session = Depends(get_api_db)):
    '''
      查询全局变量
      :param case_id: 全局用例的id
      :db:
      :return:
      '''
    try:
        result = db.query(GlobalCase).filter(GlobalCase.id == case_id).first()
        return {'code': 200, 'msg': '获取成功', 'data': result}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post('/save_gcase')
def save_golbal_case(items: global_case_schemas.GlobalCaseSave, db: Session = Depends(get_api_db)):
    '''

    :param items: 保存全局用例信息
    :param db:
    :return:
    '''
    try:
        case = db.query(GlobalCase).filter(GlobalCase.join_case_id == items.join_case_info[2],
                                           GlobalCase.pro_code == items.pro_code,
                                           GlobalCase.isdelete == 0).first()

        case2 = db.query(GlobalCase).filter(
            GlobalCase.pro_code == items.pro_code, GlobalCase.isdelete == 0,
            GlobalCase.assert_case_id == items.assert_case_info[2]).first()

        if case != None or case2 != None:
            return {'code': 201, 'msg': '保存失败,已存在相同的全局用例'}

        db_item = GlobalCase(**items.dict())
        db_item.join_case_id = items.join_case_info[2]
        db_item.assert_case_id = items.assert_case_info[2]
        db_item.param_value = json.dumps({})
        db_item.join_case_info = json.dumps(items.join_case_info)
        db_item.assert_case_info = json.dumps(items.assert_case_info)
        del db_item.id
        db.add(db_item)
        db.commit()
        return {'code': 200, 'msg': '保存成功'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post('/edit_gcase')
def edit_global_case(items: global_case_schemas.GlobalCaseSave, db: Session = Depends(get_api_db)):
    """

    :param items:
    :param db:
    :return:
    """
    try:
        case = db.query(GlobalCase).filter(GlobalCase.id == items.id, GlobalCase.pro_code == items.pro_code).first()

        if case == None:
            return {'code': 202, 'msg': '查询用例id失败'}

        case.id = items.id
        case.global_case_name = items.global_case_name
        case.join_case_id = items.join_case_info[2]
        case.assert_case_id = items.assert_case_info[2]
        case.param_value = items.param_value
        case.pro_code = items.pro_code
        case.isdelete = items.isdelete
        case.join_case_info = json.dumps(items.join_case_info)
        case.assert_case_info = json.dumps(items.assert_case_info)
        db.commit()
        return {'code': 200, 'msg': '修改成功'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/del")
async def del_case(items: global_case_schemas.GlobalCaseSave, db: Session = Depends(get_api_db)):
    '''
    删除环境信息
    :param item:
    :param db:
    :return:
    '''
    try:
        case = db.query(GlobalCase).filter(GlobalCase.id == items.id).first()
        if case == None: return {'code': 201, 'msg': '无效ID！'}
        case.isdelete = 1
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}
