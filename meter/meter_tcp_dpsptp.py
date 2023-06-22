import serial, time, multiprocessing,inspect, logging, logging.config, logging.handlers, math
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('meter_tcp_dpsptp')

class Meter_tcp_dpsptp_process(multiprocessing.Process):
    def __init__(self, q22, q25, qtd1, qtd4, qtd5, qtd6, qw6, qw29, qw36):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['meter_tcp_check_interval', 'new_ip',            'new_port', \
                              'new_unit',                 'reconnect_time',    'meter_tcp_inhibit', 'meter_tcp_max_attempts' ]
        self.kpv_index_list = [240, 241, 242, \
                               243, 244, 245, 238 ]
        self.KpvTypes = []  
        self.q22 = q22 # check meter tcp connection request from web
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.qtd1 = qtd1 # Modify ip address in meter_data.py
        self.qtd4 = qtd4 # send kpv file to meter_tcp_dpsptp.py
        self.qtd5 = qtd5 # meter dp to cntrl.py
        self.qtd6 = qtd6 # meter tcp connection status for cntrl.py
        self.qw6 = qw6 # meter tcp connection status to controls page
        self.qw29 = qw29 # dpsptp to web
        self.qw36 = qw36 # send_web_message for meter_tcp_dpsptp.py

        self.meter_num_reg = 6 # number of modbus registers to read in
        #self.meter_num_reg = 3 # number of modbus registers to read in
        self.meter_start_reg = '7000' # starting register
        self.meter_connect = 0
        self.meter_tcp_attempts = 0
        self.prev_msg = ""
        self.st = 0
        self.st_set = 0
        
        self.web_prev_msg = ""

        self.tcp_write_err = 0
        self.meter_TCP_address = '0.0.0.0'
        self.meter_TCP_port = 0
        self.meter_TCP_unit = 0
        self.initial_connect = 0

        self.meter_tcp_inhibit = 1
        self.meter_tcp_inhibit_prev = 1
            
    def connect(self):
        while self.meter_tcp_inhibit == 0:
            self.meter_tcp_attempts += 1
            #self.cprint("self.meter_tcp_attempts : %s"%self.meter_tcp_attempts,1,'d')
            self.check_kpv()
            if self.meter_tcp_attempts > self.meter_tcp_max_attempts:
                self.cprint("%s attempts to connect to meter tcp have failed. Restart program to try again"%self.meter_tcp_max_attempts)
                self.send_web_message("%s attempts to connect to meter tcp have failed. Restart program to try again"%self.meter_tcp_max_attempts)
                self.mod_kpv_entry(245,1) # inhibit further attempts
                self.meter_tcp_inhibit = 1
                return
            if self.meter_connect == 0:
                self.cprint("Attempting to connect to meter tcp - attempt %s/%s"%(self.meter_tcp_attempts,self.meter_tcp_max_attempts))
                self.send_web_message("Attempting to connect to meter tcp - attempt %s/%s"%(self.meter_tcp_attempts,self.meter_tcp_max_attempts))        
            try:
                self.client = ModbusTcpClient(self.meter_TCP_address, port=self.meter_TCP_port, debug=True)
            except:
                self.cprint("Not able to create ModbusTcpClient : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
                self.send_web_message("Not able to create ModbusTcpClient : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
            else:
                try:
                    self.tcp_connected = self.client.connect()
                except:
                    self.cprint("Not able to attempt connection to meter : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
                    self.send_web_message("Not able to attempt connection to meter : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))      
                else:
                    if self.tcp_connected == True:
                        if self.meter_connect == 0:
                            self.cprint("TCP to meter open : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port),0,1)
                        self.meter_connect = 1
                        data = {'dest':'meter_tcp_connection','data':'1'}
                        self.mq(self.qw6,data)
                        self.meter_tcp_attempts = 0
                        success = True
                        return
                    else:
                        self.cprint("Not able to connect to meter tcp : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
                        self.send_web_message("Not able to connect to meter tcp : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
            # un-successful connection
            data = {'dest':'meter_tcp_connection','data':'0'}
            self.mq(self.qw6,data) 
            time.sleep(self.reconnect_time)

    def close(self):
        try:
            self.client.close()
        except:
            if self.meter_connect == 1:
                self.cprint("Not able to close the tcp connection to meter")
                self.send_web_message("Not able to close the tcp connection to meter")
        else:
            if self.meter_connect == 1:
                self.send_web_message("Closed tcp connection to meter")
                self.cprint("Closed tcp connection to meter")
            
    def mod_ip(self, data):
        if data['purpose'] == "set_meter_ip":
            self.mod_kpv_entry(241,str(data['data']) + '\n')
                     
    def read_dpsptp(self):
        meter_reg_arr = []
        Dict = {'dest':'meter_readings','data':'error','meter_in_num':'error','meter_psi_num':'error','meter_temp':'error'}
        #print('self.meter_connect : %s'%self.meter_connect)
        if self.meter_connect == 1:
            
            try:
                #result = self.client.read_holding_registers(6999, 3, unit=1) # register start, number of registers, unit id
                result = self.client.read_holding_registers(7000, 6, unit=1) # register start, number of registers, unit id
            except:
                self.cprint("Problem reading holding registers from meter")
                self.connect()               
            else:
                try:
                    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Little)
                except:
                    self.cprint("problem with decoding registers")
                    self.connect()
                else:
                    try:
                        for i in range(0,int(self.meter_num_reg / 2)):
                            meter_reg_arr.append(decoder.decode_32bit_float())
                    except:
                        self.cprint("problem with decoding registers")
                        self.connect()
                    else:
                        if type(meter_reg_arr[0]) == float and type(meter_reg_arr[1]) == float and type(meter_reg_arr[2]) == float: 
                            self.meter_in_num = ("{0:0.3f}".format(meter_reg_arr[0]))
                            self.meter_psi_num = ("{0:0.3f}".format(meter_reg_arr[1]))
                            self.meter_temp = ("{0:0.3f}".format(meter_reg_arr[2]))
                            Dict = {'data':'good','dest':'meter_readings','meter_in_num':self.meter_in_num, 'meter_psi_num':self.meter_psi_num, 'meter_temp':self.meter_temp}
                            #print(Dict)
        return Dict

    def cprint(self, msg = "",printout = True, web = False,lvl = None):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (meter_tcp_dpsptp%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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
                None
            else:
                try:
                    self.q.put(val, block, timeout)
                except:
                    None
        except:
            None    
                               
    def init_kpv_to_val(self, index = 'init', val = 0):
        #self.cprint("self.meter_tcp_inhibit : %s"%self.meter_tcp_inhibit)
        #self.cprint('init_kpv')
        tv = 'int'
        if len(self.kpv_vars_list) > 0:
            if index == 'init':
                new_ip = ''
                new_port = ''
                new_unit = ''
                for i in range(len(self.kpv_vars_list)):
                    #self.cprint("%s[%s]{%s}(%s) = %s"%(i,self.kpv_index_list[i],self.kpv_vars_list[i],self.KpvTypes[self.kpv_index_list[i]],self.Kpv[self.kpv_index_list[i]]))
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
            
        if self.meter_tcp_inhibit == 0:
            self.meter_tcp_attempts = 0
        check_tcp = 0
        ip = self.meter_TCP_address
        port = self.meter_TCP_port
        unit = self.meter_TCP_unit
        #self.cprint("meter tcp inhibit %s"%self.meter_tcp_inhibit)
        if ip != self.new_ip:
            self.meter_TCP_address = self.new_ip
            check_tcp = 1
        if port != self.new_port:
            self.meter_TCP_port = self.new_port
            check_tcp = 1
        if unit != self.new_unit:
            self.meter_TCP_unit = self.new_unit
            check_tcp = 1
        #self.cprint("%s:%s/%s"%(self.meter_TCP_address,self.meter_TCP_port,self.meter_TCP_unit))
        if self.initial_connect == 1 and check_tcp == 1: # tcp was connected and then a change was made requiring tcp check
            self.connect() # try to connect with new settings
        if self.initial_connect == 0 and self.meter_tcp_inhibit == 0:
            self.cprint("initial tcp connection to meter")
            self.connect()
        #self.cprint("self.meter_tcp_inhibit : %s"%self.meter_tcp_inhibit)
            
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
        
    def check_kpv(self):
        if not self.qtd1.empty(): # Modify ip address in meter_data.py
            data = self.qtd1.get()
            self.mod_ip(data)
        if not self.qtd4.empty(): # get updated kpv from cntrl.py
            data = self.qtd4.get()
            index = data[0]
            val = data[1]
            #self.cprint(data)
            self.init_kpv_to_val(index,val)

    def send_web_message(self, var, clstime = 0):
        if clstime != 0:
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw36.put(Dict)
        Dict = {'dest':'web_message', 'val':var}
        self.qw36.put(Dict)
        self.prev_msg = var
        if clstime != 0:
            time.sleep(clstime)
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw36.put(Dict)
                    
    def run(self):
        #self.cprint("meter_tcp.py running")
        while self.qtd4.empty():
            time.sleep(1)
            #print('here')
        obj = self.qtd4.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            #print('here')
            None
        self.init_kpv_to_val('init') 
        #self.cprint("meter_tcp.py kpv imported successfully")
        #self.cprint("self.meter_tcp_inhibit : %s"%self.meter_tcp_inhibit)
        if self.meter_tcp_inhibit == 1:
            self.cprint("Tcp communication to meter disabled by user")
            self.send_web_message("Tcp communication to meter disabled by user")
        while True:
            self.check_kpv()
            #self.cprint('self.meter_tcp_inhibit : %s'%self.meter_tcp_inhibit)
            #if self.st_set ==0:
            #    self.st_set = 1
            #    self.st = time.time()
            #if time.time() - self.st > 60: # periodically print ip address
                #self.cprint("meter IP = %s " %self.meter_TCP_address)
                #self.st_set = 0
                #self.st = time.time()
                                        
            if self.meter_tcp_inhibit != self.meter_tcp_inhibit_prev:
                if self.meter_tcp_inhibit == 0:
                    self.send_web_message("tcp to meter enabled")
                    self.connect()
                elif self.meter_tcp_inhibit == 1:
                    Dict = {'dest':'meter_readings','data':'error','meter_in_num':'error','meter_psi_num':'error','meter_temp':'error'}
                    self.mq(self.qw29,Dict) # meter dpsptp to web
                    self.mq(self.qtd5,Dict) # meter dpsptp to cntrl.py                                    
                    data = {'dest':'meter_tcp_connection','data':'0'}
                    self.mq(self.qw6,data)
                    self.send_web_message("tcp to meter disabled")
                self.meter_tcp_inhibit_prev = self.meter_tcp_inhibit

            if self.meter_tcp_inhibit == 0:
                if not self.q22.empty(): # check meter tcp connection request from web
                    data = self.q22.get()
                    self.initial_connect = 1
                    if data['purpose'] == 'check_meter_tcp':
                        self.cprint("checking tcp connection to meter")
                        self.connect() # connect function
                # live readings from meter
                data = self.read_dpsptp() # read data from meter
                self.mq(self.qw29,data) # meter dpsptp to web
                self.mq(self.qtd5,data) # meter dpsptp to cntrl.py                
                               
                
            time.sleep(0.05)
