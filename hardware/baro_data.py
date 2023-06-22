import serial, time
import multiprocessing
import Adafruit_BMP.BMP085 as BMP085
import inspect,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('baro_data')                     

class Baro_Process(multiprocessing.Process):
    def __init__(self, q25, qb1, qb2, qb3, qw2):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['baro_lock_active']
        self.kpv_index_list = [166]
        self.KpvTypes = []
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.qb1 = qb1 # send kpv from cntrl to baro_data.py
        self.qb2 = qb2
        self.qb3 = qb3 # send kpv file to baro_data.py
        self.qw2 = qw2 # baro readings from bar_data.py
        self.qb1 = qb1
        self.st_set = 0
        self.st = 0
        self.sensor = BMP085.BMP085()
        self.read_interval = 60
        pst = time.time()
        self.prev_msg = ""
        
        self.dc = 0 # dead count

    def read_baro(self):
        try:
            baro = ("{0:0.2f}".format(self.sensor.read_pressure() / 6854.757))
        except:
            self.cprint("Not able to read in pressure from barometric pressure sensor")
            return("error")
        else:
            var = "Barometric pressure = %s psi" %baro
            #self.cprint(var)
            Dict = {'data':'good','dest':'baro_readings','baro_psi':baro}
            return Dict

    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (baro_data%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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

                        
    def get_data(self):
        try:
            data = self.read_baro()
            if data != "error":
                while not self.qw2.empty():
                    var = self.qw2.get()
                while not self.qb2.empty():
                    var = self.qb2.get()
                self.mq(self.qw2, data)
                self.mq(self.qb2, data)
            else:
                data = {'data':'error','dest':'baro_readings','baro_psi':'error'}
                self.mq(self.qw2, data)
                self.mq(self.qb2, data)
        except:
            self.cprint("exception in baro_data.py")
            data = {'data':'error','dest':'baro_readings','baro_psi':'error'}
            self.mq(self.qw2, data)
            self.mq(self.qb2, data)
            
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
        
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
                                          
    def run(self):
        #self.cprint("baro_data.py running")
        while self.qb3.empty():
            time.sleep(1)
        obj = self.qb3.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None                           
        self.init_kpv_to_val('init') 
        #self.cprint("baro_data.py kpv imported successfully")
        if self.baro_lock_active == 0:
            self.get_data()
        fm = 1
        self.baro_set = 0
        while True:
            #print("baro_data.py  %s"%time.time())
            if not self.qb1.empty():
                data = self.qb1.get()
                if data['purpose'] == "baro_set":
                    self.baro_set = int((data['data']))                
                            
            if self.st_set == 0:
                self.st = time.time()
                self.st_set = 1
            if self.baro_set == 0: # display baro every second for first minute of program run
                if time.time() - self.st > fm and self.baro_lock_active == 0:
                    self.get_data()
                    fm += 1        
                    if fm > 10:
                        self.baro_set = 1
            if time.time() - self.st > self.read_interval and self.baro_lock_active == 0:
                self.baro_set = 1                
                self.st = time.time()
                self.st_set = 0
                self.get_data()
            if not self.qb3.empty(): # get updated kpv from cntrl.py
                obj = self.qb3.get()
                index = obj[0]
                val = obj[1]

                self.init_kpv_to_val(index,val) # set local process kpv values
                
            time.sleep(0.05)

