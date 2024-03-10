#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2021/7/05 10:17
# @Author：kee
# @Description：接口用例

from fastapi import APIRouter
from qa_api_dal.case.case_dal import Case_Dal
from api.run_case_uitls.run_business import Run_Business
from api.run_case_uitls.case_plugin import Case_Plugin

from qa_dal.models import Case,Global,ApiData,Api,ApiHost
from api.run_case_uitls.global_case_run import Global_case
from sqlalchemy.orm import Session
from qa_dal.database import get_api_db
from qa_dal.api import case_schemas
from fastapi import Depends
from typing import Optional
from pydantic import BaseModel
from qa_dal import qa_uitls
from urllib.parse import urlparse
import json


router = APIRouter(
    prefix="/case",
    tags=["接口信息库[/api]"]
)

@router.get('/check_param')
async def check_param(pro_code:str,extract_name:str,db:Session=Depends(get_api_db)):
    try:
        if db.query(Case).filter(Case.extract_param.like('%{}%'.format(extract_name)),Case.pro_code==pro_code,Case.isdelete==0).count()>1:
            return {'code': 201, 'msg': '变量名称已存在类似名称，请重新输入!'}

        if db.query(Global).filter(Global.global_param.like('%{}%'.format(extract_name)),Global.pro_code==pro_code,Global.isdelete==0).count()>1:
            return {'code': 201, 'msg': '变量名称已存在类似名称，请重新输入!'}

        return {'code':200,'msg':'检测成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get('/list',response_model=case_schemas.CaseListShow)
async def search_case(pro_code:str='',api_id_list:str='',case_name:str='',page_num:int=1,page_size:int=10,db:Session=Depends(get_api_db)):
    '''
    搜索用例
    :param api_id:
    :param case_name:
    :param page_num:
    :param page_size:
    :return:
    '''
    try:
        sql_param =[Case.pro_code==pro_code,Case.isdelete==0]

        # 追加sql条件
        if api_id_list.__len__()!=0:
            id_list='[{}]'.format(api_id_list[:-1])
            sql_param.append(Case.api_id.in_(eval(id_list)))
        if case_name.__len__() != 0: sql_param.append(Case.case_name.like('%{}%'.format(case_name)))

        result=db.query(Case).filter(*sql_param).order_by(Case.id.desc()).all()
        return qa_uitls.page_info(result, page_num, page_size)
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}






@router.post('/create')
async def add_case(item:case_schemas.CaseCreate,db:Session=Depends(get_api_db)):
    '''
    新增用例
    :param item:
    :param db:
    :return:
    '''
    try:
        item.request_body = json.dumps(item.request_body)
        item.header = json.dumps(item.header)
        item.header_param = json.dumps(item.header_param)
        item.extract_param = json.dumps(item.extract_param)
        item.assert_param = json.dumps(item.assert_param)
        item.join_param = json.dumps(item.join_param)
        item.assert_list = json.dumps(item.assert_list)
        item.api_id = item.api_id[1]

        case_info=item.dict()
        del case_info['request_body'],case_info['run_host'],case_info['assert_list']
        case_item = Case(**case_info)
        db.add(case_item)
        db.commit()  # 添加
        db.refresh(case_item)


        # 添加默认数据
        case_data={'request_body':item.request_body,
                   'assert_list':json.dumps(item.assert_list),
                   'case_id':case_item.id,
                   'run_host':item.run_host,
                   'data_name':item.case_name,
                  'isdelete':0}

        data_item = ApiData(**case_data)
        db.add(data_item)
        db.commit()

        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post('/update_case')
async def update_case(item:case_schemas.CaseUpdate,db:Session=Depends(get_api_db)):
    '''
    修改用例
    :param api:
    :return:
    '''
    try:
        case=db.query(Case).filter(Case.id==item.id).first()
        if case==None: return {'code':201,'msg':'无效ID！'}
        case.case_name = item.case_name
        case.url_param = item.url_param
        case.header = json.dumps(item.header)
        case.header_param = json.dumps(item.header_param)
        case.extract_param = json.dumps(item.extract_param)
        case.preconditions = item.preconditions
        case.assert_param = json.dumps(item.assert_param)
        case.join_param = json.dumps(item.join_param)
        case.wait_time = item.wait_time
        db.commit()

        # 修改默认数据
        case_data=db.query(ApiData).filter(ApiData.case_id==item.id,ApiData.data_group_num=='df',ApiData.isdelete==0).first()
        if case_data==None: return {'code': 201, 'msg': '查找不到默认数据！'}

        case_data.request_body = json.dumps(item.request_body)
        case_data.assert_list=json.dumps(item.assert_list)
        case_data.run_host = item.run_host
        db.commit()

        return {'code':200,'msg':'操作成功！'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



@router.get('/case_detail')
async def case_detail(id: int, db: Session = Depends(get_api_db)):
    try:

        case = db.query(Case).filter(Case.id == id).first()
        if case == None: return {'code': 201, 'msg': '无效ID！'}
        case_data = db.query(ApiData).filter(ApiData.case_id == id, ApiData.data_group_num == 'df').first()
        api = db.query(Api).filter(Api.id == case.api_id).first()
        host = db.query(ApiHost).filter(ApiHost.id == api.host_id).first()

        case_json = {}
        case_json['id']=id
        case_json['api_name'] = api.api_name
        case_json['api_id'] = api.id
        case_json['case_name']=case.case_name
        case_json['wait_time']=case.wait_time
        case_json['url_param']=case.url_param
        case_json['preconditions']=case.preconditions
        case_json['url'] = api.url
        case_json['method'] = api.method
        case_json['module_code'] = api.module_code
        case_json['test_host'] = host.test_host
        case_json['uat_host'] = host.uat_host
        case_json['prd_host'] = host.prd_host
        case_json['api_select'] = [api.module_code, str(case.api_id)]
        case_json['request_body'] = json.loads(case_data.request_body)
        case_json['assert_list'] = json.loads(case_data.assert_list)
        case_json['host_json'] = {'test_host': host.test_host,
                                  'uat_host': host.uat_host,
                                  'prd_host': host.prd_host}
        case_json['run_host'] = case_data.run_host
        case_json['header'] = json.loads(case.header)
        case_json['header_param'] = json.loads(case.header_param)
        case_json['join_param'] = json.loads(case.join_param)
        case_json['extract_param'] = json.loads(case.extract_param)
        case_json['assert_param'] = json.loads(case.assert_param)
        case_json['host'] = case_json.get(case_data.run_host)

        return {'code': 200, 'msg': case_json}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




class CaseItem(BaseModel):
    id:Optional[int]
    api_select:Optional[list]
    url:Optional[str]
    host:Optional[str]
    host_json:Optional[dict]
    method:Optional[str]
    pro_code:Optional[str]
    case_name:Optional[str]
    request_body:Optional[dict]
    url_param:Optional[str]
    header:Optional[dict]
    preconditions:Optional[str]
    header_param:Optional[list]
    join_param:Optional[list]
    extract_param:Optional[list]
    assert_param:Optional[list]
    create_name:Optional[str]
    run_host:Optional[str]
    wait_time:Optional[int]
    assert_list:Optional[list]



@router.post('/save_case_run')
def save_case_run(case:CaseItem,db: Session = Depends(get_api_db)):
    '''
    保存用例执行
    :param case:
    :return:
    '''
    #try:
    global_value=Global_case(case.pro_code,db)
    cp = dict(Case_Plugin(dict(case), global_value))
    detail_info = {}

    # 提取参数
    detail_info['extract_param'] = cp['extract_info']

    # 断言
    detail_info['assert_param'] = cp['assert_info']['msg']

    # 详细信息
    detail_info['error_tag'] = cp['error_tag']
    detail_info['api_url'] = cp['url']
    detail_info['method'] = case.method
    detail_info['header'] = cp['header']
    detail_info['request_body'] = cp['request_body']['result']
    detail_info['response_body'] = cp['response_body']

    return {'code': 200, 'msg': detail_info}
    # except Exception as ex:
    #     error_line = ex.__traceback__.tb_lineno
    #     error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
    #     return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



### 快捷调试模型
class DebugItem(BaseModel):
    # 接口参数
    pro_code: Optional[str]
    api_name: Optional[str]
    module_code: Optional[str]
    dev_name: Optional[str]
    method: Optional[str]
    url: Optional[str]
    host_id: Optional[str]
    remark: Optional[str]
    tag: Optional[str]
    # 用例参数
    case_name: Optional[str]
    request_body: Optional[dict]
    url_param: Optional[str]
    header: Optional[dict]
    preconditions: Optional[str]
    header_param: Optional[list]
    join_param: Optional[list]
    extract_param: Optional[list]
    assert_param: Optional[list]
    save_type: Optional[int]
    create_name: Optional[str]
    run_host: Optional[str]
    wait_time: Optional[int]
    assert_list:Optional[list]



@router.post('/run')
def run_case(item:DebugItem,db: Session = Depends(get_api_db)):
    '''
    运行单个用例
    :param db:
    :return:
    '''
    try:

        global_value=Global_case(item.pro_code,db)  # 全局变量
        #拆解url
        cut_url = urlparse(item.url)  # 拆分url
        cp_info=item.dict()
        cp_info['host']='{}://{}'.format(cut_url.scheme,cut_url.netloc)
        cp_info['url']=cut_url.path
        cp=dict(Case_Plugin(cp_info,global_value))

        detail_info={}

        #提取参数
        detail_info['extract_param']=cp['extract_info']

        #断言
        detail_info['assert_param']=cp['assert_info']['msg']

        #详细信息
        detail_info['error_tag']=cp['error_tag']
        detail_info['api_url']=cp['url']
        detail_info['method']=item.method
        detail_info['header']=cp['header']['result']
        detail_info['request_body'] =cp['request_body']['result']
        detail_info['response_body']=cp['response_body']

        return {'code': 200, 'msg': detail_info}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        LOG().ex_position(ex)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.get('/baseinfo')
async def base_info(pro_code:str):
    '''
    基础数据，包括项目模块、host、tag、dev_name
    :param pro_code:
    :return:
    '''
    try:
        ca=Case_Dal().base_info(pro_code)
        return {'code':200,'msg':{'module_list':[{'label':md['module_name'],'value':md['module_code']} for md in ca[0]],
                                  'dev_name_list': [dev['user_name'] for dev in ca[1]],
                                  'tag_list': [tag['tag'] for tag in ca[2]],
                                  'host_list':[{'label':host['host_name'],'value':host['id']} for host in ca[3]]}}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post('/save_api_case')
async def save_api_case(item:DebugItem,db: Session = Depends(get_api_db)):
    '''
    保存接口和用例
    :param db:
    :return:
    '''
    try:
        cut_url=urlparse(item.url)  #拆分url
        #拆解url参数
        if item.url_param == '' and cut_url.query != '':
            item.url_param = cut_url.query

        #保存接口
        if item.save_type==0:

            if db.query(Api).filter(Api.url==cut_url.path,Api.pro_code==item.pro_code,Api.isdelete==0).count()>0: return {'code':203,'msg':'接口已存在！'}

            api_info={
                'api_name':item.api_name,
                'method':item.method,
                'header':json.dumps(item.header),
                'url':cut_url.path,
                'host':'{}://{}'.format(cut_url.scheme,cut_url.netloc),
                'request_body':json.dumps(item.request_body),
                'response_body':'',
                'dbsource':1,
                'pro_code':item.pro_code,
                'module_code':item.module_code,
                'tag':item.tag,
                'remark':item.remark,
                'host_id':item.host_id,
                'dev_name':item.dev_name
            }
            db_item=Api(**api_info)
            db.add(db_item)
            db.commit()
            return {'code':200,'msg':'操作成功！'}
        else:
            #保存接口和用例
            check_api_id=db.query(Api.id).filter(Api.url == cut_url.path, Api.pro_code == item.pro_code,Api.isdelete == 0).first()
            if check_api_id!=None:
                case_info={
                    'api_id':check_api_id.id,
                    'case_name':item.case_name,
                    'url_param':item.url_param,
                    'header':json.dumps(item.header),
                    'extract_param':json.dumps(item.extract_param),
                    'preconditions':item.preconditions,
                    'assert_param':json.dumps(item.assert_param),
                    'create_name':item.create_name,
                    'header_param':json.dumps(item.header_param),
                    'join_param':json.dumps(item.join_param),
                    'pro_code':item.pro_code,
                    'wait_time':item.wait_time
                }

                case_item=Case(**case_info)
                db.add(case_item)
                db.commit()
                db.refresh(case_item)

                #添加默认数据
                data_info={
                    'data_group_name':'默认参数',
                    'business_id':0,
                    'request_body':json.dumps(item.request_body),
                    'case_id':case_item.id,
                    'data_group_num':'df',
                    'data_name':item.case_name,
                    'assert_list':json.dumps(item.assert_list),
                    'run_host':item.run_host
                }
                data_item=ApiData(**data_info)
                db.add(data_item)
                db.commit()

                return {'code': 203, 'msg': '接口已存在！用例已保存'}
            else:
                api_info = {
                    'api_name': item.api_name,
                    'method': item.method,
                    'header': json.dumps(item.header),
                    'url': cut_url.path,
                    'host': '{}://{}'.format(cut_url.scheme, cut_url.netloc),
                    'request_body': json.dumps(item.request_body),
                    'response_body': '{}',
                    'dbsource': 1,
                    'pro_code': item.pro_code,
                    'module_code': item.module_code,
                    'tag': item.tag,
                    'remark': item.remark,
                    'host_id': item.host_id,
                    'dev_name': item.dev_name
                }
                api_item = Api(**api_info)
                db.add(api_item)
                db.commit()
                db.refresh(api_item)

                case_info = {
                    'api_id': api_item.id,
                    'case_name': item.case_name,
                    'url_param': item.url_param,
                    'header': json.dumps(item.header),
                    'extract_param': json.dumps(item.extract_param),
                    'preconditions': item.preconditions,
                    'assert_param': json.dumps(item.assert_param),
                    'create_name': item.create_name,
                    'header_param': json.dumps(item.header_param),
                    'join_param': json.dumps(item.join_param),
                    'pro_code': item.pro_code,
                    'wait_time': item.wait_time
                }

                case_item = Case(**case_info)
                db.add(case_item)
                db.commit()
                db.refresh(case_item)

                # 添加默认数据
                data_info = {
                    'data_group_name': '默认参数',
                    'business_id': 0,
                    'request_body': json.dumps(item.request_body),
                    'case_id': case_item.id,
                    'data_group_num': 'df',
                    'data_name': item.case_name,
                    'assert_list': json.dumps(item.assert_list),
                    'run_host': item.run_host
                }
                data_item = ApiData(**data_info)
                db.add(data_item)
                db.commit()

                return {'code': 200, 'msg': '操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}




@router.post('/del')
async def delete_case(item:case_schemas.CaseBase,db:Session=Depends(get_api_db)):
    '''
    删除用例
    :param ca:
    :return:
    '''
    try:

        case=db.query(Case).filter(Case.id==item.id).first()
        if case==None: return {'code':201,'msg':'无效ID！'}
        if case.business_list not in ('[]','',None): return {'code':202,'msg':'该用例已加入业务流，不能删除！'}
        case.isdelete = 1
        db.commit()

        #删除默认数据
        case_data=db.query(ApiData).filter(ApiData.case_id==item.id,ApiData.data_group_num=='df').first()
        if case_data==None: return {'code':203,'msg':'查找不到默认数据！'}
        case_data.isdelete =1
        db.commit()

        return {'code':200,'msg':'操作成功！'}

    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}



class CaseID(BaseModel):
    case_id_list:list
    pro_code:str


from uitls.log import LOG
@router.post('/runs')
def run_cases(ci:CaseID,db:Session=Depends(get_api_db)):
    '''
    运行多个用例
    :param db:
    :return:
    '''

    run_reslut_list=[]
    global_value=Global_case(ci.pro_code,db)  # 全局变量

    #查询执行用例
    run_case_info = db.query(Case, Api, ApiData).filter(Case.id.in_(ci.case_id_list),Case.api_id == Api.id, ApiData.data_group_num == 'df',
                 ApiData.case_id == Case.id).all()


    total_count=run_case_info.__len__()
    fail_count = 0
    error_count = 0

    for caseinfo in run_case_info:
        case_host_json = db.query(ApiHost).filter(ApiHost.id == caseinfo.Api.host_id).first()
        case_host_json = case_host_json.to_json()

        detail_info = {
            'api_name': caseinfo.Api.api_name,
            'assert_list': json.loads(caseinfo.ApiData.assert_list),
            'case_name': caseinfo.Case.case_name,
            'extract_param': json.loads(caseinfo.Case.extract_param),
            'header': json.loads(caseinfo.Case.header),
            'header_param': json.loads(caseinfo.Case.header_param),
            'host': case_host_json[caseinfo.ApiData.run_host],
            'host_json': case_host_json,
            'join_param': json.loads(caseinfo.Case.join_param),
            'method': caseinfo.Api.method,
            'preconditions': caseinfo.Case.preconditions,
            'pro_code': ci.pro_code,
            'request_body': json.loads(caseinfo.ApiData.request_body),
            'url': caseinfo.Api.url,
            'url_param': caseinfo.Case.url_param,
            'wait_time': caseinfo.Case.wait_time
        }

        cp = dict(Case_Plugin(detail_info,global_value))


        # 提取参数
        detail_info['extract_param'] = cp['extract_info']
        global_value=cp['global_param']

        # 断言
        detail_info['assert_param'] = cp['assert_info']['msg']

        # 详细信息
        detail_info['error_tag'] = cp['error_tag']
        detail_info['api_url'] = cp['url']
        detail_info['header'] = cp['header']['result']
        detail_info['request_body'] = cp['request_body']['result']
        detail_info['response_body'] = cp['response_body']
        detail_info['reponse_tab'] = 'reponse_tab{}'.format(caseinfo.Case.id)
        detail_info['reponse_detail_tab'] = 'reponse_detail{}'.format(caseinfo.Case.id)

        if cp['assert_info']['isok'] == False:
            fail_count += 1
            detail_info['result'] = 'fail'
        else:
            detail_info['result'] = 'ok'

        if len(cp['error_tag'])>0:
            detail_info['result'] = 'error'
            error_count += 1

        run_reslut_list.append(detail_info)

    ok_count=total_count-fail_count-error_count
    pass_percent=int(ok_count/total_count*100)
    return {'code':200,'msg':run_reslut_list,'summary':{'total':total_count,'ok':total_count-fail_count-error_count,
                                                        'fail':fail_count,'error':error_count,'pass_percent':pass_percent}}







