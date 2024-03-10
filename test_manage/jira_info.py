from fastapi import APIRouter
from fastapi import File, UploadFile
import common.jira_base as jira_com
from uitls.redis_clt import redis_clt
from qa_dal.testmanage import bug_schemas
from uitls.sqldal import MysqlPool
import common.dingtalk_notice as ding
import sys
import traceback
router = APIRouter(
    prefix="/tm/jira",
    tags=["测试管理-bug信息"]
)

prosql = MysqlPool()
jirasql = MysqlPool('jira')
testsql = MysqlPool('test_manage')
redis = redis_clt()


@router.get("/update_issue")
async def update_issue(pro_code, token, num=200, day=None, start=None, end=None):
    '''
    :param pro_code:
    :param day:   更新距离现在多少天内的issue
    :param token:
    :return:
    '''
    try:
        if int(num) > 200:
            return {'code': 302, 'msg': 'num需小于等于200'}
        jira_clt = jira_com.INKE_JIRA(ticket=token)
        if day is not None:
            num_issue, err_list = jira_com.getjira(pro_code=pro_code, jira_clt=jira_clt, jirasql=jirasql, prosql=prosql, r=redis.r(), limit=num, time_dis=day)
            return {'code': 200, 'msg': '获取issue数量：{}'.format(num_issue), "save_err":err_list}
        if start is None or end is None:
            return {'code': 300, 'msg': '参数错误'}
        num_issue, err_list = jira_com.getjira(pro_code=pro_code, jira_clt=jira_clt, jirasql=jirasql, prosql=prosql, r=redis.r(), limit=num, start=start, end=end)
        return {'code': 200, 'msg': '获取issue数量：{}'.format(num_issue), "save_err":err_list}
    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_tb)
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(exc_value)}


@router.get("/update")
async def update(token):   # 更新各项目版本，模块数据
    try:
        r = redis.r()
        jira_clt = jira_com.INKE_JIRA(ticket=token)
        pro_codes = jira_com.get_project_codes(prosql=prosql)
        for i in pro_codes:
            jira_com.update_versions(jira_clt, i, r, prosql)
            jira_com.update_project_components(jira_clt, i, r, prosql)
        jira_clt.close()
        return {'code': 200, 'msg': '成功'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.post("/upload")        # 文件上传
async def upload(file: UploadFile = File(...)):
    try:
        res = await file.read()
        with open('./res/{}'.format(file.filename), "wb") as f:
            f.write(res)
        return {"message": "success", 'filename': file.filename}
    except Exception as e:
        return {"message": str(e), 'filename': file.filename}


@router.post("/push_bug")      # bug提交
async def push_bug(body: bug_schemas.issue):
    try:
        r = redis.r()
        jira_clt = jira_com.INKE_JIRA(ticket=body.token)
        bug = jira_com.create_issues(jira_clt, prosql, r, body)
        jira_clt.close()
        if bug:
            if body.case_id and body.plan_id:
                jira_com.case_update_bug(body.plan_id, body.case_id, testsql, bug)
            summ = ''
            for i, v in enumerate(body.summary):
                if v == ']' or v == '】':
                    summ = body.summary[0:i + 1]
                    break
            r.set('{}:{}'.format(body.token, body.pro_code, 7*24*3600), "{"+"'summary':'{}','issuetype':'{}','component':'{}',"
                                                                 "'assignee':'{}','version':'{}','belong':'{}'".format(summ,
                                                            body.issuetype, body.component, body.assignee, body.version, body.belong)+"}")
            # jira_com.save_issue(body, bug, jirasql)
            if body.notice:
                ding.push_bug_notice(r, body.assignee, bug, body.pro_code, prosql)
            return {'code': 200, 'msg': 'bug提交成功'}
        return {'code': 500, 'msg': 'bug提交或附件上传错误'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        jira_com.log.error("【{}】问题提交错误：第{error_line}行发生error为: {e}".format(body.summary, error_line=error_line, e=str(ex)))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/get_lastBug")      # 获取上次提交的BUG记录
async def get_lastBug(pro_code, token):
    try:
        r = redis.r()
        lastBug = r.get('{}:{}'.format(token, pro_code))
        if lastBug:
            return {'code': 200, 'data': eval(lastBug)}
        return {'code': 201, 'data': '无上次提交记录'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/get_components")      # 获取components
async def get_components(pro_code):
    try:
        r = redis.r()
        components = r.hget('jira_project_components', pro_code)
        if components:
            return {'code': 200, 'data': eval(components)}
        return {'code': 200, 'data': []}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/get_versions")      # 获取version
async def get_versions(pro_code):
    try:
        r = redis.r()
        versions = r.hget('jira_versions', pro_code)
        if versions:
            return {'code': 200, 'data': eval(versions)}
        return {'code': 200, 'data': []}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/bug_list")
async def bug_list(pro_code, case_id):
    try:
        sql = "SELECT * FROM `{}` where case_id={} and is_del=0;".format(pro_code, case_id)
        res = jirasql.select_all(sql)
        return {'code': 200, 'data': res}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/version_trend")
async def version_trend(pro_code, versions):
    try:
        versions = versions.split(',')
        data = [[0 for j in range(len(versions))] for i in range(5)]
        for idx, i in enumerate(versions):
            sql = "SELECT priority,COUNT(*) as num FROM `{}` WHERE affectedVersion = '{}' and is_del=0 GROUP BY priority;".format(pro_code, i)
            res = jirasql.select_all(sql)
            total = 0
            for v in res:
                total = total + v['num']
                if v['priority'] == 'Medium':
                    data[3][idx] = v['num']
                    continue
                if v['priority'] == 'Low':
                    data[4][idx] = v['num']
                    continue
                if v['priority'] == 'High':
                    data[2][idx] = v['num']
                    continue
                data[1][idx] = v['num']
            data[0][idx] = total
        return {'code': 200, 'data': data}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/dis_belong")
async def dis_belong(pro_code, versions):
    try:
        versions = versions.split(',')
        belongs = []
        data = []
        sql = "SELECT belong,COUNT(*) as num FROM `{}` WHERE affectedVersion in ({}) and is_del=0 GROUP BY belong;".format(pro_code, str(versions)[1:-1])
        res = jirasql.select_all(sql)
        alist = []
        for i in res:
            belongs.append(i['belong'])
            alist.append(i['num'])
        data.append(alist)
        data = data + [[0 for j in range(len(belongs))] for i in range(4)]
        for idx, i in enumerate(belongs):
            sql = "SELECT priority,COUNT(*) as num FROM `{}` WHERE affectedVersion in ({}) and belong = '{}' GROUP BY priority;".format(pro_code, str(versions)[1:-1], i)
            res = jirasql.select_all(sql)
            for v in res:
                if v['priority'] == 'Medium':
                    data[3][idx] = v['num']
                    continue
                if v['priority'] == 'Low':
                    data[4][idx] = v['num']
                    continue
                if v['priority'] == 'High':
                    data[2][idx] = v['num']
                    continue
                data[1][idx] = v['num']
        return {'code': 200, 'data': data, 'belongs': belongs}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/dis_assignee")
async def dis_assignee(pro_code, versions):
    try:
        versions = versions.split(',')
        assignee_list = []
        data = []
        sql = "SELECT assignee,COUNT(*) as num FROM `{}` WHERE affectedVersion in ({})  GROUP BY assignee;".format(pro_code, str(versions)[1:-1])
        res = jirasql.select_all(sql)
        alist = []
        for i in res:
            assignee_list.append(i['assignee'])
            alist.append(i['num'])
        data.append(alist)
        data = data + [[0 for j in range(len(assignee_list))] for i in range(4)]
        for idx, i in enumerate(assignee_list):
            sql = "SELECT priority,COUNT(*) as num FROM `{}` WHERE affectedVersion in ({}) and assignee = '{}' GROUP BY priority;".format(pro_code, str(versions)[1:-1], i)
            res = jirasql.select_all(sql)
            for v in res:
                if v['priority'] == 'Medium':
                    data[3][idx] = v['num']
                    continue
                if v['priority'] == 'Low':
                    data[4][idx] = v['num']
                    continue
                if v['priority'] == 'High':
                    data[2][idx] = v['num']
                    continue
                data[1][idx] = v['num']
        return {'code': 200, 'data': data, 'assignee_list':assignee_list}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/del_issue")
async def del_issue(id, token, pro_code):
    try:
        jira_clt = jira_com.INKE_JIRA(ticket=token)
        jira_clt.issue(id).delete()
        sql = "UPDATE `jira`.`{}` SET `is_del`= 1 WHERE `id`='{}';".format(pro_code, id)
        jirasql.save(sql)
        return {'code': 200, 'msg': '删除成功'}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/allowed_values")
async def allowed_values(token, pro_code):
    try:
        jira_clt = jira_com.INKE_JIRA(ticket=token)
        createmeta = jira_clt.createmeta(expand='projects.issuetypes.fields', projectKeys=jira_com.get_jira_id(pro_code, prosql, redis.r()), issuetypeNames='缺陷')['projects'][0]['issuetypes'][0]['fields']
        components = []
        versions = []
        belong = []
        level = []
        for i in createmeta['components']['allowedValues']:
            components.append(i['name'])
        for i in createmeta['versions']['allowedValues']:
            versions.append(i['name'])
        for i in createmeta['customfield_11302']['allowedValues']:
            belong.append(i['value'])
        for i in createmeta['customfield_11310']['allowedValues']:
            level.append(i['value'])
        return {'code': 200, 'msd': '成功', 'data': {'components': components, 'versions': versions[::-1], 'belong': belong, 'level': level}}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}


@router.get("/test")
async def test(a, b=1,  start=None, end=None):
    try:
        print(type(a), type(b))
        return {'code': 200, 'msd': []}
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex))
        return {'code': 500, 'msg': '接口报错，报错信息：{}'.format(error_info)}

