import serial
import time
import multiprocessing
import inspect,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('serialworker')
        
## Change this to match your local settings


class SerialProcess(multiprocessing.Process):
    def __init__(self,q9, q12, q13, q14, q21, q25, qs1, qs2, qs3, qs4, qs5, qs6, qs7, qs8, \
    qs9, qs10, qs11, qs12, qw3, qw5, qw23, qw24, qw27):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['read_in','dp_high_stpt','sp_high_stpt','psi_open_equalizer_stpt', \
                               'max_poll_fail','serial_baudrate','crystal_inhibit','auto_psi_in_alarm_stpt',
                               'crystal_revision']
        self.kpv_index_list = [195,196,197,198, \
                               199,200,201,202,
                               192]
        self.KpvTypes = []    
        self.q9 = q9 # web eq control
        self.q12 = q12 # serial_worker open the equalizer for high dp
        self.q13 = q13 # serial_worker vent_alarm
        self.q14 = q14 # serial_worker in_vent_alarm
        self.q21 = q21 # serial_worker stop_pid
        self.q25 = q25 # send kpv from py processes to cntrl.py        
        self.qs1 = qs1 # cntrl.py eq_status
        self.qs2 = qs2 # cntrl.py vent_status
        self.qs3 = qs3 # cntrl.py   in_vent_status
        self.qs4 = qs4 # serial worker dp_high_alarm_display
        self.qs5 = qs5 # serial worker sp_high_alarm_display
        self.qs6 = qs6 # write to serial
        self.qs7 = qs7 # reference DP to cntrl.py
        self.qs8 = qs8 # NA
        self.qs9 = qs9 # send auto_pid mode to serialworker
        self.qs10 = qs10 # send kpv file to serialworker.py
        self.qs11 = qs11 # serial worker dp high during SP testing
        self.qs12 = qs12 # restart crystal communication attempts
        
        self.qw3 = qw3 # inlet_display        
        self.qw5 = qw5 # inch and psi readings
        self.qw23 = qw23 # send_web_message for serialworker.py
        self.qw24 = qw24 # port zeroed
        self.qw27 = qw27 # disable clear crystal alarm button
        
        self.Kpv = []       
        self.lta = []
        
        self.prev_Dict = None
        self.prev_msg = ""

        self.auto_mode = None
        self.eq_status = -1
        self.eq_status_get = -1
        self.vent_status = -1
        self.vent_status_get = -1
        self.in_vent_status = -1
        self.in_vent_status_get = -1
        
        self.poll_fail_count = 0
        self.poll_fail = 0
        self.cdt = 0 # countdown timer active
        
        self.prev_msg = ""

        self.auto_sp_in_alarm_display = 0
        self.auto_psi_in_alarm_status = 0
        self.dp_high_alarm_display = 0 # failsafe to make sure alarm will show on web
        self.dp_alarm_status = 0
        self.sp_high_alarm_display = 0 # failsafe to make sure alarm will show on web
        self.sp_alarm_status = 0
        self.mset = 0
        
        self.sltm = 0.001
        
        self.port_works = 0 #verify connection to port
        self.ref_in_num = ""
        self.ref_psi_num = ""
        self.ref_psi_num_prev = 0.0
        self.crystal_inhibit_prev = None
            
    def get_valve_states(self):
        self.eq_status = self.eq_status_get
        self.vent_status = self.vent_status_get
        self.in_vent_status = self.in_vent_status_get

    def check_port_status(self):
        #Determine correct crystal port - Verify ability to read in data
        #self.cprint("self.crystal_inhibit : %s"%self.crystal_inhibit)
        self.check_input()
        if self.crystal_inhibit == 0:        
            self.send_web_message("Checking crystal port status",0)
            if self.poll_fail_count >= self.max_poll_fail:
                self.poll_fail = 1          
                self.send_web_message("%s attempts to connect to crystal have failed. No more attempts will be made.\
                             Please verify the crystal is working and connected, then click --reset crystal alarms--'"\
                             %int(self.max_poll_fail),0)
                self.mq(self.qw5, {'dest':'max_poll_fail'})
                self.mod_kpv_entry(201,1) # disable crystal readings button
            else:
                try:
                    self.ser = serial.Serial(self.serial_port, self.serial_baudrate, timeout=1, parity=serial.PARITY_NONE, rtscts=0)
                except:
                    #raise
                    self.send_web_message("Not able to open serial port to crystal",2)
                    self.connect_countdown()
                else:        
                    try:
                        inw = self.ser.in_waiting
                    except:
                        #raise
                        self.cprint("problem with in waiting")
                        self.connect_countdown()
                    else:        
                        self.send_web_message("Serial port to crystal opened",0.5)
                        try:
                            self.ser.write(b'C') #start the data stream
                            self.ser.write(b'C') #start the data stream
                            self.ser.write(b'P2') #Set correct units
                        except:
                            #raise
                            self.connect_countdown()                   
                            self.send_web_message("Crystal not taking commands",2)
                        else:
                            self.send_web_message("Crystal is taking commands",0.5)
                            try:
                                var = self.ser.read(50).decode()#read in 50 bytes from the data stream
                            except:
                                #raise
                                self.send_web_message("Not able to decode crystal data stream",2)
                                self.connect_countdown() 
                                var = "..."                       
                            else:
                                if var != "": #non empty string from data stream indicates commands are working
                                    self.port_works = 1
                                    self.send_web_message("Communication to crystal successful",1.5)
                                else:
                                    self.cprint("empty string")
                                    self.connect_countdown()
                self.check_input()
                if self.crystal_inhibit == 0:                              
                    time.sleep(self.sltm)
            
    def connect_countdown(self):
        self.check_input()
        if self.crystal_inhibit == 0:
            Dict = {'dest':'poll_fail'}
            self.mq(self.qw5, Dict)
            self.cdt = 1
            self.poll_fail_count += 1
            #if self.poll_fail_count < self.max_poll_fail
            self.cprint("self.poll_fail_count : %s  self.max_poll_fail : %s"%(self.poll_fail_count,self.max_poll_fail))
            self.send_web_message("Problem reading in from crystal",2)
            try:
                self.ser.close()
            except:
                self.cprint("error")
                #raise
                #self.send_web_message("Not able to close serial port to crystal",2) 
            self.mq(self.q21, {'purpose':'stop_pid', 'data':'0'})
            st  = time.time()
            ct = 5
            dt = 0
            tu = 0
            while tu < 6:
                dt = time.time() - st
                if dt > tu:
                    self.send_web_message("Attempt %s/%s to connect to crystal in %s"%(self.poll_fail_count,int(self.max_poll_fail),ct),1)
                    ct -= 1
                    tu += 1
            self.cdt = 0
            self.check_port_status()

    def writeSerial(self, data):
        self.check_input()
        if self.crystal_inhibit == 0:        
            try:
                self.ser.write(data.encode())
            except:
                #raise
                self.connect_countdown()
            else:
                if data =='Z1':
                    self.send_web_message("Reference DP zero command sent",0)
                    Dict =  {'dest':'btn_status', 'btn':'zero1', 'state':'1'}
                    self.mq(self.qw24,Dict)                  
                    time.sleep(0.2)
                    Dict =  {'dest':'btn_status', 'btn':'zero1', 'state':'0'}
                    self.mq(self.qw24,Dict)                  
                elif data =='Z2':    
                    self.send_web_message("Reference SP zero command sent",0)
                    Dict =  {'dest':'btn_status', 'btn':'zero2', 'state':'1'}
                    self.mq(self.qw24,Dict)                  
                    time.sleep(0.2)
                    Dict =  {'dest':'btn_status', 'btn':'zero2', 'state':'0'}
                    self.mq(self.qw24,Dict)                                  

    def send_web_message(self, var, clstime):
        '''
        if clstime != 0:
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw23.put(Dict)
        '''
        Dict = {'dest':'web_message', 'val':var}
        self.qw23.put(Dict)
        self.prev_msg = var
        '''
        if clstime != 0:
            time.sleep(clstime)
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw23.put(Dict)
        '''
        
    def readSerial(self):
        self.check_input()
        if self.crystal_inhibit == 0:
            try:
                sr_str = self.ser.read(self.read_in)
            except:
                self.cprint("Problem reading in string from crystal")
                #raise
                return 'error'
            else:    
                try:
                    r_str = sr_str.decode()
                except:
                    self.cprint("Problem with decode")
                    self.cprint(r_str)
                    #raise
                    return 'error'
                else:
                    length = len(r_str)
                    instr = r_str.find(self.in_str)
                    r_str = r_str[instr+13:length] + r_str[0:instr+13]
                    try: #verify inh20 value is a number
                        self.ref_in_num = format(float(r_str[0:8]),'.2f')
                    except:
                        self.cprint(r_str)
                        self.cprint("Problem with in num")
                        #raise
                        return 'error'
                    else:
                        try: #verify psi value is a number
                            self.ref_psi_num = format(float(r_str[31:39]),'.1f')
                        except:
                            self.cprint("Problem with psi num")
                            #raise
                            return 'error'
                            self.connect_countdown()
                        else:
                            self.poll_fail_count = 0
                            self.gd = 1
                            self.get_valve_states()
                            self.check_alarms()                     
                            Dict = {'dest':'ref_readings','data':'good','ref_in_num':self.ref_in_num, 'ref_psi_num':self.ref_psi_num}
                            return Dict

    def check_alarms(self):
        # check for high sp---------------
        if float(self.ref_psi_num) > self.sp_high_stpt: # over ranging crystal sp
            if self.sp_alarm_status == 0:
                self.send_web_message("Alarm: High SP",0)
                self.mq(self.qw3,{'dest':'sp_high_alarm', 'data':'1'}) # change display color
                self.sp_alarm_status = 1
            if self.vent_status == 0: # psi vent is currently closed
                self.send_web_message("Auto opening the psi vent for high SP",0)
                Dict = {'dest':'q13','purpose':'vent_alarm','data':'1'} # open the psi vent for high SP
                self.mq(self.q13, Dict)                  
        elif self.sp_alarm_status == 1: # psi in normal range - reset high sp alarm
            self.send_web_message("SP high alarm reset",0)
            self.mq(self.qw3,{'dest':'sp_high_alarm', 'data':'0'}) # change display color
            self.sp_alarm_status = 0
            Dict = {'dest':'q13','purpose':'vent_alarm','data':'0'} # reset
            self.mq(self.q13, Dict)
        # check for high sp---------------
        
        # check sp high enough to need to open equalizer---------------
        if float(self.ref_psi_num) > self.psi_open_equalizer_stpt:
            if self.eq_status == 1: # equalizer is currently closed
                self.send_web_message("Auto opening the equalizer for high psi",0)
                Dict = {'dest':'cntrl','purpose':'eq','data':'0'} # open the equalizer for high psi
                self.mq(self.q9, Dict)
        # check sp high enough to need to open equalizer---------------
        
        # check for high dp---------------
        if float(self.ref_in_num) > self.dp_high_stpt: # over ranging crystal dp
            if self.dp_alarm_status == 0:
                self.cprint("Alarm: High DP")
                self.send_web_message("Alarm: High DP",0)
                self.mq(self.qw3,{'dest':'dp_high_alarm', 'data':'1'}) # change display color
                self.dp_alarm_status = 1
                
            if self.eq_status == 1: # eq is currently closed
                self.send_web_message("Auto opening the equalizer for high DP",0)
                Dict = {'dest':'q12','purpose':'eq_alarm','data':'0'} # open the equalizer for high dp
                self.mq(self.q12, Dict)
            if self.vent_status == 0: # psi vent is currently closed
                self.send_web_message("Auto opening the vent for high DP",0)
                Dict = {'dest':'q13','purpose':'vent_alarm','data':'1'} # open the psi vent for high DP
                self.mq(self.q13, Dict)
            if self.in_vent_status == 0: # inch vent is currently closed
                self.send_web_message("Auto opening the in vent for high DP",0)
                Dict = {'dest':'q14','purpose':'in_vent_alarm','data':'1'} # open the inch vent for high DP
                self.mq(self.q14, Dict)                 
        elif self.dp_alarm_status == 1: # dp in normal range - reset high dp alarm
            self.cprint("High DP alarm reset")
            Dict = {'dest':'q14','purpose':'in_vent_alarm','data':'0'} # reset
            self.mq(self.q14, Dict)
            Dict = {'dest':'q13','purpose':'vent_alarm','data':'0'} # reset
            self.mq(self.q13, Dict)
            self.mq(self.qw3,{'dest':'dp_high_alarm', 'data':'0'}) # change display color                  
            self.dp_alarm_status = 0
        # check for high dp---------------    

        # DP reading during SP testing ---------------
        if self.auto_mode == 'p' and float(self.ref_in_num) > self.auto_psi_in_alarm_stpt:
            if self.auto_psi_in_alarm_status == 0:
                self.send_web_message("Alarm: high DP during SP test",0)
                self.cprint("Alarm: DP reading too high during SP testing")
                self.mq(self.qw3,{'dest':'auto_sp_in_alarm', 'data':'1'}) # change display color
                self.auto_psi_in_alarm_status = 1                
            if self.vent_status == 0: # psi vent is currently closed
                self.send_web_message("Auto opening the vent for high DP during SP testing",0)
                Dict = {'dest':'q13','purpose':'vent_alarm','data':'1'} # open the psi vent for high DP during SP testing
                self.mq(self.q13, Dict)
        elif self.auto_psi_in_alarm_status == 1: # dp in normal range - reset high dp alarm
            self.send_web_message("High DP during SP test alarm reset",0)
            Dict = {'dest':'q13','purpose':'vent_alarm','data':'0'} # reset
            self.mq(self.q13, Dict)
            self.mq(self.qw3,{'dest':'auto_sp_in_alarm', 'data':'0'}) # change display color                  
            self.auto_psi_in_alarm_status = 0
        # DP reading during SP testing ---------------
                
    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (serialworker%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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
               
    def mq(self, q, val, block = False, timeout = 0.05): # verify queue transmission
        if block == 1:
            block = True
        try:
            self.q = q
            try:
                while self.q.full():
                    self.q.get(block, timeout)
            except:
                self.cprint("error : while self.q.full():")
                #raise
            else:
                try:
                    self.q.put(val, block, timeout)         
                except:
                    self.cprint("error : self.q.put(val, block, timeout)         ")
                    #raise
        except:
            self.cprint("error : self.q = q")
            #raise
                               
    def init_kpv_to_val(self, index = 'init', val = 0):
        self.serial_port = '/dev/serial/by-id/usb-Crystal_Crystal_Engineering_USB_Device-if00-port0'
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
                    #self.cprint("{%s}(%s)[%s] = %s"%(type(self.Kpv[self.kpv_index_list[i]]),self.kpv_vars_list[i],self.kpv_index_list[i],self.Kpv[self.kpv_index_list[i]]))
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
        if self.crystal_inhibit_prev == None: # initialize
            Dict = {'dest':'crystal_inhibit','crystal_inhibit':str(self.crystal_inhibit)}
            self.mq(self.qw5, Dict)
        elif self.crystal_inhibit != self.crystal_inhibit_prev:
            if self.crystal_inhibit == 1:
                self.cprint("Reference pressure readings disabled")
            else:
                self.cprint("Reference pressure readings enabled")
                self.mq(self.qs12,{"purpose":"clear_crystal_alarm","data" : "1"})
            Dict = {'dest':'crystal_inhibit','crystal_inhibit':str(self.crystal_inhibit)}
            self.mq(self.qw5, Dict)
        self.crystal_inhibit_prev = self.crystal_inhibit
        if self.crystal_revision == 2:
            self.in_str = 'P11'
        elif self.crystal_revision == 3:
            self.in_str = 'P11'
            
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py

    def check_input(self):
        #self.cprint('check_input')
        if not self.qs1.empty():
            data = self.qs1.get()
            self.eq_status_get = int((data['data']))                
        if not self.qs2.empty():
            data = self.qs2.get()                
            self.vent_status_get = int((data['data']))                
        if not self.qs3.empty():
            data = self.qs3.get()            
            self.in_vent_status_get = int((data['data']))                 
        if not self.qs4.empty():
            data = self.qs4.get()
            self.cprint("DP high alarm display received")
            self.dp_high_alarm_display = int((data['data']))                
        if not self.qs5.empty():
            data = self.qs5.get()
            self.sp_high_alarm_display = int((data['data']))
        if not self.qs9.empty():
            data = self.qs9.get()
            self.auto_mode = data['data']
        if not self.qs10.empty(): # get updated kpv from cntrl.py
            obj = self.qs10.get()
            index = obj[0]
            val = obj[1]
            self.init_kpv_to_val(index,val) # set local process kpv values
        if not self.qs11.empty():
            data = self.qs11.get()
            self.auto_sp_in_alarm_display = int((data['data']))
        if not self.qs12.empty(): # restart crystal communication attempts
            data = self.qs12.get()
            self.poll_fail_count = 0
            self.poll_fail = 0
            self.mq(self.qw27,{'dest':'crystal_alarm_cleared'}) # disable clear crystal alarm button
            
    def run(self):
        #self.cprint("serialworker.py running")
        while self.qs10.empty():
            time.sleep(1)
        obj = self.qs10.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None                   
        self.init_kpv_to_val('init') 
        #self.cprint("serialworker.py kpv imported successfully")                                
        inw = 0
        if self.crystal_inhibit == 0:                   
            try:
                self.ser = serial.Serial(self.serial_port, self.serial_baudrate, timeout=1, parity=serial.PARITY_NONE, rtscts=0)
            except:
                self.send_web_message("Initial attempt to connect to crystal failed",3)
                #raise
                self.connect_countdown()
            try:
                self.ser.reset_input_buffer()
            except:
                self.send_web_message("Initial connect to crystal failed",2)
                #raise
                self.cprint("Unable to clear crystal input buffer")
                self.connect_countdown()
            else:
                #self.cprint("\nCrystal input buffer reset")
                self.lta = []
                stlt = time.time()
                time.sleep(2) # allow crystal time to boot
                    
        while True:   
            #print("serialworker.py  %s"%time.time())
            self.check_input()                   
            # get data from crystal
            if self.crystal_inhibit == 0:
                if self.poll_fail == 0 and self.cdt == 0:
                    try:
                        inw = self.ser.in_waiting
                    except:
                        #raise
                        self.cprint("problem at in waiting")
                        self.connect_countdown()
                    else:
                        if (inw > 0 and self.poll_fail == 0 and self.cdt == 0):
                            try:
                                data = self.readSerial()
                            except:
                                #raise
                                self.mq(self.qs7, {'data':'error'})
                                self.connect_countdown()
                            else:
                                if data == 'error':
                                    self.mq(self.qs7, {'data':'error'})
                                    self.connect_countdown()
                                if data != 'error':    
                                    if len(self.lta) > 30:
                                        self.lta.pop(0)
                                    self.mq(self.qw5, data)
                                    self.mq(self.qs7, data)
                        elif inw < 1:
                            self.cprint("Crystal buffer in_waiting is empty")
                            self.connect_countdown()
                        elif self.poll_fail != 0:
                            self.cprint("crystal poll fail")
                        elif self.cdt != 0:
                            self.cprint("re-connect to crystal countdown timer running")
                        if not self.qs6.empty():
                            data = self.qs6.get()
                            self.writeSerial(data['data'])
                time.sleep(0.1)
