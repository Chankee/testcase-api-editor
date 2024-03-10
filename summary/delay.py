from sqlalchemy import func
from fastapi import APIRouter
from fastapi import Depends
from qa_dal.testmanage import testcase_schemas
from qa_dal.database import get_case_db
from sqlalchemy.orm import Session
from sqlalchemy import or_
from qa_dal.models import Delay
from qa_dal import qa_uitls
from pydantic import BaseModel
from typing import List, Optional,Dict,Union


router = APIRouter(
    prefix="/summary/delay",
    tags=["延期提测"]
)


@router.get("/list")
async  def get_delay_list(pro_code:str='',version_name:str='',page_num:int=1,page_size:int=10,db:Session=Depends(get_case_db)):
    try:
        sql_param=[Delay.isdelete==0]
        if pro_code.__len__()>0: sql_param.append(Delay.pro_code==pro_code)
        if version_name.__len__()>0: sql_param.append(Delay.version_name==version_name)

        result=db.query(Delay).filter(*sql_param).order_by(Delay.id.desc()).all()

        return qa_uitls.page_info(result, page_num, page_size)

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


class DelayBase(BaseModel):
    id:Optional[int]
    pro_code:Optional[str]
    version_name:Optional[str]
    user_name:Optional[str]
    delay_demand:Optional[str]
    delay_time:Optional[str]



@router.post("/save")
async def save_delay(delay_item: DelayBase, db:Session=Depends(get_case_db)):
    '''
    创建用例评审
    :param review:
    :param db:
    :return:
    '''
    try:
        if delay_item.id==0:
            db_item=Delay(**delay_item.dict())
            db.add(db_item)
            db.commit()
        else:
            delay = db.query(Delay).filter(Delay.id == delay_item.id).first()

            if delay == None: return {'code': 201, 'msg': '无效ID!'}

            delay.pro_code = delay_item.pro_code
            delay.version_name = delay_item.version_name
            delay.user_name = delay_item.user_name
            delay.delay_demand = delay_item.delay_demand
            delay.delay_time = delay_item.delay_time
            db.commit()
        return {'code': 200, 'msg': '操作成功!'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get("/detail")
async def get_detail(id:int,db:Session=Depends(get_case_db)):
    '''
    创建延期内容
    :param id:
    :param db:
    :return:
    '''
    try:
        return {'code': 200, 'msg': db.query(Delay).filter(Delay.id == id).first()}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post("/del")
async def del_delay(delay: DelayBase, db:Session=Depends(get_case_db)):
    '''
    删除
    :param :
    :param db:
    :return:
    '''
    try:

        delay_item = db.query(Delay).filter(Delay.id == delay.id).first()
        if delay_item == None: return {'code': 201, 'msg': '无效ID!'}

        delay_item.isdelete = 1
        db.commit()
        return {'code': 200, 'msg': '操作成功！'}


    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



