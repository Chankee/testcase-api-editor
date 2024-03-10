#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time：2019/7/22 10:17
# @Author：kee
# @Description：数据库基础类

import pymysql
import pymysql.cursors
from uitls.read_config import ReadConfig as rc
from uitls.log import LOG
from dbutils.pooled_db import PooledDB



class SqlDal():

    def __init__(self,dbname="qa_api"):

        try:
            conf_name=rc().read_config('dbconfig', 'DBSELECT', 'dbname')
            self.connect=pymysql.Connect(host=rc().read_config('dbconfig', conf_name, 'host'),
                                         port=int(rc().read_config('dbconfig', conf_name, 'port')),
                                         user=rc().read_config('dbconfig', conf_name, 'user'),
                                         passwd=rc().read_config('dbconfig', conf_name, 'passwd'),
                                         db=dbname,
                                         charset=rc().read_config('dbconfig', conf_name, 'charset'),
                                         cursorclass=pymysql.cursors.DictCursor)

            self.connect.ping(reconnect=True)   # 判断关闭则打开
            self.cursor=self.connect.cursor()
        except Exception as ex:
            LOG().error('连接数据库失败，错误信息：{}'.format(ex))



    def close_conn(self):
        '''
        关闭数据库及游标
        '''

        try:
            self.cursor.close()
            self.connect.close()
        except Exception as ex:
            LOG().error("关闭数据库失败，错误信息：{}".format(ex))


    def select_data(self, sql):
        '''
        查询单条数据
        :sql:sql语句
        :return:返回列表格式
        '''
        result = ''
        try:
            self.cursor.execute(sql)
            # 获取结果数据列表
            result = self.cursor.fetchall()
        except Exception as ex:
            LOG().error('sql语句：{}，查询数据失败，错误信息：{}'.format(sql,str(ex)))
        finally:
            self.close_conn()
        return result


    def select_data_one(self, sql):
        '''
        查询单条数据
        :sql:sql语句
        :return:返回列表格式
        '''
        result = ''
        try:
            self.cursor.execute(sql)
            # 获取结果数据列表
            result = self.cursor.fetchone()
        except Exception as ex:
            LOG().error('sql语句：{}，查询数据失败，错误信息：{}'.format(sql,str(ex)))
        finally:
            self.close_conn()
        return result


    def select_datas(self,sql_list):
        '''
        批量查询
        :param sql_list:
        :return:
        '''
        reslut_list=[]
        try:
            for sql in sql_list:
                self.cursor.execute(sql)
                # 获取结果数据列表
                reslut_list.append(self.cursor.fetchall())
        except Exception as ex:
            LOG().error('sql语句：{}，查询数据失败，错误信息：{}'.format(','.join(sql_list), str(ex)))
        finally:
            self.close_conn()
        return reslut_list


    def save_datas(self, sql,value_list):
        '''
        批量插入数据
        :sql:sql语句
        :value_list:列表
        :return:返回列表格式
        '''
        try:
            res = self.cursor.executemany(sql,value_list)
            self.connect.commit()
            LOG().info('保存成功,执行了{}条'.format(res))
        except Exception as ex:
            LOG().error('保存数据失败，错误信息：{}'.format(ex))
        finally:
            self.close_conn()



    def delete_data(self,sql):
        '''
        删除数据
        :sql:sql语句
        :return:
        '''

        try:
            res=self.cursor.execute(sql)
            self.connect.commit()
            LOG().info('删除成功,执行了{}条'.format(res))
        except Exception as ex:
            LOG().error('删除数据失败，错误信息：{}'.format(ex))
        finally:
            self.close_conn()



    def insert_data_retunid(self, sql, insert_info):
        '''
        插入/编辑单条数据返回ID
        :sql:sql语句
        :return:ID
        '''

        last_id=0
        try:
            with self.connect.cursor() as curs:
                curs.execute(sql, insert_info)
                last_id = curs.lastrowid
            self.connect.commit()
        except Exception as ex:
            LOG().error('插入数据失败，sql语句：{}，错误信息：{}'.format(sql,ex))
            self.connect.rollback()
        finally:
            self.close_conn()
        return last_id



    def save_data(self, sql, save_info):
        '''
        插入/编辑单条数据
        :sql:sql语句
        :insert_info:插入数据，列表格式
        :return:ID
        '''

        try:
            with self.connect.cursor() as curs:
                curs.execute(sql, save_info)
        except Exception as ex:
            LOG().error('保存数据失败，sql语句：{}，错误信息：{}'.format(sql, ex))
            self.connect.rollback()
        finally:
            self.connect.commit()
            self.close_conn()


class MysqlPool(object):
    def __init__(self, dbname="qa_api"):
        conf_name = rc().read_config('dbconfig', 'DBSELECT', 'dbname')
        self.POOL = PooledDB(
            creator=pymysql,  # 使用链接数据库的模块
            maxconnections=6,  # 连接池允许的最大连接数，0和None表示不限制连接数
            mincached=2,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
            maxcached=5,  # 链接池中最多闲置的链接，0和None不限制
            maxshared=3,
            # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
            blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
            maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
            setsession=[],  # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
            ping=0,
            # ping MySQL服务端，检查是否服务可用。# 如：0 = None = never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is executed, 7 = always
            host=rc().read_config('dbconfig', conf_name, 'host'),
            port=int(rc().read_config('dbconfig', conf_name, 'port')),
            user=rc().read_config('dbconfig', conf_name, 'user'),
            passwd=rc().read_config('dbconfig', conf_name, 'passwd'),
            database=dbname,
            charset='utf8'
        )

    # def __new__(cls, *args, **kw):
    #     '''
    #     启用单例模式
    #     :param args:
    #     :param kw:
    #     :return:
    #     '''
    #     if not hasattr(cls, '_instance'):
    #         cls._instance = object.__new__(cls)
    #     return cls._instance

    def connect(self):
        '''
        启动连接
        :return:
        '''
        conn = self.POOL.connection()
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        return conn, cursor

    def connect_close(self, conn, cursor):
        '''
        关闭连接
        :param conn:
        :param cursor:
        :return:
        '''
        cursor.close()
        conn.close()

    def select_all(self, sql):
        '''
        批量查询
        :param sql:
        :param args:
        :return:
        '''
        conn, cursor = self.connect()
        cursor.execute(sql)
        record_list = cursor.fetchall()
        self.connect_close(conn, cursor)

        return record_list

    def select_one(self, sql):
        '''
        查询单条数据
        :param sql:
        :param args:
        :return:
        '''
        conn, cursor = self.connect()
        cursor.execute(sql)
        result = cursor.fetchone()
        self.connect_close(conn, cursor)

        return result

    def save(self, sql, args):
        '''
        变更数据
        :param sql:
        :param args:
        :return:
        '''
        conn, cursor = self.connect()
        try:
            sql = cursor.mogrify(sql, args)
            print(sql)
            cursor.execute(sql)
            conn.commit()
            self.connect_close(conn, cursor)
            # LOG().info('执行，sql语句：{}'.format(sql))
        except Exception as ex:
            conn.rollback()
            LOG().info('保存数据失败，sql语句：{}，错误信息：{}'.format(sql, ex))
            return 0
        return 1


if __name__ == "__main__":
    sq = MysqlPool('jira')
    # sql = "select * from user_roles_contact where username='冯思华' and isdelete=0"
    # print(sq.select_data(sql))
    # sql = "SELECT priority,COUNT(*) as num FROM `yp` WHERE affectedVersion = '4.4.00' GROUP BY priority;"
    sql = "UPDATE `jira`.`{}` SET `is_del`= 1 WHERE `id`='{}';".format('yp', 'MAIFOU-1797')
    sq.save(sql)
    # sql2 = "select id from api_info"
    # result2 = sq.select_data(sql2)
    # print(result)
    # print(result2)
    #LOG().info('123')








