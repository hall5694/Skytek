import serial
import time
import multiprocessing
import inspect
import minimalmodbus,logging,logging.config,logging.handlers

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('usb485')                

class USB485_Process(multiprocessing.Process):
    def __init__(self, q20, q25, qu1, qu2, qu3, qw4, qw11):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['max_poll_fail','serial_baudrate','serial_parity','serial_stopbits', \
                              'read_interval','slave_address','usb_485_inhibit']
        self.kpv_index_list = [217,218,219,220, \
                               221,222,223]                            
        self.KpvTypes = []
        self.q20 = q20 # temp readings for cntrl.py
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.qu1 = qu1 # send kpv from cntrl to usb485.py
        self.qu2 = qu2 # NA
        self.qu3 = qu3 # send kpv file to usb485.py
        self.qw4 = qw4 # temp readings from usb485.py
        self.qw11 = qw11 # send_web_message for usb485.py
        self.st_set = 0
        self.st = 0
        pst = time.time()
        self.prev_msg = ""
        self.web_prev_msg = ''

        self.Kpv=[]
                
        self.dc = 0 # dead count
        self.usb_485_inhibit = 0
        self.usb_485_inhibit_prev = 0
        self.read_paused = 0
        self.poll_fail_count = 0

    def read_temp(self):
        try:
            temp = self.instrument.read_register(5) # read register #5
        except:
            self.cprint("Not able to read in reference temperature sensor")
            #raise          
            return("error")
        else:
            tens = int(temp / 10);
            dec = (temp % 10)/10;
            var = ("{0:0.1f}".format(tens + dec))
            Dict = {'data':'good','dest':'temp_readings','temp':var}
            return Dict

    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (usb485%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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

    def send_web_message(self, var):
        if var != self.web_prev_msg:
            Dict = {'dest':'web_message', 'val':var}
            self.qw11.put(Dict)
            self.web_prev_msg = var
              
    def get_data(self):
        try:
            data = self.read_temp()
        except:
            self.cprint("exception in usb485.py line")
            self.poll_fail_count += 1
            #raise
        else:
            if data != "error":
                self.mq(self.qw4, data)
                self.mq(self.q20, data)
                if self.poll_fail_count > 0:
                    self.poll_fail_count = 0
                    self.cprint("reference temperature readings restored",1,1)
            else:
                self.poll_fail_count += 1
                self.cprint("Reference temperature read fail %s/%s"%(self.poll_fail_count, self.max_poll_fail),1,1)
                data = {'data':'error','dest':'temp_readings','temp':'error'}
                self.mq(self.qw4, data)
                self.mq(self.q20, data)
                time.sleep(3)
                try:          
                    self.instrument = minimalmodbus.Instrument(self.serial_port, self.slave_address)
                    self.instrument.serial.baudrate = self.serial_baudrate
                    self.instrument.serial.stopbits = self.serial_stopbits                
                except:
                    self.cprint('not able to connect usb485 temperature')
                    time.sleep(3)
                    
            
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
            
        if self.usb_485_inhibit != self.usb_485_inhibit_prev:
            self.usb_485_inhibit_prev = self.usb_485_inhibit 
            if self.usb_485_inhibit == 1:
                self.cprint("Temperature readings enabled")
                data = {'dest':'temp_readings','temp':'error'}
                self.mq(self.qw4, data)
                self.mq(self.qu2, data)     
            if self.usb_485_inhibit == 0:
                self.cprint("Temperature readings disabled")
                self.poll_fail_count = 0
                
        self.serial_port = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AD0JLRXO-if00-port0'
        
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
                                          
    def run(self):
        #self.cprint("usb485.py running")
        while self.qu3.empty():
            time.sleep(1)
        obj = self.qu3.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None          
        self.init_kpv_to_val('init') 
        #self.cprint("usb485.py kpv imported successfully")
        if self.usb_485_inhibit == 0:   
            try:
                self.instrument = minimalmodbus.Instrument(self.serial_port, self.slave_address)
                self.instrument.serial.baudrate = self.serial_baudrate
                self.instrument.serial.stopbits = self.serial_stopbits              
                # self.instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1, "rtu", False, True)
                # self.instrument.serial.baudrate = 9600
                # self.instrument.serial.stopbits = 2   
            except:
                self.cprint("Not able to connect usb485")
                self.poll_fail_count += 1
                time.sleep(3)
                #raise
            else:
                self.get_data()

        while True:
            #print("usb485.py  %s"%time.time())
            if not self.qu1.empty():
                data = self.qu1.get()                              
            if self.st_set == 0:
                self.st = time.time()
                self.st_set = 1
            if time.time() - self.st > self.read_interval and self.usb_485_inhibit == 0:
                self.st = time.time()
                self.get_data()
                if self.poll_fail_count >= self.max_poll_fail:
                    self.cprint("%s attempts to read reference temperature have failed."%self.poll_fail_count,1,1)
                    self.cprint("Further attempts inhibited",1,1)
                    self.usb_485_inhibit = 1
                    self.mod_kpv_entry(223,self.usb_485_inhibit)
                    
            if not self.qu3.empty(): # kpv was modified
                obj = self.qu3.get()
                index = obj[0]
                val = obj[1]

                self.init_kpv_to_val(index,val) # set local process kpv values                      
                
            time.sleep(0.05)
