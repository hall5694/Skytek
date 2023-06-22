import serial, time, multiprocessing,inspect, logging, logging.config, logging.handlers, math
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('meter_tcp_rw')

class Meter_tcp_rw_process(multiprocessing.Process):
    def __init__(self, q25, q38, q40, qt1, qt2, qt3, qt4, qw31):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['max_tcp_read_err',  'max_tcp_write_err',  'new_ip',            'new_port', \
                              'new_unit',          'reconnect_time',     'meter_tcp_inhibit', 'meter_tcp_max_attempts' ]
        self.kpv_index_list = [236, 239, 241, 237, \
                               243, 244, 245, 238 ]
        self.KpvTypes = []  
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.q38 = q38 # returned data from meter_read_reg
        self.q40 = q40 # returned meter_write_reg status code
        self.qt1 = qt1 # Modify ip address in meter_tcp_rw.py
        self.qt2 = qt2 # write register to meter
        self.qt3 = qt3 # read register from meter
        self.qt4 = qt4 # send kpv file to meter_tcp_rw.py
        self.qw31 = qw31 # send_web_message for meter_tcp_rw.py

        self.meter_connect = 0
        self.meter_tcp_attempts = 0
        self.prev_msg = ""
        self.st = 0
        self.st_set = 0
        
        self.web_prev_msg = ""

        self.tcp_write_err = 0
        self.tcp_read_err = 0
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
                        self.meter_tcp_attempts = 0
                        success = True
                        return
                    else:
                        self.cprint("Not able to connect to meter tcp : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
                        self.send_web_message("Not able to connect to meter tcp : %s / %s"%(self.meter_TCP_address,self.meter_TCP_port))
            # un-successful connection
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

    def write_meter(self, data):
        self.tcp_write_err = 0
        #self.cprint("checking tcp connection to meter before write")
        self.connect() # had to add this to avoid broken pipe error - Modbus errno 32
        if self.meter_connect == 1:
            #self.builder = BinaryPayloadBuilder(byteorder=Endian.Little, wordorder=Endian.Little)
            self.builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little) # working with tflow 16 bit modicon
            ##self.builder = BinaryPayloadBuilder(byteorder=Endian.Little, wordorder=Endian.Big)
            ##self.builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
            register = int(data['register'])
            #self.cprint("register : %s"%register)
            val = data['value']
            self.data_type = data['data_type']
            try:
                tstamp = data['tstamp']
            except:
                tstamp = time.time()
            reg_dict = {'int':'int(val)','i':'int(val)','int32':'int(val)','i32':'int(val)',
                        'float':'float(val)','f':'float(val)','byte':'int(val)','b':'int(val)'}
            self.builder_dict = {'float':'self.builder.add_32bit_float(float(val))',
                'f':'self.builder.add_32bit_float(float(val))',
                'int':'self.builder.add_16bit_int(int(val))',
                'i':'self.builder.add_16bit_int(int(val))',
                'int32':'self.builder.add_32bit_int(int(val))',
                'i32':'self.builder.add_32bit_int(int(val))',                           
                'byte':'self.builder.add_bits([0,0,0,0,0,0,0,int(val)])',
                'b':'self.builder.add_bits([0,0,0,0,0,0,0,int(val)])'}  
            try:
                exec(self.builder_dict[self.data_type])
                exec("val = " + reg_dict[self.data_type])
            except:
                self.cprint("invalid data type entered")
                self.send_web_message("invalid data type entered")
                self.mq(self.q40,{'code':'error','tstamp':tstamp})
                return False
            else:
                self.cprint("Writing to meter - register: %s data: %s type : %s  time_stamp : %s"%(register,val, self.data_type,tstamp),1,0,'d')
                registers = self.builder.to_registers()
                #self.cprint(registers)
                payload = self.builder.build()
                #self.cprint(payload)
                register = (register//1000) * 1000 + ((register % 1000) * 2) # stupid totalflow...
                fault1 = err = fault2 = None
                while self.tcp_write_err < self.max_tcp_write_err:
                    #self.cprint('write attempt : %s'%self.tcp_write_err,0,0,'d')
                    try:
                        rq = self.client.write_registers(register-1, payload, skip_encode=True, unit=1)
                    except:
                        fault1 = 1
                        raise
                    else:
                        try:
                            time.sleep(0.01)
                            err = rq.function_code
                        except: # error code received
                            fault2 = 1
                        else:
                            if int(err) == 16:
                                self.builder.reset() # reset payload buffer
                                self.tcp_write_err = 0
                                self.mq(self.q40,{'reg':register,'code':int(err),'tstamp':tstamp})
                                return True
                    # write not successful - returns True otherwise
                    self.tcp_write_err += 1
                    time.sleep(0.2)
                    self.connect()
                            
                # max write attempts
                if err != None:
                    self.cprint("modbustcp error : function code : %s  time_stamp : %s"%(err,tstamp),1,1)
                if fault1 != None:
                    self.cprint("Not able to write register(s) to meter   time_stamp : %s"%tstamp,1,1)
                if fault2 != None:
                    self.cprint("modbus error after write attempt(register:%s) (data:%s) (dtype:%s) (err:%s) (time_stamp : %s)"%(register,val,self.data_type,rq, tstamp))
                self.cprint("Max number (%s) of write attempts reached"%self.max_tcp_write_err)
                self.mq(self.q40,{'code':'error','tstamp':tstamp})
                self.builder.reset() # reset payload buffer
                    
    def mod_ip(self, data):
        if data['purpose'] == "set_meter_ip":
            self.mod_kpv_entry(241,str(data['data']) + '\n')

    def read_meter(self, data):
        self.tcp_read_err = 0
        #self.cprint("checking tcp connection to meter before read")
        self.connect() # had to add this to avoid broken pipe error - Modbus errno 32
        self.cprint("read register request",1,0,None)
        if self.meter_connect == 1:
            return_to = data['return_to']
            register = int(data['register'])
            #self.cprint(register)
            data_type = data['data_type']
            type_dict = {'float':2,'f':2,'int':1,'i':1,'int32':2,'i32':2,'byte':1,'b':1,'string':1,'s':1}
            try:
                read_in = type_dict[data_type]
            except:
                self.cprint('bad data type entered')
                if return_to == "web":
                    self.send_web_message('bad data type entered')
                elif return_to == "cntrl":
                    Dict = {}
                    self.mq(self.q38,Dict)
            else:
                #self.cprint("read_in : %s"%read_in)
                #self.cprint("data_type : %s"%data_type)
                #self.cprint("register : %s"%register)
                meter_reg_arr = []
                eregister = (register//1000) * 1000 + ((register % 1000) * 2) # stupid totalflow...
                fault1 = fault2 = fault3 = fault4 = None
                while self.tcp_read_err < self.max_tcp_read_err:
                    try:
                        result = self.client.read_holding_registers(eregister - 1, read_in, unit=1)
                    except:
                        fault2 = 1
                    else:
                        if not result.isError():
                            #self.cprint(result)
                            #self.cprint(result.registers)
                            try:
                                decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Little)
                            except:
                                raise
                                fault3 = 1
                            else:
                                decode_dict = {'float':'decoder.decode_32bit_float()',
                                   'f':'decoder.decode_32bit_float()',
                                   'int':'decoder.decode_16bit_int()',
                                   'i':'decoder.decode_16bit_int()',
                                   'int32':'decoder.decode_32bit_int()',
                                   'i32':'decoder.decode_32bit_int()',                           
                                   'byte':'decoder.decode_8bit_int()',
                                   'b':'decoder.decode_8bit_int()',
                                   'string':'decoder.decode_string(size=32)',
                                   's':'decoder.decode_string(size=32)'}
                                try:
                                    self.val=''
                                    exec("self.val = " + str(decode_dict[data_type]))
                                except:
                                    fault3 = 1
                                else:
                                    if self.val != "":
                                        self.cprint("Read from meter - register: %s data: %s type : %s"%(register,self.val, data_type))
                                        self.mq(self.q38,{"register":register,"data":self.val,"type":data_type})
                                        return True
                                    else:
                                        fault4 = 1
                        else: # result.isError() = True
                            fault1 = 1

                # read failed            
                self.mq(self.q38,{"register":register,"data":"error"})
                if fault1 != None:
                    self.cprint("modbus error during read : %s"%result,1,1)                
                if fault2 != None:
                    self.cprint('not able to read holding registers from meter',1,1)
                if fault3 != None:
                    self.cprint("problem with decoding read registers",1,1)
                if fault4 != None:
                    self.cprint("empty data read from meter",1,1)
        else:
            self.cprint("connecting to meter for tcp read")
            self.connect()
                                
    def cprint(self, msg = "",printout = True, web = False,lvl = None):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (meter_tcp_rw%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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
        #self.cprint("mq  queue : %s  val : %s"%(q,val))
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
        self.meter_tcp_inhibit_prev = 1
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
            
        if not self.meter_tcp_inhibit:
            self.meter_tcp_attempts = 0
            self.meter_tcp_inhibit_prev = 0
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
            #self.cprint("initial tcp connection to meter")
            self.connect()
        #self.cprint("self.meter_tcp_inhibit : %s"%self.meter_tcp_inhibit)
            
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
        
    def check_kpv(self):
        if not self.qt1.empty(): # Modify ip address in meter_data.py
            data = self.qt1.get()
            self.mod_ip(data)
        if not self.qt4.empty(): # get updated kpv from cntrl.py
            data = self.qt4.get()
            index = data[0]
            val = data[1]
            #self.cprint(data)
            self.init_kpv_to_val(index,val)

    def send_web_message(self, var, clstime = 0):
        if clstime != 0:
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw31.put(Dict)
        Dict = {'dest':'web_message', 'val':var}
        self.qw31.put(Dict)
        self.prev_msg = var
        if clstime != 0:
            time.sleep(clstime)
            Dict = {'dest':'web_message', 'val':'cls'}
            self.qw31.put(Dict)
                    
    def run(self):
        #self.cprint("meter_tcp.py running")
        while self.qt4.empty():
            time.sleep(1)
            #print('here')
        obj = self.qt4.get()
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
            #if self.st_set ==0:
            #    self.st_set = 1
            #    self.st = time.time()
            #if time.time() - self.st > 60: # periodically print ip address
                #self.cprint("meter IP = %s " %self.meter_TCP_address)
                #self.st_set = 0
                #self.st = time.time()
            if self.meter_tcp_inhibit == 0:
                if self.meter_tcp_inhibit_prev == 1:
                    self.send_web_message("tcp to meter enabled")
                    self.meter_tcp_inhibit_prev = 0
                    if data['purpose'] == 'check_meter_tcp':
                        self.cprint("checking tcp connection to meter")
                        self.connect() # connect function
                if not self.qt2.empty(): # write to meter
                    data = self.qt2.get()
                    self.write_meter(data) # write was not successful
                if not self.qt3.empty(): # read from meter
                    data = self.qt3.get()
                    self.read_meter(data)
                
            time.sleep(0.05)
