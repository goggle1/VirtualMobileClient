#coding=utf-8
import MySQLdb

class DB_MYSQL :
    
    def __init__(self):
        self.conn = None
        self.cur = None
    '''    
    def __del__(self):
        del self.conn
        del self.cur
        self.conn = None
        self.cur = None
    '''
            
    def connect(self, host, port, user, passwd, db, charset='utf8') :
        self.conn = MySQLdb.connect(host, user, passwd, db, port, charset='utf8')
        self.cur  = self.conn.cursor()
        
    def execute(self, sql):           
        self.cur.execute(sql)
        
    def close(self):
        self.cur.close()
        self.conn.close()
        
        
class DB_CONFIG_MACROSS:
    host        = '192.168.8.101'
    port        = 3317
    user        = 'public'
    password    = 'funshion'
    db          = 'macross'
   
    
class DB_CONFIG_MSMASTER:
    host        = '192.168.160.203'
    port        = 3306
    user        = 'admin'
    password    = '123456'
    db          = 'msmaster2'