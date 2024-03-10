
from fastapi import FastAPI
from qa_sys import pro_module
from api import api_info, case, api_host, api_config, global_value, business, business_detail, report, job, api_data, runjenkins, global_case
from common import sys_base,test_manage_base,api_base,dingding
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from test_manage import version,demand,caselist,jira_info,caseplan,caseindex,testplan,join_testplan
from summary import jira_summary,qa_mon_report,delay,middle_report,qa_mon,middle_mon_report

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#系统设置
app.include_router(pro_module.router)   #项目模块

#接口
app.include_router(api_info.router)   #接口信息
app.include_router(case.router)   #用例
app.include_router(api_host.router)   #接口host信息
app.include_router(api_config.router)   #接口配置信息
app.include_router(global_value.router)   #全局变量
app.include_router(global_case.router)  # 全局用例
app.include_router(business.router)   #业务流
app.include_router(business_detail.router)   #业务流
app.include_router(report.router)   #测试报告
app.include_router(job.router)   #定时任务
app.include_router(api_data.router)   #执行数据
app.include_router(runjenkins.router)   # 定时任务
app.include_router(jira_info.router)
#app.include_router(pro_module.router)

#统计
app.include_router(jira_summary.router)     #jira统计
app.include_router(qa_mon_report.router)    #质量月报
app.include_router(delay.router)            #延期提测
app.include_router(middle_report.router)    #中台月报
app.include_router(qa_mon.router)
app.include_router(middle_mon_report.router)    #中台月报


#基础数据
app.include_router(sys_base.router)     #系统基础数据
app.include_router(test_manage_base.router)     #测试工具基础数据
app.include_router(api_base.router)     #接口基础数据
app.include_router(dingding.router)     #钉钉基础数据

#测试管理
app.include_router(version.router)    #版本需求
app.include_router(demand.router)    #需求模块
app.include_router(caselist.router)  #测试用例
app.include_router(caseindex.router)    #用例目录
app.include_router(caseplan.router) #测试计划
app.include_router(testplan.router)
app.include_router(join_testplan.router)


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="0.0.0.0", port=8000, reload=True, debug=True)

