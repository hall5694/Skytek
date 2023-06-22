import time
import multiprocessing
import board
import busio
import adafruit_ina260
import inspect,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('motor_current')

class Mtr_Current_Process(multiprocessing.Process):
    def __init__(self, q6, q25, qm1, qm2, qm3, qm4, qm5, qm6, qm7, qw1, qw3, qw22, qwg1):
        multiprocessing.Process.__init__(self)

        self.kpv_vars_list = ['adjuster_pos','min_ma_record','adj_arr_ST_up_size', 'adj_arr_ST_down_size', \
                               'adj_arr_LT_up_size','adj_arr_LT_up_min_size','adj_arr_LT_down_min_size','adj_arr_LT_down_size', \
                               'adj_up_avg_max','adj_down_avg_max','adj_up_outlier_stpt','adj_down_outlier_stpt', \
                               'adj_up_inst_max','adj_LT_up_avg','adj_LT_down_avg','max_ma_violation', \
                               'adj_down_inst_max']
        self.kpv_index_list = [82,170,171,172, \
                               173,174,175,176, \
                               177,178,179,180, \
                               181,182,183,184, \
                               194]
        self.KpvTypes = []
        self.q6 = q6 # web re_center and motor current inst ma max
        self.q25 = q25 # send kpv from py processes to cntrl.py        
        self.qm1 = qm1 # motor_current.py motor direction
        self.qm2 = qm2 # motor_current.py adjuster position
        self.qm3 = qm3 # motor_current.py re-center active
        self.qm4 = qm4 # constant ma alarm checking
        self.qm5 = qm5 # NA
        self.qm6 = qm6 # send kpv list to motor_current.py
        self.qm7 = qm7 # send kpv list from motor_current.py to cntrl
        self.qw1 = qw1 # ma readings from motor_current.py
        self.qw3 = qw3 # inlet_display
        self.qw22 = qw22  # send_web_message for motor_current.py

        self.qwg1  = qwg1

        i2c = busio.I2C(board.SCL, board.SDA)
        self.ina260 = adafruit_ina260.INA260(i2c, 0x40)

        self.Kpv = []

        self.update_interval = 20 # seconds to update kpv
        self.udst = time.time()
        self.web_prev_msg = ""
        self.post_time = 3
        self.pst = time.time()
        self.st = time.time()
        self.stset = 0
        self.dt = 0

        self.prev_msg = ""
        self.read_interval = 0.1
        self.st_set = 0
        self.st = 0
        self.adj_max_ma_alarm = 0

        self.adj_arr_ST_up = []
        self.adj_ST_up_avg = 0
        self.adj_arr_ST_down = []
        self.adj_ST_down_avg = 0

        self.adj_arr_LT_up = []
        self.adj_arr_LT_down = []

        self.adj_max_inst_ma_alarm = 0

        self.mtr_dir = 0
        self.re_center_stat = 0
        self.re_center_active = 0
        
        self.adj_up_violation = 0
        self.inhibit_up = 0
        self.adj_down_violation = 0
        self.inhibit_down = 0        


    def read_current(self):
        try:
            adj_ma = int(self.ina260.current)
        except:
            self.cprint("Not able to read in aduster motor current from INA260")
            return("error")
        else:
            self.dt = time.time() - self.st
            if self.stset == 0:
                self.stset = 1
                self.st = time.time()
                self.dt = 0
            #self.cprint("adj_ma : %s"%adj_ma)
            Dct = {'dest':'web_graph_adj_ma','dir':self.mtr_dir, 'dt':self.dt, 'adj_ma':adj_ma, \
                   'adj_ST_up_avg':self.adj_ST_up_avg, 'adj_ST_down_avg':self.adj_ST_down_avg, \
                   'adj_LT_up_avg':self.adj_LT_up_avg, 'adj_LT_down_avg':self.adj_LT_down_avg, \
                   'adj_up_inst_max':self.adj_up_inst_max, 'adj_down_inst_max':self.adj_down_inst_max,  \
                   'adj_up_avg_max':self.adj_up_avg_max, 'adj_down_avg_max':self.adj_down_avg_max}
            self.mq(self.qwg1, Dct)
            Dict = {'dest':'mtr_current_readings','adj_ma':adj_ma, 'adj_ST_up_avg':self.adj_ST_up_avg, 'adj_ST_down_avg':self.adj_ST_down_avg, 'adj_LT_up_avg':self.adj_LT_up_avg, 'adj_LT_down_avg':self.adj_LT_down_avg}
            return Dict

    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (motor_current%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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
            data = self.read_current()
        except:
            raise
            self.cprint("problem with reading motor current")
        else:
            self.mq(self.qw1,data) # send ma to web
            #self.cprint(data)
            if data != "error":
                ma = data['adj_ma']
                if time.time() - self.pst > self.post_time:
                    self.pst = time.time()
                if self.re_center_active == 0 and ma > self.min_ma_record:
                    if self.mtr_dir == 1:
                        # short term ma up
                        if ma < self.adj_up_outlier_stpt:
                            self.adj_arr_ST_up.append(ma)
                            if len(self.adj_arr_ST_up) > int(self.adj_arr_ST_up_size):
                                self.adj_arr_ST_up.pop(0)
                            if len(self.adj_arr_ST_up) > 0:
                                self.adj_ST_up_avg = int(sum(self.adj_arr_ST_up) / len(self.adj_arr_ST_up))
                            # long term ma up
                            self.adj_arr_LT_up.append(ma)
                            if len(self.adj_arr_LT_up) > int(self.adj_arr_LT_up_size):
                               self.adj_arr_LT_up.pop(0)
                            if len(self.adj_arr_LT_up) > 0:
                                self.adj_LT_up_avg = int(sum(self.adj_arr_LT_up) / len(self.adj_arr_LT_up))

                    elif self.mtr_dir == -1:
                        # short term ma down array
                        if ma < self.adj_down_outlier_stpt:                        
                            self.adj_arr_ST_down.append(ma)
                            if len(self.adj_arr_ST_down) > int(self.adj_arr_ST_down_size):
                                self.adj_arr_ST_down.pop(0)
                            if len(self.adj_arr_ST_down) > 0:
                                self.adj_ST_down_avg = int(sum(self.adj_arr_ST_down) / len(self.adj_arr_ST_down))
                            # long term ma down array
                            self.adj_arr_LT_down.append(ma)
                            if len(self.adj_arr_LT_down) > int(self.adj_arr_LT_down_size):
                                self.adj_arr_LT_down.pop(0)
                            if len(self.adj_arr_LT_down) > 0:
                                self.adj_LT_down_avg = int(sum(self.adj_arr_LT_down) / len(self.adj_arr_LT_down))

                # alarms
                if self.mtr_dir == 1:
                    if self.adj_ST_up_avg > self.adj_up_inst_max:
                        self.adj_max_inst_ma_alarm = 1
                        self.cprint("---(%s) Adjuster instantaneous ma up tripped - max (%s) ---"%(self.adj_ST_up_avg,self.adj_up_inst_max))
                        self.send_web_message("---(%s) Adjuster instantaneous ma up tripped - max (%s) ---"%(ma,self.adj_up_inst_max))
                    elif self.adj_ST_up_avg > self.adj_up_avg_max:
                        if self.adjuster_pos != self.prev_adjuster_pos:
                            self.cprint("self.adj_ST_up_avg : %s"%self.adj_ST_up_avg)
                            self.cprint("self.adj_up_avg_max : %s"%self.adj_up_avg_max)                                                        
                            if self.adj_max_ma_alarm == 0:
                                self.adj_max_ma_alarm = 1
                                self.adj_up_violation += 1
                                self.cprint("self.adj_up_violation : %s"%self.adj_up_violation)
                    else:
                        self.adj_max_ma_alarm = 0
                        self.adj_max_inst_ma_alarm = 0
                        self.adj_up_violation = 0
                    if self.inhibit_down == 1:
                        self.inhibit_down = 0
                        self.cprint("Downward movement of adjuster allowed")
                        self.send_web_message("Downward movement of adjuster allowed")
                        self.mq(self.qm4, {'purpose':'inhibit_down', 'data':'0'})                                                                                
                        self.adj_down_violation = 0

                elif self.mtr_dir == -1:
                    if self.adj_ST_down_avg > self.adj_down_inst_max:
                        self.adj_max_inst_ma_alarm = 1
                        self.cprint("---(%s) Adjuster instantaneous ma down tripped - max (%s) ---"%(self.adj_ST_down_avg,self.adj_down_inst_max))
                        self.send_web_message("---(%s) Adjuster instantaneous ma down tripped - max (%s) ---"%(self.adj_ST_down_avg,self.adj_down_inst_max))
                    elif self.adj_ST_down_avg > self.adj_down_avg_max:
                        if self.adjuster_pos != self.prev_adjuster_pos:
                            self.cprint("self.adj_ST_down_avg : %s"%self.adj_ST_down_avg)
                            self.cprint("self.adj_down_avg_max : %s"%self.adj_down_avg_max)                            
                            if self.adj_max_ma_alarm == 0:
                                self.adj_max_ma_alarm = 1
                                self.adj_down_violation += 1
                                self.cprint("self.adj_down_violation : %s"%self.adj_down_violation)
                    else:
                        self.adj_max_ma_alarm = 0
                        self.adj_max_inst_ma_alarm = 0
                        self.adj_down_violation = 0
                    if self.inhibit_up == 1:
                        self.inhibit_up = 0
                        self.cprint("Upward movement of adjuster allowed",1,1)
                        self.mq(self.qm4, {'purpose':'inhibit_up', 'data':'0'})                                                                                                                
                        self.adj_up_violation = 0

                # trigger re-center action
                if self.adj_max_inst_ma_alarm == 1:
                    self.mtr_dir = 0
                    self.mq(self.q6, {'purpose':'stop', 'data':'3'}) # command to stop
                    self.send_web_message("Stop adjuster command sent from motor_current.py")
                    self.adj_max_inst_ma_alarm = 0
                elif self.adj_max_ma_alarm == 1:
                    if abs(self.adjuster_pos) > self.Kpv[26] and self.re_center_active == 0:
                        if self.mtr_dir == 1:
                            self.cprint("---(%s) Adjuster ST ma up avg tripped - max (%s) ---"%(self.adj_ST_up_avg,self.adj_up_avg_max),1,1)
                            self.reset_ST_up_arr()                            
                        elif self.mtr_dir == -1:
                            self.cprint("---(%s) ST ma down tripped - max (%s) ---"%(self.adj_ST_down_avg,self.adj_down_avg_max),1,1)
                            self.reset_ST_down_arr()                            
                        #self.cprint("Re-center adjuster command sent from motor_current.py")
                        #self.send_web_message("Re-center adjuster in progress")
                        #self.mq(self.q6, {'purpose':'re_center', 'data':'2'}) # command to re-center adjuster
                    elif abs(self.adjuster_pos) < self.Kpv[26] or self.re_center_active == 1: # stop motor
                        #self.reset_ST_down_arr()                            
                        self.cprint("Adjuster stopped for over-current",1,1)
                        self.mq(self.qm4, {'purpose':'stop', 'data':'2'}) # command to stop adjuster
                    if self.adj_up_violation > self.max_ma_violation and self.inhibit_up == 0:
                        self.cprint("Further upward movement of adjuster prohibited",1,1)
                        self.mq(self.qm4, {'purpose':'inhibit_up', 'data':'1'})
                        self.inhibit_up = 1
                    if self.adj_down_violation > self.max_ma_violation and self.inhibit_down == 0:
                        self.cprint("Further downward movement of adjuster prohibited",1,1)
                        self.mq(self.qm4, {'purpose':'inhibit_down', 'data':'1'})                            
                        self.inhibit_down = 1
                    self.adj_max_ma_alarm = 0
                    self.mtr_dir = 0

            else:
                data = {'dest':'mtr_current_readings','adj_ma': 'error'}
                self.cprint("error with mtr amp data")
                self.mq(self.qw1, data)

        # save values for next program run
        if time.time() - self.udst > self.update_interval:
            if self.adj_LT_down_avg != self.Kpv[183]:
                self.Kpv[183] = self.adj_LT_down_avg
                self.mod_kpv_entry(183,self.adj_LT_down_avg)
                self.udst = time.time()
            if self.adj_LT_up_avg != self.Kpv[182]:
                self.Kpv[182] = self.adj_LT_up_avg
                self.mod_kpv_entry(182,self.adj_LT_up_avg)
                self.udst = time.time()
        self.adj_LT_down_avg_prev = self.adj_LT_down_avg
        self.adj_LT_up_avg_prev = self.adj_LT_up_avg

    def ft2(self, data, precision):
        if precision == 2:
            return (format(data,'.2f'))

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

    def send_web_message(self, var):
        if True: #var != self.web_prev_msg:
            Dict = {'dest':'web_message', 'val':var}
            self.qw22.put(Dict)
            self.web_prev_msg = var

    def reset_ST_up_arr(self):
        for i in range(len(self.adj_arr_ST_up)):
            self.adj_arr_ST_up.pop(0)
            self.adj_arr_ST_up.append(self.adj_LT_up_avg)
            
    def reset_ST_down_arr(self):
        for i in range(len(self.adj_arr_ST_down)):
            self.adj_arr_ST_down.pop(0)
            self.adj_arr_ST_down.append(self.adj_LT_down_avg)
         
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
                                                        
        self.prev_adjuster_pos = self.adjuster_pos
        self.adj_LT_up_avg_prev = self.adj_LT_up_avg
        self.adj_LT_down_avg_prev = self.adj_LT_down_avg
        
        if self.Kpv[182] != 0:
            self.adj_arr_LT_up = []
            for i in range(20):
                self.adj_arr_LT_up.append(self.Kpv[182])
        if self.Kpv[183] != 0:
            self.adj_arr_LT_down = []
            for i in range(20):
                self.adj_arr_LT_down.append(self.Kpv[183])        
        
                 
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
                                
    def run(self):
        #self.cprint("motor_current.py running")
        while self.qm6.empty():
            time.sleep(1)
        obj = self.qm6.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None          
        self.init_kpv_to_val('init')
        #self.cprint("motor_current.py kpv imported successfully")
        self.get_data()
        while True:
            #print("motor_current.py  %s"%time.time())
            self.get_data()
            if not self.qm1.empty(): # motor_current.py motor direction
                self.mtr_dir = self.qm1.get()
                #self.cprint("mtr_dir : %s"%self.mtr_dir)
            if not self.qm2.empty(): # motor_current.py adjuster position
                self.prev_adjuster_pos = self.adjuster_pos
                self.adjuster_pos = int(self.qm2.get())
            if not self.qm3.empty(): # motor_current.py re-center active
                self.re_center_active = self.qm3.get()
            if not self.qm6.empty(): # get updated kpv from cntrl.py
                obj = self.qm6.get()
                index = obj[0]
                val = obj[1]

                self.init_kpv_to_val(index,val) # set local process kpv values                      

            time.sleep(0.05)
