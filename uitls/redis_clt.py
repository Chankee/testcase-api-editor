import redis
from uitls.read_config import ReadConfig as rc
redis_host = rc().read_config('dbconfig', 'redis', 'host')
redis_port = rc().read_config('dbconfig', 'redis', 'port')
password = rc().read_config('dbconfig', 'redis', 'password')


class redis_clt():
    def __init__(self, db=0):
        self.pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=db, password=password, decode_responses=True)
        # r = redis.Redis(host=redis_host, port=redis_port, db=db, password=password, decode_responses=True)

    def __new__(cls, *args, **kw):
        '''
        启用单例模式
        :param args:
        :param kw:
        :return:
        '''
        if not hasattr(cls, '_instance'):
            cls._instance = object.__new__(cls)
        return cls._instance

    def r(self):
        return redis.Redis(connection_pool=self.pool)


if __name__ == '__main__':
    # r = redis_clt().r()
    # a = r.get('heqicong:phone')
    # print(a)
    # r.close()
    r=redis_clt(1).r()
    r.hdel("testcase_select_tree", "waha")
    r.close()
