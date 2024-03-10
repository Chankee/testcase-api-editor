from jira import JIRA
import requests
import urllib3
import requests.adapters
import datetime, time
from uitls.log import LOG
from qa_dal.testmanage import bug_schemas
from multiprocessing.dummy import Pool as ThreadPool
urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 5
log = LOG("jira")


class INKE_JIRA(JIRA):
    def __init__(self, ticket):   # basic_auth
        self.server = 'https://jira.inkept.cn/'
        self.ticket = ticket
        if ticket == "":
            pass
            return
        session = self._get_jira_session(ticket)
        if session == "":
            # TODO: raise exception
            pass
            return
        self.session = session
        super(INKE_JIRA, self).__init__(server=self.server, options={"cookies": {"JSESSIONID": session}})

    def _get_jira_session(self, ticket):
        url = "%s/secure/Dashboard.jspa?ticket=%s" % (self.server, ticket)
        x = requests.get(url, allow_redirects=False, verify=False)
        cookies = x.cookies
        for cookie in cookies:
            if cookie.name == "JSESSIONID":
                return cookie.value


def getjira(pro_code, jira_clt, jirasql, prosql, r, limit, time_dis=None, start=None ,end=None):   # 更新jira数据
    '''
    更新jira数据,目前只更新缺陷
    :param jirasql:
    :param project: 项目名称
    :param time_dis: int,距离当前时间多少天
    :param jira_clt: jira客户端
    :return:
    '''
    if time_dis:
        jql = 'project={} and type=缺陷 and created>={}'.format(get_jira_id(pro_code, prosql, r), time.strftime("%Y-%m-%d", time.localtime(time.time()-int(time_dis)*86400)))
    else:
        jql = 'project={} and type=缺陷 and created >={} and created<= {}'.format(get_jira_id(pro_code, prosql, r), start, end)
    issues = jira_clt.search_issues(jql, maxResults=limit)
    # log.info("执行jql:{}".format(jql))
    save_err = []
    pool = ThreadPool()
    for issue in issues:
        pool.apply_async(task, (issue, pro_code, jirasql, save_err))
    pool.close()
    pool.join()
    return len(issues), save_err


def task(issue, pro_code, jirasql, save_err):
    created_time = datetime.datetime.strptime(issue.fields.created, '%Y-%m-%dT%H:%M:%S.000+0800')
    resolved_time = None
    if issue.fields.resolutiondate:
        resolved = datetime.datetime.strptime(issue.fields.resolutiondate, '%Y-%m-%dT%H:%M:%S.000+0800')
        resolved_time = "{}".format(resolved)
    isonline, reopen = 0, 0
    belong = None
    description = None
    component = None
    versions = ''
    try:
        versions = ','.join([i.name for i in issue.fields.versions])
        if issue.fields.customfield_11302:
            belong = "{}".format(issue.fields.customfield_11302)
        if issue.fields.description:
            description = issue.fields.description.replace(u'\xa0', u'\x20')  # gbk encode \xa0 error
        if issue.fields.customfield_10102 and issue.fields.customfield_10102.value == '线上问题':
            isonline = 1
        if issue.fields.customfield_10103 and issue.fields.customfield_10103.value == 'yes':
            reopen = 1
        if issue.fields.components:
            component = issue.fields.components[0].name
    except Exception as e:
        log.error(issue.key + '属性赋值报错，' + e.__class__.__name__ + str(e))
    sql = "SELECT id FROM `jira`.`%s` WHERE id='%s';" % (pro_code, issue.key)
    res = jirasql.select_one(sql)
    if res:
        sql = "UPDATE `jira`.`{}` SET `summary`=%s, `description`=%s, `status`=%s, `resolved`=%s,  `assignee`=%s, " \
              "`priority`=%s, `belong`=%s, `reopen`=%s, `isonline`=%s , `affectedVersion`=%s WHERE `id`=%s;".format(pro_code)
        jirasql.save(sql, (issue.fields.summary, description, issue.fields.status, resolved_time, issue.fields.assignee,
               issue.fields.priority, belong, reopen, isonline, versions, issue.key))
        return
    sql = "INSERT INTO `jira`.`{}` (`id`, `issuetype`, `status`, `summary`, `description`, `created`, `resolved`," \
          "`reporter`, `assignee`, `priority`, `component`, `affectedVersion`, `isonline`, `reopen`, `belong`) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s);".format(pro_code)
    res = jirasql.save(sql, (issue.key, issue.fields.issuetype, issue.fields.status, issue.fields.summary, description,
           created_time, resolved_time, issue.fields.reporter, issue.fields.assignee, issue.fields.priority,
           component, versions, isonline, reopen, belong))
    if res == 0:
        save_err.append(issue.key)


def save_issue(para: bug_schemas.issue, bug, jirasql):
    isonline = 0
    if para.is_online == '线上问题':
        isonline = 1

    plan_id, case_id, demand_id = para.plan_id, para.case_id, para.demand_id
    if para.plan_id is None:
        plan_id = 0
    if para.case_id is None:
        case_id = 0
    if para.demand_id is None:
        demand_id = 0
    component = None
    if para.component:
        component = para.component
    sql = "INSERT INTO `jira`.`{}` (`id`, `issuetype`, `status`, `summary`, `description`, `reporter`, `assignee`, " \
          "`priority`, `component`, `affectedVersion`, `isonline`, `plan_id`, `case_id`, `demand_id`,`created`, `belong` ) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s);".format(para.pro_code)
    jirasql.save(sql, (bug, para.issuetype, '开放', para.summary, para.description, para.reporter, para.assignee.split(',')[1], para.priority,
           component, para.version, isonline, plan_id, case_id, demand_id, time.strftime('%Y-%m-%d %H:%M:%S'), para.belong))



def create_issues(jira_clt, prosql, r, param):
    '''
    创建问题
    :param jira_clt: jira客户端
    :param pro_code: str,项目code yp
    :param summary: str,标题
    :param description: str,描述
    :param issuetype: str,问题类型,'缺陷'
    :param component: str,端, '服务端'
    :param priority: str,优先级,'Medium'
    :param assignee: str,经办人，'yanfaminzi'
    :param versions: str,版本号，'3.6.00'
    :param is_online: str,是否线上问题，'非线上问题'
    :param attachment: str,附件地址，'./test.png'
    :return:
    '''
    try:
        issue_dict = dict()
        jira_id = get_jira_id(param.pro_code, prosql, r)
        if jira_id == 0:
            return 0
        issue_dict.update({
            'project': {'key': jira_id},
            'summary': param.summary,
            'description': param.description,
            'issuetype': param.issuetype,  # 10102
            'priority': {'name': param.priority},  # Low Medium High Highest
            'assignee': {'name': param.assignee.split(',')[0]},
            'versions': [{'name': param.version}],  # 3.5.00
            'customfield_10102': {'value': param.is_online},
            'customfield_11302': {'value': param.belong}
             })
        if param.level:
            issue_dict.update({'customfield_11303': {'value': param.level}})
        if param.component:
            issue_dict.update({'components': [{'name': param.component}]})
        issue = jira_clt.create_issue(issue_dict)
        log.info('添加bug成功:{}'.format(issue.key))
        attachment = param.files
        if attachment:
            for i in attachment:
                jira_clt.add_attachment(issue, attachment='./res/{}'.format(i['name']))
                log.info('{}：添加附件{}成功'.format(issue.key, i))
        return issue.key
    except Exception as ex:
        error_line = ex.__traceback__.tb_lineno
        log.error('第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(ex)))
        return 0


def update_versions(jira_clt, pro_code, r, prosql):
    '''
    更新项目版本号
    :param jira_clt:
    :param project:
    :return:
    '''
    jira_id = get_jira_id(pro_code, prosql, r)
    if jira_id == 0:
        log.info("update_versions:{}失败".format(pro_code))
        return
    poject = jira_clt.project(jira_id)
    version_list = [i.name for i in poject.versions][::-1]
    r.hset("jira_versions", pro_code, str(version_list))


def update_project_components(jira_clt, pro_code, r, prosql):
    '''
    更新各项目jira的components
    :param pro_code
    :param jira_clt:
    :return:
    '''
    jira_id = get_jira_id(pro_code, prosql, r)
    if jira_id == 0:
        log.info("update_project_components:{}失败".format(pro_code))
        return
    poject = jira_clt.project(jira_id)
    components = [i.name for i in poject.components]
    r.hset("jira_project_components", pro_code, str(components))


def get_jira_id(pro_code, prosql, r):
    '''
    :param project: pro_code 如 yp
    :param conn: 数据库连接
    :return:
    '''
    jira_id = r.hget('jira_project_ids', pro_code)
    if jira_id:
        return jira_id
    try:
        sql = "SELECT jira_id FROM `project` WHERE pro_code='{}';".format(pro_code)
        jira_id = prosql.select_one(sql)['jira_id']
        r.hset('jira_project_ids', pro_code, jira_id)
        return jira_id
    except Exception as e:
        log.error("get_jira_id:{}, {}".format(e.__class__.__name__, str(e)))
        return 0


def case_update_bug(plan_id,case_id,testsql,new_bug):
    sql = "SELECT bug FROM plancase WHERE case_id={} and plan_id={};".format(case_id,plan_id)
    bug = testsql.select_one(sql)['bug']
    if bug:
        bug = bug + ',' + new_bug
    else:
        bug = new_bug
    sql = "UPDATE plancase SET bug=%s WHERE case_id=%s and plan_id=%s;"
    testsql.save(sql,(bug, case_id, plan_id))


def get_project_codes(prosql):
    sql = "SELECT pro_code FROM `project` where jira_id is not null;"
    res = prosql.select_all(sql)
    return [i['pro_code'] for i in res]


if __name__ == '__main__':
    jira_clt = INKE_JIRA(ticket='STXOBWElEecZDdRYPNGnciXcmcnViabkPnT')
    print(get_project_codes())
