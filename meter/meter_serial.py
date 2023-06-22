import serial
import time
import multiprocessing
import inspect,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('meter_serial')                     

class Meter_serial_process(multiprocessing.Process):
    def __init__(self,q25,q35,qts1,qts2,qts3,qts4,qw30):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['max_poll_fail','serial_baudrate','read_in','meter_rs232_inhibit']
        self.kpv_index_list = [230,231,232,233]
        self.KpvTypes = []     
        self.q25 = q25        
        self.q35 = q35 # Register to read      
        self.qts1 = qts1 # send kpv file to meter_serial.py
        self.qts2 = qts2
        self.qts3 = qts3
        self.qts4 = qts4 # write data to meter rs232
        self.qw30 = qw30 # Send web message for meter_serial.py
        
        self.Kpv = []       
        
        self.prev_Dict = None
        self.prev_msg = ""
        
        self.poll_fail_count = 0
        self.poll_fail = 0
        
        self.prev_msg = ""
       
        self.sltm = 0.001
        
        self.testc = 0
        self.testa = {'DP':'11.7.0','SP':'11.3.0','Temp':'11.3.3','Battery':'7.3.5','Charger':'7.3.6','Today':'11.7.22','Yest':'11.7.23','Flow':'11.7.19'};
        self.testk = list(self.testa) # accessible list of dictionary key values
        self.lt = 0
        self.st = 0
        self.lta = 0
        self.count = 1
        self.meter_rs232_inhibit = 0
             
    def check_port_status(self):
        #Determine correct meter serial port - Verify ability to read in data
        self.send_web_message("Checking meter rs232 port status",0)
        if self.poll_fail_count >= self.max_poll_fail:
            self.poll_fail = 1          
            self.send_web_message("%s attempts to connect to meter rs232 have failed. No more attempts will be made.\
                         Please verify the connection is working and connected, then restart the program."\
                         %int(self.max_poll_fail),0)
        else:
            try:
                self.ser = serial.Serial(self.serial_port, self.serial_baudrate, timeout=1, parity=serial.PARITY_NONE, stopbits=2, rtscts=0)
            except:
                self.send_web_message("Not able to open serial port to meter",2)
                self.connect_countdown()
            else:        
                try:
                    inw = self.ser.in_waiting
                except:
                    self.cprint("problem with in waiting")
                    self.connect_countdown()
                else:        
                    self.send_web_message("Serial port to meter opened",0.5)
                    try:
                        self.ser.write(b'TERM') #start the data stream
                    except:
                        self.connect_countdown()                   
                        self.send_web_message("meter rs232 not taking commands",2)
                    else:
                        self.send_web_message("meter rs232 is taking commands",0.5)
                        try:
                            var = self.ser.read(self.read_in).decode()#read in 50 bytes from the data stream
                        except:
                            self.send_web_message("Not able to decode meter rs232 data stream",2)
                            self.connect_countdown() 
                            var = "..."                       
                        else:
                            if var != "": #non empty string from data stream indicates commands are working
                                self.port_works = 1
                                self.send_web_message("rs232 communication to meter successful",1.5)
                            else:
                                self.cprint("empty string")
                                self.connect_countdown()
                          
            time.sleep(self.sltm)
            
    def connect_countdown(self):
        Dict = {'dest':'poll_fail'}       
        self.cdt = 1
        self.poll_fail_count += 1
        self.cprint("self.poll_fail_count : %s  self.max_poll_fail : %s"%(self.poll_fail_count,self.max_poll_fail))
        self.send_web_message("Problem reading in from meter rs232",2)
        try:
            self.ser.close()
        except:
            self.send_web_message("Not able to close serial port to meter",2) 
        #self.mq(self.q21, {'purpose':'stop_pid', 'data':'0'})
        st  = time.time()
        ct = 5
        dt = 0
        tu = 0
        while tu < 6:
            dt = time.time() - st
            if dt > tu:
                self.send_web_message("Attempt %s/%s to connect to meter rs232 in %s"%(self.poll_fail_count,int(self.max_poll_fail),ct),1)
                ct -= 1
                tu += 1
        self.cdt = 0
        self.check_port_status()

    def writeSerial(self, data):
        try:
            self.ser.write(data.encode())
            self.ser.write(b'\r')
            #self.ser.write(str(data))
        except:
            self.connect_countdown()

    def send_web_message(self, var, clstime):
        if clstime != 0:
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw30.put(Dict)
        Dict = {'dest':'web_message', 'val':var}
        self.qw30.put(Dict)
        self.prev_msg = var
        if clstime != 0:
            time.sleep(clstime)
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw30.put(Dict)
        
    def readSerial(self):
        try:
            r_str = (self.ser.read(self.read_in)).decode()
        except:
            self.cprint("Problem reading in string from meter rs232")
            self.connect_countdown()
            raise
        else:    
            return r_str
                
    def parse_read(self, r_str):
        r_str = r_str[r_str.find("\n")+1:r_str.find(">")-3]
        self.ser.reset_input_buffer()
        return r_str

    def check_alarms(self):
        # check for high sp---------------
        if float(self.psi_num) > self.sp_high_stpt: # over ranging meter sp
            if self.sp_alarm_status == 0:
                self.mq(self.qw3,{'dest':'meter_sp_high_alarm', 'data':'1'}) # change display color
                self.sp_alarm_status = 1
            if self.vent_status == 0: # psi vent is currently closed
                self.send_web_message("Auto opening the psi vent for high meter SP",0)
                Dict = {'dest':'q13','purpose':'vent_alarm','data':'1'} # open the psi vent for high SP
                self.mq(self.q13, Dict)                  
        elif self.sp_alarm_status == 1: # psi in normal range - reset high sp alarm
            self.mq(self.qw3,{'dest':'meter_sp_high_alarm', 'data':'0'}) # change display color
            self.sp_alarm_status = 0
            Dict = {'dest':'q13','purpose':'vent_alarm','data':'0'} # reset
            self.mq(self.q13, Dict)
        # check for high sp---------------
        
        # check sp high enough to need to open equalizer---------------
        if float(self.psi_num) > self.psi_open_equalizer_stpt:
            if self.eq_status == 1: # equalizer is currently closed
                self.send_web_message("Auto opening the equalizer for high meter psi",0)
                Dict = {'dest':'cntrl','purpose':'eq','data':'0'} # open the equalizer for high psi
                self.mq(self.q9, Dict)
        # check sp high enough to need to open equalizer---------------
        
        # check for high dp---------------
        if float(self.in_num) > self.dp_high_stpt: # over ranging meter dp
            if self.dp_alarm_status == 0:
                self.cprint("Alarm: High meter DP")
                self.mq(self.qw3,{'dest':'meter_dp_high_alarm', 'data':'1'}) # change display color
                self.dp_alarm_status = 1
                
            if self.eq_status == 1: # eq is currently closed
                self.send_web_message("Auto opening the equalizer for high meter DP",0)
                Dict = {'dest':'q12','purpose':'eq_alarm','data':'0'} # open the equalizer for high dp
                self.mq(self.q12, Dict)
            if self.vent_status == 0: # psi vent is currently closed
                self.send_web_message("Auto opening the vent for high meter DP",0)
                Dict = {'dest':'q13','purpose':'vent_alarm','data':'1'} # open the psi vent for high DP
                self.mq(self.q13, Dict)
            if self.in_vent_status == 0: # inch vent is currently closed
                self.send_web_message("Auto opening the in vent for high meter DP",0)
                Dict = {'dest':'q14','purpose':'in_vent_alarm','data':'1'} # open the inch vent for high DP
                self.mq(self.q14, Dict)                 
        elif self.dp_alarm_status == 1: # dp in normal range - reset high meter dp alarm
            Dict = {'dest':'q14','purpose':'in_vent_alarm','data':'0'} # reset
            self.mq(self.q14, Dict)
            Dict = {'dest':'q13','purpose':'vent_alarm','data':'0'} # reset
            self.mq(self.q13, Dict)
            self.mq(self.qw3,{'dest':'meter_dp_high_alarm', 'data':'0'}) # change display color                  
            self.dp_alarm_status = 0
        # check for high dp---------------    
        
    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (meter_serial%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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
                self.cprint("error in mq")
            else:
                try:
                    self.q.put(val, block, timeout)         
                except:
                    self.cprint("error in mq:")
        except:
            self.cprint("error in mq::")
 
                               
    def init_kpv_to_val(self, index = 'init', val = 0):
        self.serial_port = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0'        
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
        self.cdt = 0
        #self.cprint("meter_serial.py running")
        while self.qts1.empty():
            time.sleep(1)
        obj = self.qts1.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None          
        self.init_kpv_to_val('init')         
        #self.cprint("meter_serial.py kpv imported successfully")                                
        inw = 0
        try:
            self.ser = serial.Serial(self.serial_port, self.serial_baudrate, timeout=1, parity=serial.PARITY_NONE, stopbits = 2, rtscts=0)
        except:
            self.send_web_message("Initial attempt to connect to meter rs232 failed", 3)
            self.connect_countdown()        
        else:
            self.cprint("Initial attempt to connect to meter rs232 successful")
        try:
            self.ser.reset_input_buffer()
        except:
            self.send_web_message("Initial connect to meter rs232 failed",2)
            self.cprint("Unable to clear meter rs232 input buffer")
            self.connect_countdown()
        else:
            self.cprint("meter reset_input_buffer successful")
            stlt = time.time()
            time.sleep(2) # allow time to boot ( may not be necessary )
            while True and self.meter_rs232_inhibit == 0:   
                if not self.qts2.empty():
                    data = self.qts2.get()                
                if not self.qts3.empty():
                    data = self.qts3.get()                              
                if not self.qts1.empty(): # get updated kpv from cntrl.py
                    obj = self.qts1.get()
                    index = obj[0]
                    val = obj[1]
                    while len(self.Kpv) == 0: # wait for kpv to populate
                        self.cprint("meter_serial : getting kpv")
                    self.init_kpv_to_val(index,val) # set local process kpv values                                                                   
                    
                #self.writeSerial("7.3.5")                
                
                if self.st == 0:
                    self.st = time.time()
                # self.writeSerial(self.testa[self.testk[self.testc]]) # request a register value from meter
                # get data from meter rs232
                
                if self.poll_fail == 0 and self.cdt == 0: 
                    try:
                        inw = self.ser.in_waiting
                    except:
                        self.cprint("problem at in waiting")
                        self.connect_countdown()
                    else:
                        if (inw >= self.read_in and self.poll_fail == 0 and self.cdt == 0):
                            r_str = self.readSerial()
                            if r_str != None:
                                r_str = self.parse_read(r_str)
                            if r_str != None:
                                print(self.testk[self.testc] + " : %s  index : %s"%(r_str,self.testc))    
                                self.lt = time.time() - self.st
                                self.lta = self.lt / self.count
                                print("lta : %s"%self.lta)
                                self.count += 1
                                self.testc += 1
                                if self.testc == len(self.testa):
                                    self.testc = 0                                                                
                        elif self.poll_fail != 0:
                            self.cprint("meter rs232 poll fail")
                        elif self.cdt != 0:
                            self.cprint("re-connect to meter rs232 countdown timer running")
                        if not self.qts4.empty():
                            data = self.qts4.get()
                #if self.ser.in_waiting > 0:
                #    print((self.ser.read(self.read_in)).decode())
                if not self.q35.empty():
                    data = self.q35.get()
                    self.cprint("Write register command issued")                                
                    reg = data['data']
                    self.cprint("Writing : %s"%reg)
                    self.writeSerial(data['data'])
                if not self.qts1.empty(): # get updated kpv from cntrl.py
                    obj = self.qts1.get()
                    index = obj[0]
                    val = obj[1]

                    self.init_kpv_to_val(index,val) # set local process kpv values                                                 
                time.sleep(0.05)

