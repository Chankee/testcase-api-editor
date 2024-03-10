#### 1、项目结构
```
qa_api_server
├── api                                #接口公共库和接口自动化
├── qa_api_business                    #qa_api业务逻辑层
├── pm                                 #项目管理                                                             
├── user                               #用户信息登录和认证
├── log                                #日志文件
├── uitls                              #通用功能库                         
└── main.py                            #路由登记和项目启动                                        
```


#### 1.执行安装代码同步安装包版本
```
pip install -r requirements.txt #安装依赖包
```

#### 2.启动fastapi命令
uvicorn main:app --reload



