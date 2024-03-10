import requests


def push_bug_notice(r, assignee, bug, pro_code, prosql):
    data = {
         "msgtype": "markdown",
         "markdown": {
             "title": "新BUG提交通知",
             "text": "## 新BUG提交通知 \n ### {}:[{}](https://jira.inkept.cn/browse/{})".format(assignee.split(',')[1], bug, bug)
         },
         "at": {
            "atMobiles": [],
            "isAtAll": False
         }
     }
    phone = r.get("{}:phone".format(assignee.split(',')[0]))
    if phone is None:
        sql = "SELECT tel FROM `user_info` WHERE user_name ='{}';".format(assignee.split(',')[1])
        phone = prosql.select_one(sql)['tel']
    if phone:
        r.set("{}:phone".format(assignee.split(',')[0]), phone)
        data["at"]["atMobiles"].append(phone)
        data["markdown"]["text"] = data["markdown"]["text"] + '\n<font color=#1890ff face=\"黑体\"> @{}<font>'.format(phone)
    # 钉钉通知
    print(data)
    key = r.get("ding_robot_{}".format(pro_code))
    if key:
        a = requests.post('https://oapi.dingtalk.com/robot/send?access_token={}'.format(key), json=data)
        return a.status_code
    sql = "SELECT ding_robot FROM `project` WHERE pro_code='{}';".format(pro_code)
    key = prosql.select_one(sql)['ding_robot']
    if key:
        r.set("ding_robot_{}".format(pro_code), key)
        a = requests.post('https://oapi.dingtalk.com/robot/send?access_token={}'.format(key), json=data)
        return a.status_code
    return -1


if __name__ == '__main__':
    push_bug_notice()
