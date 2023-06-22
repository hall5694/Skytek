import time
import multiprocessing
import inspect

class Activity_Process(multiprocessing.Process):
    def __init__(self, qv1, qv2, qv3, qv4):
                     
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['max_inactivity_min','check_activity_interval']
        self.kpv_index_list = [260,261]
        self.KpvTypes = []
        self.qv1 = qv1 # user activity detected
        self.qv2 = qv2 # max inactivity reached
        self.qv3 = qv3 # kpv for activity.py
        self.qv4 = qv4 # inactivity time
        self.st = None
        self.prev_msg = ""

    def set_user_activity_time(self):
        self.user_activity_time = time.time()

    def check_user_inactivity(self):
        self.inactive_time = time.time() - self.user_activity_time
        if time.time() - self.user_activity_time > self.max_inactivity_sec:
            return True
        else:
            self.mq(self.qv4,{'max_inactive_sec':self.max_inactivity_sec,'inactive_sec':int(self.inactive_time)})
            return False
        
    def cprint(self, msg):
        if msg != self.prev_msg:
            print("%s  (bd%s)"%(msg,inspect.currentframe().f_back.f_lineno))
            self.prev_msg = msg

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
        self.max_inactivity_sec = self.max_inactivity_min * 60
        
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
                                          
    def run(self):
        #self.cprint("activity.py running")
        while self.qv3.empty():
            time.sleep(1)
        obj = self.qv3.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None                           
        self.init_kpv_to_val('init') 
        while True:
            #print("activity.py  %s"%time.time())
            if not self.qv1.empty():
                data = self.qv1.get()
                self.set_user_activity_time()
                if self.st == None:
                    self.st = time.time() # start periodically checking for activity
            if self.st != None:
                if time.time() - self.st > self.check_activity_interval:
                    self.st = time.time()
                    if self.check_user_inactivity():
                        self.mq(self.qv2,{'dest':'logout'})
                        self.st = None
            if not self.qv3.empty(): # get updated kpv from cntrl.py
                obj = self.qv3.get()
                index = obj[0]
                val = obj[1]

                self.init_kpv_to_val(index,val) # set local process kpv values
                
            time.sleep(0.05)

