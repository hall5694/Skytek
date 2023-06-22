import time
import busio
import board    
import multiprocessing
import inspect,logging,logging.config,logging.handlers
import adafruit_ina260

i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
ina260 = adafruit_ina260.INA260(i2c, 0x40)

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('analog_in')        

class Ai_Process(multiprocessing.Process):
    def __init__(self, q25, q28, q39, q42, qa1, qa2, qa3, qa4, qw26, qw35):
        multiprocessing.Process.__init__(self)
        self.kpv_vars_list = ['beam_inhibit',             'beam_fault_max', 'beam_fail_max', 'beam_trip_max',
                              'beam_post_to_web_interval'
                             ]
        self.kpv_index_list = [205, 206, 207, 208, \
                               209,
                              ]
        self.web_prev_msg = ""
        self.web_post_st = time.time()
        self.KpvTypes = []
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.q28 = q28 # stop button
        self.q39 = q39 # re-center command from analog_in.py
        self.q42 = q42 # zero adjuster position based on center beam sensor
        self.qa1 = qa1 # send kpv to analog_in.py
        self.qa2 = qa2 # send adjuster position to analog_in.py
        self.qa3 = qa3 # re-center complete from cntrl.py
        self.qa4 = qa4 # re-center command from cntrl to analog in
        self.qw26 = qw26 # beam indicators
        self.qw35 = qw35 # send_web_message for analog_in.py
        ads = ADS.ADS1115(i2c, address=0x48)
        chan = AnalogIn(ads, ADS.P0)
        self.st = time.time()
        self.read_interval = .1
        self.ch0 = AnalogIn(ads, ADS.P0)
        self.ch1 = AnalogIn(ads, ADS.P1)
        self.ch2 = AnalogIn(ads, ADS.P2)
        self.prev_msg = ""
        self.ai0 = None
        self.ai1 = None
        self.ai2 = None
        self.beam_inhibit = 0 # inhibit all beam signals either by setting or due to power wiring failure
        self.pause = 0

        self.beam_fault_inner = 0
        self.beam_fail_inner = 0
        self.beam_fail_center = 0
        
        self.beam_fault_outer = 0
        self.beam_fail_outer = 0
        self.beam_fail_center = 0

        self.beam_inner_trip = 0
        self.beam_outer_trip = 0
        self.beam_center_trip = 0
        
        self.re_center_outward = 0
        self.re_center_inward = 0

        self.adj_pos = 0
        self.adj_pos

        self.beam_current = 0 # current drawn through beam sensor power
        self.beam_current_array = []
        self.beam_current_avg = 16

    def read_ai(self):
        try:
            ai0 = self.ch0.voltage # outer
            #print("ai0 : %s"%format(ai0,'.3f'))
            ai1 = self.ch1.voltage # inner
            #print("ai1 : %s"%format(ai1,'.3f'))
            ai2 = self.ch2.voltage # center
            #print("ai2 : %s"%format(ai2,'.3f'))
            #self.cprint("ai0 : %s  ai1 : %s  ai2 : %s"%(format(ai0,'.3f'),format(ai1,'.3f'),format(ai2,'.3f')))
        except:
            self.cprint("Not able to read analog input")
            return("error")
        else:
            # outer
            if ai0 < 1:
                self.ai0 = 0 # not broken ??
            elif ai0 > 2:
                self.ai0 = 3 # bad signal ??
            else: 
                self.ai0 = 1 # broken ??

            # inner
            if ai1 < 1:
                self.ai1 = 0 # not broken ??
            elif ai1 > 2:
                self.ai1 = 3 # bad signal ??
            else: 
                self.ai1 = 1 # broken ??

            # center
            if ai2 < 1:
                if self.ai2 == 1 and self.re_center_inward == 0 and self.re_center_outward == 0: # switched from not broken to broken - adjuster centered
                    self.mq(self.q42,{'adj_pos':'centered'})
                self.ai2 = 0 # not broken ??
            elif ai2 > 2:
                self.ai2 = 3 # bad signal ??
            else:
                if self.ai2 == 0 and self.re_center_outward == 0 and self.re_center_inward == 0: # switched from broken to not broken - adjuster centered
                    self.mq(self.q42,{'adj_pos':'centered'})
                self.ai2 = 1 # broken ??
                                
            Dict = {'dest':'ai_readings','ai0':self.ai0,'ai1':self.ai1,'ai2':self.ai2}
            #print(Dict)
            return Dict

    def check_beam_sensors(self):

        ''' current drawn through sensor power circuit-----------------------------------'''
        self.beam_current_array.append(ina260.current)
        if len(self.beam_current_array) > 20:
            self.beam_current_array.pop(0)
            self.beam_current_avg = sum(self.beam_current_array) / len(self.beam_current_array)
            #self.cprint("self.beam_current_avg : %s"%self.beam_current_avg)
            if self.beam_current_avg < 20:
                self.set_beam_inhibit(1)
                self.cprint("Open in power wiring to adjuster beam sensors - beam signals inhibited",1,1)
            elif self.beam_current_avg > 30:
                self.set_beam_inhibit(1)
                self.cprint("Short in power wiring to adjuster beam sensors - beam signals inhibited",1,1)

        
        '''outer beam --------------------------------------------------------------------'''
        # outer beam fail
        if (self.ai0 != 0 and self.ai0 != 1):
            if self.beam_fail_outer < self.beam_fail_max:
                #self.cprint("beam_fail_outer : %s"%self.beam_fail_outer)
                self.beam_fail_outer += 1
        else:
            self.beam_fail_outer = 0
        
        # outer beam actions
        if self.beam_inhibit == 0:
            #self.cprint("beam_fail_outer : %s"%self.beam_fail_outer)
            #self.cprint("self.beam_fail_max : %s"%self.beam_fail_max)
            if self.beam_fail_outer >= self.beam_fail_max:
                self.beam_fail_outer = self.beam_fail_max
                self.cprint("Invalid signal from adjuster outer beam sensor(ai0) - beam signals inhibited",1,1)
                self.set_beam_inhibit(1)
            if self.re_center_inward == 0:
                # secondary trip
                if self.beam_outer_trip >= 1 and self.beam_outer_trip < self.beam_trip_max:
                    if self.ai0 == 1:
                        if self.adj_pos < self.outer_trip_adj_pos: # adjuster moved outward
                            self.outer_trip_adj_pos = self.adj_pos
                            self.beam_outer_trip += 1
                            self.send_web_message("Beam sensor outer trip #%s"%self.beam_outer_trip)
                    elif self.ai0 == 0:
                        self.cprint("outward beam trip reset")
                        self.beam_outer_trip = 0
                        self.send_web_message("Beam sensor outer trip reset")
                # initial trip
                if self.ai0 == 1 and self.beam_outer_trip == 0:
                        self.outer_trip_adj_pos = self.adj_pos
                        self.beam_outer_trip = 1
                        self.send_web_message("Beam sensor outer trip #%s"%self.beam_outer_trip)                        
                # re-center action
                if self.re_center_inward == 0:
                    if self.beam_outer_trip == self.beam_trip_max:
                        self.beam_outer_trip += 1 # only perform action once
                        self.re_center_inward = 1
                        self.re_center_outward = 0                        
                        Dict = {'purpose':'re_center','direction':'in'}
                        self.mq(self.q39,Dict)

        '''inner beam --------------------------------------------------------------------        '''
        # inner beam fail
        if (self.ai1 != 0 and self.ai1 != 1):
            if self.beam_fail_inner < self.beam_fail_max:
                self.beam_fail_inner += 1
        else:
            self.beam_fail_inner = 0

        # inner beam actions
        if self.beam_inhibit == 0:
            if self.beam_fail_inner >= self.beam_fail_max:
                self.beam_fail_inner = self.beam_fail_max
                self.send_web_message("Invalid signal from adjuster inner beam sensor(ai1) - beam signals inhibited")
                self.set_beam_inhibit(1)
            if self.re_center_outward == 0:
                # secondary trip
                if self.beam_inner_trip >= 1 and self.beam_inner_trip < self.beam_trip_max:
                    if self.ai1 == 0:
                        if self.adj_pos > self.inner_trip_adj_pos: # adjuster moved inward
                            self.inner_trip_adj_pos = self.adj_pos
                            self.beam_inner_trip += 1
                            self.send_web_message("Beam sensor inner trip #%s"%self.beam_inner_trip)
                    elif self.ai1 == 1:
                        self.cprint("inward beam trip reset")
                        self.beam_inner_trip = 0
                        self.send_web_message("Beam sensor inner trip reset")
                # initial trip
                if self.ai1 == 0 and self.beam_inner_trip == 0:
                        self.inner_trip_adj_pos = self.adj_pos
                        self.beam_inner_trip = 1
                        self.send_web_message("Beam sensor inner trip #%s"%self.beam_inner_trip)                        
                # re-center action
                if self.re_center_outward == 0:
                    if self.beam_inner_trip == self.beam_trip_max:
                        self.beam_inner_trip += 1 # only perform action once
                        self.re_center_outward = 1
                        self.re_center_inward = 0                        
                        Dict = {'purpose':'re_center','direction':'out'}
                        self.mq(self.q39,Dict)

        '''center beam --------------------------------------------------------------------        '''
        # center beam fail
        if (self.ai2 != 0 and self.ai2 != 1):
            if self.beam_fail_center < self.beam_fail_max:
                self.beam_fail_center += 1
        else:
            self.beam_fail_center = 0

        # center beam actions
        if self.beam_inhibit == 0:
            #self.cprint("self.re_center_outward : %s  self.re_center_inward : %s  self.ai2 %s"%(self.re_center_outward,self.re_center_inward,self.ai2)) 
            # center beam fail
            if self.beam_fail_center >= self.beam_fail_max:
                self.beam_fail_center = self.beam_fail_max
                self.send_web_message("Invalid signal from adjuster center beam sensor(ai2) - beam signals inhibited")
                self.set_beam_inhibit(1)
            # secondary trip
            if (self.re_center_outward == 1 and self.ai2 == 1) or \
               (self.re_center_inward == 1 and self.ai2 == 0):            
                if self.beam_center_trip >= 1 and self.beam_center_trip < self.beam_trip_max:
                    if self.adj_pos != self.center_trip_adj_pos: # adjuster moved
                        self.center_trip_adj_pos = self.adj_pos
                        self.beam_center_trip += 1
                        self.cprint("Beam sensor center trip #%s"%self.beam_center_trip,1,1)
            # initial trip
            if (self.re_center_outward == 1 and self.ai2 == 1) or \
               (self.re_center_inward == 1 and self.ai2 == 0):
                if self.beam_center_trip == 0:
                    self.center_trip_adj_pos = self.adj_pos
                    self.beam_center_trip = 1
                    self.cprint("Beam sensor center trip #%s"%self.beam_center_trip,1,1)
            # stop adjuster when centered
            if self.beam_center_trip == self.beam_trip_max and \
                (self.re_center_outward == 1 or self.re_center_inward == 1):
                self.beam_center_trip += 1 # prevent from sending again
                Dict = {'purpose':'re-center','direction':'centered'}
                self.mq(self.q39,Dict)
                    
    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (analog_in%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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
            data = self.read_ai()
            if data != "error":
                if time.time() - self.web_post_st > self.beam_post_to_web_interval:
                    self.web_post_st = time.time()
                    data = {'dest':'beam_stat','outer':self.ai0,'inner':self.ai1,'center':self.ai2}
                    # print(data)
                    self.mq(self.qw26, data)
        except:
            self.cprint("exception in analog_in.py")
            
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
                if index == 205 and val == 0 and self.beam_inhibit == 1: # restore beam signal monitoring
                    self.send_web_message("beam sensor signal monitoring re-activated")
                    self.beam_current_avg = 16
                    self.beam_inhibit = 0
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
            
        if self.beam_inhibit == 1 and self.pause == 0:
            self.pause = 1
            val = 2
            data = {'dest':'beam_stat','outer':val,'inner':val}
            self.mq(self.qw26, data)
        if self.beam_inhibit == 0 and self.pause == 1:
            self.pause = 0
        
    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py

    def send_web_message(self, var):
        if var != self.web_prev_msg:
            Dict = {'dest':'web_message', 'val':var}
            self.qw35.put(Dict)
            self.web_prev_msg = var

    def set_beam_inhibit(self,var):
        if var == 1:
            self.mq(self.q28,{'purpose':'stop_pid'})
            self.mod_kpv_entry(205,1)
        else:
            self.mod_kpv_entry(205,0)

    def mod_kpv_entry(self, index, val):
        self.Kpv[index] = val # update local process kpv entry
        Dict = {'row':index,'val':val}
        self.mq(self.q25, Dict) # send new values to cntrl.py
                                
    def run(self):
        #self.cprint("analog_in.py running")
        while self.qa1.empty():
            time.sleep(1)
        obj = self.qa1.get()
        self.Kpv = obj[0]
        self.KpvTypes = obj[1]
        while len(self.Kpv) == 0:
            None      
        self.init_kpv_to_val('init') 
        #self.cprint("analog_in.py kpv imported successfully")           
        while True:
            #print("self.beam_inhibit : ",self.beam_inhibit)
            if time.time() - self.st > self.read_interval and self.beam_inhibit == 0:
                self.st = time.time()
                self.get_data()
                self.check_beam_sensors()
            if not self.qa1.empty(): # get updated kpv from cntrl.py
                obj = self.qa1.get()
                index = obj[0]
                val = obj[1]
                self.init_kpv_to_val(index,val) # set local process kpv values
            if not self.qa2.empty(): # send adjuster position to analog_in.py
                data = self.qa2.get()
                self.adj_pos = float(data['position'])
                self.adjuster_direction = int(data['direction'])
            if not self.qa3.empty(): # re-center complete from cntrl.py
                data = self.qa3.get()
                self.re_center_outward = 0
                self.re_center_inward = 0
                self.beam_center_trip = 0
                self.beam_inner_trip = 0
                self.beam_outer_trip = 0
            if not self.qa4.empty(): # re-center command from cntrl to analog in
                data = self.qa4.get()
                if self.adj_pos > 0:
                    self.re_center_outward = 1
                    Dict = {'purpose':'re_center','direction':'out'}
                    self.mq(self.q39,Dict)
                else:
                    self.re_center_inward = 1
                    Dict = {'purpose':'re_center','direction':'in'}
                    self.mq(self.q39,Dict)
                
            time.sleep(0.05)

