import multiprocessing, time
import sys, torndb, MySQLdb
from time import strftime,localtime
import inspect,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('mysql')

class Mysql_process(multiprocessing.Process):
    def __init__(self, qd1, qd2):
        multiprocessing.Process.__init__(self)
        self.qd1 = qd1 # write to db
        self.qd2 = qd2 # read from db
        self.db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')
        self.prev_msg = ""
        
    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (mysql%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
            self.prev_msg = msg
        if web:
            self.send_web_message(msg)            
        if lvl=='d':
            logger.debug(msg)
        elif lvl=='i':        
            logger.info(msg)
        elif lvl=='w':              
            logger.warning(msg)
        elif lvl=='e':                 
            logger.error(msg)
        elif lvl=='c':               
            logger.critical(msg)
            
    def run(self):
        #print("mysql.py running")
        while True:
            if not self.qd1.empty(): # write marker to db
                data = self.qd1.get()
                dtype = str(data['dtype']) # SPDPTP
                dtime = strftime("%Y%m%d%H%M%S", localtime())
                m_read = '-100' if data['m_read'] == 'error' else str(data['m_read']) # meter
                r_read = '-100' if data['r_read'] == 'error' else str(data['r_read']) # reference
                try:
                    self.db.execute("INSERT INTO test_records(type,datetime,meter_read,reference_read) VALUES('" + \
                            dtype + "' , " + dtime + "," + m_read + "," + r_read + ");")
                except:
                    raise
                else:
                    None
                    #self.cprint("database updated")
            if not self.qd2.empty(): # read from db
                data = self.qd2.get()
                
            time.sleep(0.05)

