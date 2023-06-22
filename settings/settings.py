import time
import multiprocessing
import inspect,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('settings')        

class Settings_Process(multiprocessing.Process):
    def __init__(self, q25, qk2, qk4, qw7):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = []
        self.kpv_index_list = []
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.qk2 = qk2 # retreive kpv settings from cntrl
        self.qk4 = qk4 # change made to kpv - update web
        self.qw7 = qw7 # kpv for settings.py
        self.Dict = {'dest':'kpv'}
        self.prev_msg = ""
        
    def mq(self, q, val, block = False, timeout = 0.05): # verify queue transmission
        if block == 1:
            block = True
        try:
            self.q = q
            try:
                while self.q.full():
                    self.q.get(block, timeout)
            except:
                None
            else:
                try:
                    self.q.put(val, block, timeout)         
                except:
                    None
        except:
            None
               
    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (settings%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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

    def init_kpv_to_val(self, index = 'init', val = 0):
        tv = 'int'
        if len(self.kpv_vars_list) > 0:
            if index == 'init':
                for i in range(len(self.kpv_vars_list)):
                    if str(self.KpvTypes[self.kpv_index_list[i]]) == 'i':
                        tv = 'int'
                    elif str(self.KpvTypes[self.kpv_index_list[i]]) == 'f':
                        tv = 'float'
                    elif str(self.KpvTypes[self.kpv_index_list[i]]) == 's':
                        tv = 'str'                                        
                    exec("self." + self.kpv_vars_list[i] + " = " + tv + "(self.Kpv[" + str(self.kpv_index_list[i]) + "])")
            else:
                index = int(index)
                fv = -1
                for i in range(len(self.kpv_index_list)):
                    if index == self.kpv_index_list[i]:
                        fv = i
                        break
                if str(self.KpvTypes[index]) == 'i':
                    tv = 'int'
                elif str(self.KpvTypes[index]) == 'f':
                    tv = 'float'
                elif str(self.KpvTypes[index]) == 's':
                    tv = 'str'
                if (fv != -1):
                    exec("self." + self.kpv_vars_list[fv] + " = " + tv + "(" + str(val) + ")")
        
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
        
    def run(self):
        #print("settings.py running  %s"%time.time())
        #self.cprint("settings.py kpv imported successfully")          
        while True:
            #print("settings.py")
            if not self.qk2.empty(): # retreive full kpv settings
                obj = self.qk2.get()
                self.Kpv = obj[0]
                self.KpvTypes = obj[1]
                self.KpvTags = obj[2]           
                while len(self.Kpv) == 0:
                    None
                self.init_kpv_to_val('init')
                self.Dict = {'dest':'kpv','kpv':self.Kpv,'kpv_types':self.KpvTypes,'kpv_tags':self.KpvTags}
                self.mq(self.qw7, self.Dict)
            if not self.qk4.empty(): # change made to kpv - update web
                obj = self.qk4.get()
                index = int(obj[0])
                val = obj[1]
                self.init_kpv_to_val(index,val) # set local process kpv values    
                self.Dict = {'dest':'kpv_update','index':index,'val':val}
                self.mq(self.qw7, self.Dict)                  
            time.sleep(0.1)

