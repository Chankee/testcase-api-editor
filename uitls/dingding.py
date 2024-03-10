import requests

url='https://oapi.dingtalk.com/robot/send?access_token=706567debfcbbffa52b61119c5843566ecf8c870d5a9fb7c82fec1e288b29c12'
content={
 "msgtype": "markdown",
 "markdown": {
     "title":"自测提醒",
     "text": '- 研发自测提醒：'
             '- 【版本】3.4.8'
             '- 【自测】用例总数142条，有74条用例未执行；执行总进度是47.89%'
             '- 【自测链接】<a href="http://gz-qa.inkept.cn/qa_view/#/test/plan/plan_list" target="_blank">'
 },
  "at": {
      "atMobiles": [
          "150XXXXXXXX"
      ],
      "atUserIds": [
          "user123"
      ],
      "isAtAll": False
  }
 }


print(requests.post(url,json=content).json())




