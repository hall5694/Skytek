    # imports
import tornado.httpserver, tornado.ioloop, tornado.web, tornado.websocket, tornado.gen, \
        os, time, multiprocessing, hardware, meter, program, json, web, inspect,subprocess, \
        math, torndb, MySQLdb, keyring, activity, configobj, subprocess, sys, urllib, mysql, \
        logging, logging.config, logging.handlers
from tornado.options import define, options
from random import random,seed
from urllib import parse

#subprocess.run(['./test.sh'])

# py programs
from program import cntrl 
from meter import meter_tcp_rw, meter_tcp_dpsptp, meter_serial
from hardware import baro_data, serialworker, motor_current, analog_in, usb485
from settings import settings
from activity import activity
from mysqlpy import mysql
        
define("port1", default=10120, help="run on the given port", type=int)

clients = []

skytek_user = ''
skytek_active_user = ''
default_att_left = 5
default_lockout_sec = 300

# database connection
db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')
    
# web queue 
qw1 = multiprocessing.Queue(1) # ma readings from motor_current.py  
qw2 = multiprocessing.Queue(1) # baro readings from baro_data.py        
qw3 = multiprocessing.Queue(1) # inlet_display
qw4 = multiprocessing.Queue(1) # temp readings from USB485.py     
qw5 = multiprocessing.Queue(1) # inch and psi readings
qw6 = multiprocessing.Queue(1) # meter tcp status to controls page
qw7 = multiprocessing.Queue(1) # kpv for settings.py (settings web) and main web
qw8 = multiprocessing.Queue(1) # pid values for web 
qw9 = multiprocessing.Queue(1) # send markers
qw10 = multiprocessing.Queue(1) # ping web
qw11 = multiprocessing.Queue(1) # send_web_message for usb485.py
qw12 = multiprocessing.Queue(1) # save_msg_log
qw13 = multiprocessing.Queue(1) # eq_status
qw14 = multiprocessing.Queue(1) # outlet_display
qw15 = multiprocessing.Queue(1) # adj_pos_display
qw16 = multiprocessing.Queue(1) # stpt_display
qw17 = multiprocessing.Queue(1) # psi_stpt_display
qw18 = multiprocessing.Queue(1) # send_cal_low
qw19 = multiprocessing.Queue(1) # send_cal_high
qw20 = multiprocessing.Queue(1) # send_cal_mid
qw21 = multiprocessing.Queue(1) # send_web_message for cntrl.py
qw22 = multiprocessing.Queue(1) # send_web_message for motor_current.py
qw23 = multiprocessing.Queue(1) # send_web_message for serialworker.py
qw24 = multiprocessing.Queue(10) # btn_status
qw25 = multiprocessing.Queue(1) # pid_running_status
qw26 = multiprocessing.Queue(1) # beam indicators
qw27 = multiprocessing.Queue(1) # disable clear crystal alarm button
qw28 = multiprocessing.Queue(1) # ROC button
qw29 = multiprocessing.Queue(1) # meter tcp dpsptp to web
qw30 = multiprocessing.Queue(1) # send_web_message for meter_serial.py
qw31 = multiprocessing.Queue(1) # send_web_message for meter_tcp_rw.py
qw32 = multiprocessing.Queue(1) # send_web_message for ssh.py
qw33 = multiprocessing.Queue(1) # sounds
qw34 = multiprocessing.Queue(1) # next/prev button enable/disable
qw35 = multiprocessing.Queue(1) # send_web_message for analog_in.py
qw36 = multiprocessing.Queue(1) # send_web_message for meter_tcp_dpsptp.py
qw37 = multiprocessing.Queue(1) # status indicator
qw38 = multiprocessing.Queue(1) # NA
qw39 = multiprocessing.Queue(1) # NA
qw40 = multiprocessing.Queue(1) # NA
qw41 = multiprocessing.Queue(1) # NA
qw42 = multiprocessing.Queue(1) # NA
qw43 = multiprocessing.Queue(1) # NA
qw44 = multiprocessing.Queue(1) # NA

# web graph queue
qwg1 = multiprocessing.Queue(1) # queue web graph adjuster
    
# motor_current.py queue
qm1 = multiprocessing.Queue(1) # motor_current.py motor direction    
qm2 = multiprocessing.Queue(1) # motor_current.py adjuster position
qm3 = multiprocessing.Queue(1) # motor_current.py re-center active
qm4 = multiprocessing.Queue(5) # constant ma alarm checking
qm5 = multiprocessing.Queue(1) # NA
qm6 = multiprocessing.Queue(1) # NA
qm7 = multiprocessing.Queue(1) # NA

# cntrl.py queue
q1 = multiprocessing.Queue(1) # web save_inch_center_position
q2 = multiprocessing.Queue(1)  # web close_inlet
q3 = multiprocessing.Queue(1) # web close_outlet
q4 = multiprocessing.Queue(1) # web initialize inlet
q5 = multiprocessing.Queue(1) # cntrl.py init_outlet
q6 = multiprocessing.Queue(1) # web re_center and motor current inst ma max
q7 = multiprocessing.Queue(1) # web inlet control
q8 = multiprocessing.Queue(1) # web outlet control
q9 = multiprocessing.Queue(1) # web eq control
q10 = multiprocessing.Queue(1) # web web_running
q11 = multiprocessing.Queue(1) # web vent control
q12 = multiprocessing.Queue(1) # serial_worker open the equalizer for high dp
q13 = multiprocessing.Queue(1) # serial_worker vent_alarm
q14 = multiprocessing.Queue(1) # serial_worker in_vent_alarm
q15 = multiprocessing.Queue(1) # web full auto checks
q16 = multiprocessing.Queue(1) # full auto checks
q17 = multiprocessing.Queue(1) # web in_full_auto_cal
q18 = multiprocessing.Queue(4) # web skip point
q19 = multiprocessing.Queue(4) # web low control
q20 = multiprocessing.Queue(1) # temp readings for cntrl.py
q21 = multiprocessing.Queue(1) # serial_worker stop_pid
q22 = multiprocessing.Queue(1) # check meter tcp connection request from web
q23 = multiprocessing.Queue(1) # web psi_pid_start_stop
q24 = multiprocessing.Queue(1) # web manual_control
q25 = multiprocessing.Queue(1) # send kpv from py processes to cntrl.py
q26 = multiprocessing.Queue(1) # rest motors
q27 = multiprocessing.Queue(1) # start button
q28 = multiprocessing.Queue(1) # stop button
q29 = multiprocessing.Queue(1) # pause button
q30 = multiprocessing.Queue(1) # zero inlet
q31 = multiprocessing.Queue(1) # zero outlet
q32 = multiprocessing.Queue(1) # heartbeat
q33 = multiprocessing.Queue(1) # restart program
q34 = multiprocessing.Queue(1) # ROC button
q35 = multiprocessing.Queue(1) # meter read register button
q36 = multiprocessing.Queue(1) # web command to send a marker
q37 = multiprocessing.Queue(1) # full test (SPDPTP auto)
q38 = multiprocessing.Queue(1) # returned data from meter_read_reg
q39 = multiprocessing.Queue(1) # re-center command from analog_in.py
q40 = multiprocessing.Queue(1) # returned meter_write_reg status code
q41 = multiprocessing.Queue(1) # baro lock button
q42 = multiprocessing.Queue(1) # zero adjuster position based on center beam sensor

# serialworker.py queue
qs1 = multiprocessing.Queue(1) # cntrl.py eq_status
qs2 = multiprocessing.Queue(1) # cntrl.py vent_status
qs3 = multiprocessing.Queue(1) # cntrl.py   in_vent_status
qs4 = multiprocessing.Queue(1) # serial worker dp_high_alarm_display
qs5 = multiprocessing.Queue(1) # serial worker sp_high_alarm_display
qs6 = multiprocessing.Queue(1) # serial worker write to crystal
qs7 = multiprocessing.Queue(1) # dpsp readings for cntrl.py
qs8 = multiprocessing.Queue(1) # cntrl.py low_status
qs9 = multiprocessing.Queue(1) # send auto_pid mode to serialworker
qs10 = multiprocessing.Queue(1) # send kpv file to serialworker.py
qs11 = multiprocessing.Queue(1) # serial worker dp high during SP testing
qs12 = multiprocessing.Queue(1) # restart crystal communication attempts

# baro_data.py queue
qb1 =  multiprocessing.Queue(1) # baro set status for baro_data.py
qb2 = multiprocessing.Queue(1) # baro psi for cntrl.py
qb3 = multiprocessing.Queue(1) # send kpv file to baro_data.py

# meter_tcp.py queue
qt1 = multiprocessing.Queue(1) # Modify ip address in meter_tcp.py
qt2 = multiprocessing.Queue(1) # write register to meter tcp
qt3 = multiprocessing.Queue(1) # read register from meter tcp
qt4 = multiprocessing.Queue(1) # send kpv file to meter_tcp.py
qt6 = multiprocessing.Queue(1) # meter tcp connection status for cntrl.py

# meter_tcp_dpsptp.py queue
qtd1 = multiprocessing.Queue(1) # Modify ip address in meter_tcp_dpsptp.py
qtd4 = multiprocessing.Queue(1) # send kpv file to meter_tcp_dpsptp.py
qtd5 = multiprocessing.Queue(1) # meter dpspdp to cntrl.py
qtd6 = multiprocessing.Queue(1) # meter tcp connection status for cntrl.py

# meter_serial.py queue
qts1 = multiprocessing.Queue(1) # send kpv file to meter_serial.py
qts2 = multiprocessing.Queue(1) # 
qts3 = multiprocessing.Queue(1) # 
qts4 = multiprocessing.Queue(1) # write data to Totalflow rs232 

# settings.py queue
qk1 = multiprocessing.Queue(1) # settings.py request to cntrl.py for kpv
qk2 = multiprocessing.Queue(1) # send kpv to settings.py
qk3 = multiprocessing.Queue(1) # settings change from settings web page
qk4 = multiprocessing.Queue(1) # change made to kpv - update web

# analog_in.py queue
qa1 = multiprocessing.Queue(1) # send kpv to analog_in.py
qa2 = multiprocessing.Queue(1) # send adjuster position to analog_in.py
qa3 = multiprocessing.Queue(1) # re-center complete from cntrl.py
qa4 = multiprocessing.Queue(1) # re-center command from cntrl to analog in

# USB485.py queue
qu1 =  multiprocessing.Queue(1) # temp set status for baro_data.py
qu2 = multiprocessing.Queue(1) # NA
qu3 = multiprocessing.Queue(1) # send kpv file to USB485.py

# activity.py queue
qv1 = multiprocessing.Queue(1) # activity detected
qv2 = multiprocessing.Queue(1) # max inactivity reached
qv3 = multiprocessing.Queue(1) # kpv for activity.py
qv4 = multiprocessing.Queue(1) # inactivity time

# mysql.db queue
qd1 = multiprocessing.Queue(1) # write marker to db
qd2 = multiprocessing.Queue(1) # read marker from db

def cprint(msg = "",printout = True, web = False, lvl = 'i'):
    if printout or lvl == None:
        print("%s  (srvr%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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

def message_clients(message,webs = 'all'):
    if webs == 'all':
        for c in clients:
            c.write_message(message)
    else:
        for c in clients:
            if c.desc == webs:
                #print("websocket found : %s"%webs)
                c.write_message(message)
                break

class BaseHandler(tornado.web.RequestHandler):      
    def get_current_user(self):
        return self.get_secure_cookie('skytek_user',max_age_days=1)

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('web/settings/settings.html')

class LoginHandler(BaseHandler):
    def get(self):
        self.render('web/login/login.html')

    def post(self):
        purpose = self.get_argument('purpose')
        if purpose == 'reset_lockout':
            user = self.get_argument('user')
            db.execute("update user_credentials set att_left = " + default_att_left + "where user = '" + user + "'");
            db.execute("update user_credentials set lockout_time = " + default_lockout_sec + "where user = '" + user + "'");            
        if purpose == 'check_user_set':
            user_set = check_user_set()
            message_clients({'dest':'check_user_set','data':str(user_set)})
        elif purpose == 'check_cred': # check for valid credentials
            valid_cred = 0
            att_left = default_att_left
            lockout_time = 0
            user = self.get_argument('user')
            password = self.get_argument('password')
            for row in db.query("select * from user_credentials"):
                if row.user == user and user != 'skytek':
                    att_left = int(row.att_left)
                    lockout_time = int(row.lockout_time)
                    if lockout_time != 0:
                        if (time.time() - lockout_time > default_lockout_sec):
                            att_left = default_att_left
                            lockout_time = 0
                            db.execute("update user_credentials set lockout_time = %s where user = '%s'"%(0,user));
                            db.execute("update user_credentials set att_left = %s where user = '%s'"%(default_att_left,user));
                        else:
                            valid_cred = 3 # user is attempting login before lockout expiration
                    if row.password == password and lockout_time == 0:
                        valid_cred = 2
                        db.execute("update user_credentials set att_left = %s where user = '%s'"%(default_att_left,user));
                        db.execute("update user_credentials set lockout_time = %s where user = '%s'"%(0,user));
                        try:
                            self.clear_cookie('skytek_user')
                        except:
                            None
                        self.set_secure_cookie('skytek_user',gen_key(),expires_days=None) # expires_days = None - delete cookie after browser session              
                        
                    elif lockout_time == 0:
                        if att_left > 1:
                            att_left -= 1
                            valid_cred = 1
                            db.execute("update user_credentials set att_left = %s where user = '%s'"%(att_left,user));
                        else:
                            # maximum failed attempts for user
                            att_left = 0
                            valid_cred = 3
                            db.execute("update user_credentials set att_left = %s where user = '%s'"%(att_left,user));
                            db.execute("update user_credentials set lockout_time = %s where user = '%s'"%(time.time(),user));
                    break # user found
            message_clients({'dest':'check_cred','user':user,'valid_cred':str(valid_cred),'att_left':str(att_left), \
                           'lockout_time':str(lockout_time)},'login')
        elif purpose == 'new_user':
            user = self.get_argument('user')
            password = self.get_argument('password')
            db.execute("delete from user_credentials where user='skytek'")
            db.execute("insert into user_credentials (user,password) values('%s','%s')"%(str(user),str(password)));
            db.execute("update user_credentials set root_user = 0");
            db.execute("update user_credentials set root_user = 1 where user = '%s'"%user);
        elif purpose =='login':
            c_user = self.get_argument('user')
            self.set_cookie('skytek_active_user',c_user,expires_days=None) # expires_days = None - delete cookie after browser session
            db.execute("update user_credentials set active_user = 1 where user = '%s'"%c_user);
                        
class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('skytek_user')
        self.clear_cookie('skytek_active_user')
        skytek_active_user = ''
        logout_user = self.get_argument('user')
        db.execute("update user_credentials set active_user = 0 where user = '%s'"%logout_user)
        
class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('web/settings/settings.html')

    def post(self):
        purpose = self.get_argument('purpose')

        if purpose == 'get_user_list':
            user_list = []
            for row in db.query("select * from user_credentials"):
                user_list.append(row.user)
            message_clients({'dest':'get_user_list','all_users':user_list})
            
        elif purpose == 'check_user_privilege_level':
            root = 0
            user = self.get_argument('user')
            for row in db.query("select * from user_credentials"):
                if row.user == user:
                    if int(row.root_user) == 1:
                        root = 1
                    break
            message = {'dest':'user_privilege_level','user':str(user),'root_user':str(root)}
            message_clients(message,'settings')
            
        elif purpose == 'new_user':
            user = self.get_argument('user')
            password = self.get_argument('password')
            duplicate = 0
            for row in db.query("select * from user_credentials"):
                if row.user == user:
                    duplicate = 1
                    break
            if duplicate == 0:
                db.execute("insert into user_credentials (user,password) values('%s','%s')"%(str(user),str(password)));
                message_clients({'dest':'add_user','success':1})
                message_clients({'dest':'message','message':'User (%s) added'%user})
            else:
                message_clients({'dest':'add_user','success':0})
                message_clients({'dest':'message','message':'User already exists'})

        elif purpose == 'user_removal':
            user = self.get_argument('user')
            root = 0
            found = 0
            for row in db.query("select * from user_credentials"):
                if row.user == user:
                    found = 1
                    cprint(row.root_user)
                    if int(row.root_user) == 1:
                        root = 1
            message_clients({'dest':'user_removal','user':str(user),'found':str(found),'root':str(root)})
            
        elif purpose == 'remove_user':
            user = self.get_argument('user')
            db.execute("delete from user_credentials where user = '" + user + "'")
            message_clients({'dest':'message','message':"User (" + user + ") removed"})
            message_clients({'dest':'user_removed','user':user})

        elif purpose == 'change_root_check':
            user = self.get_argument('user')
            root = 0
            found = 0
            for row in db.query("select * from user_credentials"):
                if row.user == user:
                    found = 1
            message_clients({'dest':'change_root','user':str(user),'found':str(found)})

        elif purpose == 'change_root':
            user = self.get_argument('user')
            db.execute("update user_credentials set root_user = 0")
            db.execute("update user_credentials set root_user = 1 where user =  '" + user + "'")
            message_clients({'dest':'message','message':"New root user (" + user + ")"})
            message_clients({'dest':'root_changed','user':user})                        

        elif purpose == 'logout':
            self.clear_cookie('skytek_user')
            self.clear_cookie('skytek_active_user')
            skytek_active_user = ''
            logout_user = self.get_argument('user')
            db.execute("update user_credentials set active_user = 0 where user = '%s'"%logout_user)
            message_clients({'dest':'user_logged_out','user':logout_user})

        elif purpose == 'logout_window_close':
            print("len(clients) : %s"%len(clients))
            if (len(clients) == 1):
                self.clear_cookie('skytek_user')
                self.clear_cookie('skytek_active_user')
                skytek_active_user = ''
                logout_user = self.get_argument('user')
                db.execute("update user_credentials set active_user = 0 where user = '%s'"%logout_user)
                message_clients({'dest':'user_logged_out','user':'logout_user'})            

        elif purpose == 'get_network_settings':
            msg = 'unable to retrieve network settings'
            ENCODING='utf-8'
            try:
                conf = configobj.ConfigObj('/etc/hostapd/hostapd.conf',
                       raise_errors=True,
                       file_error=True,
                       encoding=ENCODING,
                       default_encoding=ENCODING)
                wifi_name = conf['ssid']
                wifi_password = conf['wpa_passphrase']
            except:
                self.cprint('unable to retrieve network settings')
            else:
                msg = ''
            message_clients({'dest':'get_network_settings','msg':msg,'wifi_name':wifi_name,'wifi_password':wifi_password},'settings')
            
        elif purpose == 'network_settings_check':
            wn = self.get_argument('wifi_name')
            wn_msg = ''
            wp = self.get_argument('wifi_password')
            wp_msg = ''
            change_made = False
            full_msg = 'error modifying network settings'
            success = 0
            ENCODING='utf-8'
            try:
                conf = configobj.ConfigObj('/etc/hostapd/hostapd.conf',
                       raise_errors=True,
                       file_error=True,           # don't create file if it doesn't exist
                       encoding=ENCODING,         # used to read/write file
                       default_encoding=ENCODING) # str -> unicode internally (useful on Python2.x)
            except:
                self.cprint('error modifying network settings')
            else:
                try:
                    cwn = conf['ssid']
                    conf.update(dict(ssid=wn))
                    nwn = conf['ssid']
                    
                    cwp = conf['wpa_passphrase']
                    conf.update(dict(wpa_passphrase=wp))
                    nwp = conf['wpa_passphrase']
                    
                    conf.write()
                except:
                    self.cprint('error modifying network settings')    
                else:
                    success = 1
                    if nwn != cwn:
                        change_made = True
                        wn_msg = ' wifi name (%s --> %s)'%(cwn,nwn)

                    if nwp != cwp:
                        change_made = True
                        wp_msg = 'wifi password (%s --> %s)'%(cwp,nwp)
                        
                    if change_made == True:
                        full_msg = wn_msg + wp_msg
                    else:
                        full_msg = 'no changes made to network settings'

            self.cprint(full_msg)
            message_clients({'dest':'network_settings_check','msg':full_msg,'success':success},'settings')
            
class GraphsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('web/graphs/adjgraph.html')

class ControlsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('web/controls/controls.html')                

class CmdsHandler(BaseHandler):
    def get(self,cmd):
        cprint('in CmdsHandler')
        cprint(cmd)
        self.render('cmds' + cmd)
        
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        parsed_origin = urllib.parse.urlparse(origin)
        return True
        #allowed = ["http://site1.tld", "https://site2.tld"]
        #if origin in allowed:
        #    cprint("allowed", origin)
        #    return 1
        
    def open(self,desc1):
        clients.append(self)
        cprint("new websocket opened for page (%s)"%desc1)
        self.desc = desc1 # desc1 comes from web url
        #self.write_message("connected")
        if desc1 != 'skyra':
            self.mq(q10,{'purpose':'web_running', 'data':'0'})
            qb1.put({'purpose':'baro_set', 'data':'0'})
            qu1.put({'purpose':'temp_set', 'data':'0'})  

    def on_message(self, message):
        #cprint('tornado received from client: %s' % json.dumps(message))
        #self.write_message('ack')
        #print("message from websocket (%s)"%self.desc)
        var = (json.loads(message)) #convert JSON string from main.js
        #print(var)

        # cntrl.py queue
        if var["dest"] == "q1": # web save_inch_center_position
            self.mq(q1,{'purpose':var["purpose"], 'data':var["data"]})
        if var["dest"] == "q2": # NA
            self.mq(q2,{'purpose':var["purpose"], 'data':var["data"]})            
        if var["dest"] == "q3": # NA
            self.mq(q3,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q4": # web initialize inlet
            self.mq(q4,{'purpose':var["purpose"], 'data':var["data"]})                                    
        if var["dest"] == "q5":
            self.mq(q5,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q6": # web re_center and motor current inst ma max
            self.mq(q6,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q7": # web inlet control
            self.mq(q7,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q8": # web outlet control
            self.mq(q8,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q9": # web eq control
            self.mq(q9,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q10": # web web_running
            self.mq(q10,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q11": # web vent control
            #cprint(var)
            self.mq(q11,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q12": # serial_worker open the equalizer for high dp
            self.mq(q12,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q13": # serial_worker vent_alarm
            self.mq(q13,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q14": # serial_worker in_vent_alarm
            self.mq(q14,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q15": # web full auto checks
            self.mq(q15,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q16": # full auto checks
            self.mq(q16,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q17": # web in_full_auto_cal
            s8lf.mq(q17,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q18": # web next point
            self.mq(q18,{'purpose':var["purpose"], 'data':var["data"]})
        if var["dest"] == "q19": # web low control
            self.mq(q19,{'purpose':var["purpose"], 'data':var["data"]})
        if var["dest"] == "q20": # temp readings for cntrl.py
            self.mq(q20,{'purpose':var["purpose"], 'data':var["data"]})                        
        if var["dest"] == "q21": # serial_worker stop_pid
            self.mq(q21,{'purpose':var["purpose"], 'data':var["data"]})                           
        if var["dest"] == "q22": # check meter tcp connection request from web
            self.mq(q22,{'purpose':var["purpose"], 'data':var["data"]})    
        if var["dest"] == "q23": # web psi_pid_start_stop
            self.mq(q23,{'purpose':var["purpose"], 'data':var["data"]})     
        if var["dest"] == "q24": # web manual_control
            self.mq(q24,{'purpose':var["purpose"], 'data':var["data"]})   
        if var["dest"] == "q26": # rest motors
            self.mq(q26,{'purpose':var["purpose"], 'data':var["data"]})   
        if var["dest"] == "q27": # start btn
            self.mq(q27,{'purpose':var["purpose"], 'data':var["data"]})               
        if var["dest"] == "q28": # stop btn
            self.mq(q28,{'purpose':var["purpose"], 'data':var["data"]})   
        if var["dest"] == "q29": # pause button
            self.mq(q29,{'purpose':var["purpose"], 'data':var["data"]})   
        if var["dest"] == "q30": # zero inlet
            self.mq(q30,{'purpose':var["purpose"], 'data':var["data"]})   
        if var["dest"] == "q31": # zero outlet
            self.mq(q31,{'purpose':var["purpose"], 'data':var["data"]})                           
        if var["dest"] == "q32": # heartbeat
            self.mq(q32,{'purpose':var["purpose"], 'data':var["data"]})                                       
        if var["dest"] == "q34": # ROC button
            self.mq(q34,{'purpose':var["purpose"], 'data':var["data"]})                                                   
        if var["dest"] == "q35": # meter read register button
            #cprint(var)
            self.mq(q35,{'purpose':var["purpose"], 'data':var["data"]})                                                               
        if var["dest"] == "q36": # web command to send a marker
            #cprint(var)
            self.mq(q36,{'purpose':var["purpose"], 'data':var["marker"]})
        if var["dest"] == "q37": # full test (SPDPTP auto)
            #cprint(var)
            self.mq(q37,{'purpose':var["purpose"], 'data':var["data"]})
        if var["dest"] == "q41": # baro lock button
            #cprint(var)
            self.mq(q41,{'purpose':var["purpose"], 'data':var["data"]})            
            
        # serialworker.py queue
        if var["dest"] == "qs4": # serial worker dp_high_alarm_display
            self.mq(qs4,{'purpose':var["purpose"], 'data':var["data"]})                 
        if var["dest"] == "qs5": # serial worker sp_high_alarm_display
            self.mq(qs5,{'purpose':var["purpose"], 'data':var["data"]})                 
        if var["dest"] == "qs6": # serial worker write to crystal
            self.mq(qs6,{'purpose':var["purpose"], 'data':var["data"]})
        if var["dest"] == "qs12": # restart crystal communication attempts
            self.mq(qs12,{'purpose':var["purpose"], 'data':var["data"]})
                               
        # motor_current.py queue
        if var["dest"] == "qm1": # motor_current.py motor direction           
            self.mq(qm1,{'purpose':var["purpose"], 'data':var["data"]})
        if var["dest"] == "qm2": # motor_current.py adjuster position
            self.mq(qm2,{'purpose':var["purpose"], 'data':var["data"]})                                     

        if var["dest"] == "qtd6": # meter tcp connection
            #cprint(var)
            self.mq(qtd6,{'purpose':var["purpose"], 'data':var["data"]})
            
        if var["dest"] == "qw12": # NA
            #cprint(var)
            self.mq(qw12,{'purpose':var["purpose"], 'data':var["data"]})
            
        # meter_tcp_rw.py queue - web modify ip address in meter_tcp_rw.py
        if var["dest"] == "qt1":
            self.mq(qt1, {'purpose':var["purpose"], 'data':var["data"]})
                        
        # meter_tcp_rw.py queue - web write register to meter
        if var["dest"] == "qt2":
            self.mq(qt2, {'purpose':var["purpose"], 'register':var["register"], 'value':var['value'], 'data_type':var['data_type']})
                                        
        # meter_tcp_rw.py queue - web read register from meter
        if var["dest"] == "qt3":
            self.mq(qt3, {'purpose':var["purpose"], 'register':var["register"], 'data_type':var['data_type'],'return_to':var['return_to']})
                
        # settings.py queue
        if var["dest"] == "qk1": # settings.py request to cntrl.py for kpv           
            self.mq(qk1,{'purpose':var["purpose"], 'data':var["data"]})   
        if var["dest"] == "qk3": # settings change from settings web page
            self.mq(qk3,{'purpose':var["purpose"], 'data':var["data"]}) 
        if var["dest"] == "qk4": # change made to kpv - update web
            self.mq(qk4,{'purpose':var["purpose"], 'data':var["data"]})                                          

        # mysql.py queue
        if var["dest"] == "qd1": # write marker to db
            #print(var)            
            self.mq(qd1,{'dtype':var["dtype"],'m_read':var["m_read"],'r_read':var["r_read"]})
            
        if var["dest"] == "server":
            if var["purpose"] == "restart" and var["data"] == "1": # restart button from web
                cprint("Command to restart program sent from web")
                self.mq(q33,{'purpose':var["purpose"], 'data':var["data"]})                                          

        # request from skyra for active user
        if var["dest"] == "get_active_user":
            skytek_active_user = self.get_active_user()
            message_clients({'purpose':'get_active_user','current_user':skytek_active_user,'action':var["action"], \
                             'group':var["group"],'unit':var["unit"],'ip':var["ip"],'port':var["port"]},'skyra')

        # show message on controls.js
        if var["dest"] == "message_box":
            self.mq(qd1,{'dtype':var["dtype"],'m_read':var["m_read"],'r_read':var["r_read"]})        

    def on_close(self):
        cprint('connection closed')
        clients.remove(self)
        
    def mq(self, q, val, block = False, timeout = 0.05): # verify queue transmission
        if block == 1:
            block = True
        try:
            self.q = q
            try:
                while self.q.full():
                    self.q.get(block, timeout)
            except:
                cprint("Problem with mq get")
                #raise
            else:
                try:
                    self.q.put(val, block, timeout)         
                except:
                    cprint("Problem with mq put")
                    #raise
                else:
                    None
        except:
            #raise
            None

    def get_active_user(self):
        au = ''
        for row in db.query('SELECT * FROM `user_credentials`'):
            if int(row.active_user) == 1:
                au = row.user
                break
        return au
        
class ActivityHandler(BaseHandler):
    def get(self):
        if time.time() - self.user_activity_time > self.max_inactivity:
            print("logging out")
            None

    def post(self):
        #print('in activity handler')
        purpose = self.get_argument('purpose')
        if purpose == 'activity':
            self.mq(qv1,{'dest':'activity_detected'})

    def mq(self, q, val, block = False, timeout = 0.05): # verify queue transmission
        if q == q11:
            cprint(val)
        if block == 1:
            block = True
        try:
            self.q = q
            try:
                while self.q.full():
                    self.q.get(block, timeout)
            except:
                self.cprint("Problem with mq get")
                #raise
            else:
                try:
                    self.q.put(val, block, timeout)         
                except:
                    self.cprint("Problem with mq put")
                    #raise
                else:
                    if q == q11:
                        self.cprint("mq 11 successful")
        except:
            None
        
## check the queue for pending messages, and relay that to all connected clients
def checkQueue():
    if not q33.empty(): # restart program
        data  = q33.get()    
        '''
        sp1.close()       
        sp1 = cntrl.Controls(q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, q16, q17, q18,q19, q20, \
                     q21, q22, q23, q24, q25, q26, q27, q28, q29, q30, q31, q32, q33, qm1, qm2, qm3, qm4, qm5, qm6, \
                     qm7, qs1, qs2, qs3, qs7, qs8, qs9, qs10, qs11, qw3, qw4, qw8, qw9, qw10, qw11, qw12, qw13, qw14,\
                     qw15, qw16, qw17, qw18, qw19, qw20, qw21, qw22, qw23, qw24, qw25, qw26, qw27, qw28, qw29, qw30, \
                     qw31, qw32, qw33, qw34, qw35, qw36, qw37, qw38, qw39, qw40, qk1, qk2, qk4, qk3, qt4, qb1, qb3, qa1, qa2)          
        sp1.start()
        '''
                
    if not qw1.empty(): # readings  - # ma readings from motor_current.py
        message = qw1.get()             
        #cprint("qw1 - server : %s"%message)
        message_clients(message,'controls')

            
    if not qw2.empty(): # baro readings from bar_data.py
        message = qw2.get()
        #cprint("qw2 - server : %s"%message)
        message_clients(message,'controls')
            
                        
    if not qw3.empty(): # inlet_display
        message = qw3.get()
        #cprint("qw3 - server : %s"%message)
        message_clients(message,'controls')
            
                                    
    if not qw4.empty(): # temp readings from usb485.py
        message = qw4.get()
        #cprint("qw4 - server : %s"%message)
        message_clients(message,'controls')
          
                                                
    if not qw5.empty(): # inch and psi readings
        message = qw5.get()
        #cprint("qw5 - server : %s"%message)
        message_clients(message,'controls')

            
    if not qw6.empty(): # meter tcp connection to controls page
        message = qw6.get()
        #cprint("qw6 - server : %s"%message)
        message_clients(message,'controls')
  
            
    if not qw7.empty(): # kpv for settings web
        message = qw7.get()
        #cprint("qw7 - server : %s"%message)
        message_clients(message,'controls')
        message_clients(message,'settings')
        message_clients(message,'graphs')
      
            
    if not qw8.empty(): # pid values for web
        message = qw8.get()
        #cprint("qw8 - server : %s"%message)
        message_clients(message,'controls')
             
            
    if not qw9.empty(): # send markers
        message = qw9.get()
        #cprint("qw9 - server : %s"%message)
        message_clients(message,'controls')
 
            
    if not qw10.empty(): # ping web
        message = qw10.get()
        #cprint("qw10 - server : %s"%message)
        message_clients(message,'controls')
                       
            
    if not qw11.empty(): # send_web_message from usb485.py
        message = qw11.get()
        #cprint("qw11 - server : %s"%message)
        message_clients(message,'controls')
                       
            
    if not qw12.empty(): # NA
        message = qw12.get()
        cprint("qw12 - server : %s"%message)
        message_clients(message,'controls')
                       
            
    if not qw13.empty(): # eq_status
        message = qw13.get()
        #cprint("qw13 - server : %s"%message)
        message_clients(message,'controls')
                                                           
            
    if not qw14.empty(): # outlet_display
        message = qw14.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
 
            
    if not qw15.empty(): # adj_pos_display
        message = qw15.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw16.empty(): # stpt_display
        message = qw16.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw17.empty(): # psi_stpt_display
        message = qw17.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw18.empty(): # send_cal_low
        message = qw18.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
                                                
    if not qw19.empty(): # send_cal_high
        message = qw19.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw20.empty(): # send_cal_mid
        message = qw20.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw21.empty(): # send_web_message from cntrl.py
        message = qw21.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw22.empty(): # send_web_message for motor_current.py
        message = qw22.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw23.empty(): # send_web_message for serialworker.py
        message = qw23.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw24.empty(): # btn_status
        message = qw24.get()
        #cprint("qw24 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw25.empty(): # pid_running_status
        message = qw25.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw26.empty(): # beam indicators
        message = qw26.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw27.empty(): # disable clear crystal alarm button
        message = qw27.get()
        #cprint("qw27 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw28.empty(): # ROC button
        message = qw28.get()
        cprint("qw28 - server : %s"%message)
        message_clients(message)
                                                                                   
    if not qw29.empty(): # meter read in and psi
        message = qw29.get()
        #cprint("qw29 - server : %s"%message)
        message_clients(message,'controls')
                                                                                   
            
    if not qw30.empty(): # send_web_message for meter_serial.py
        message = qw30.get()
        cprint("qw14 - server : %s"%message)
        message_clients(message)

                                                                                                                                                                                                             
    if not qw31.empty(): # send_web_message for meter_tcp_rw.py
        message = qw31.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message)
            
    if not qw32.empty(): # send_web_message for ssh.py
        message = qw32.get()
        cprint("qw14 - server : %s"%message)
        message_clients(message)
            
            
    if not qw33.empty(): # sounds
        message = qw33.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw34.empty(): # next/prev button enable/disable
        message = qw34.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw35.empty(): # send_web_message for analog_in.py
        message = qw35.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw36.empty(): # send_web_message for meter_tcp_dpsptp.py
        message = qw36.get()
        #cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw37.empty(): # status indicator
        message = qw37.get()
        #cprint("qw37 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw38.empty(): # NA
        message = qw38.get()
        cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw39.empty(): # NA
        message = qw39.get()
        cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw40.empty(): # NA
        message = qw40.get()
        cprint("qw14 - server : %s"%message)
        message_clients(message)
                        
            
    if not qw32.empty(): # NA
        message = qw32.get()
        cprint("qw14 - server : %s"%message)
        message_clients(message)
                                                                                                                        
            
    if not qwg1.empty(): # pid values for web graphs
        message = qwg1.get()
        #cprint("qwg1 - server : %s"%message)
        message_clients(message,'graphs')
 
    if not qv2.empty(): # max inactivity reached
        message = qv2.get()
        message_clients({'dest':'inactivity_logout'})
        print("user logged out due to inactivity")

    if not qv4.empty(): # inactivity time
        message = qv4.get()
        max_inactive_sec = message['max_inactive_sec']
        inactive_sec = message['inactive_sec']
        msg = {'dest':'inactivity_time','max_inactive_sec':max_inactive_sec,'inactive_sec':inactive_sec}
        message_clients(msg,'controls')
        message_clients(msg,'settings')
        message_clients(msg,'graphs')
        #print('inactivity time : %s sec'%inactive_sec)

    def mq(self, q, val, tmo=3000): # verify queue transmission
        try:
            self.q = q
            if not self.q.empty():
                self.q.get()
            self.q.put(val)
        except:
            cprint("problem modifying queue")

def check_user_set():
    user_set = 0
    duf = 0 # default user found
    nu = 0 # new user found
    au = 0 # active user already logged in
    row_count = 0
    for row in db.query("select * from user_credentials"):
        row_count += 1
        if row.user == 'skytek':
            duf = 1
        else:
            nu = 1
        if int(row.active_user) == 1:
            au = 1
    if row_count < 1:
        db.execute("insert into user_credentials (user,password,root_user) values('skytek','skytek',1)")
    if nu == 1:
        user_set = 1
    if au == 1:
        user_set = 2
    return user_set

def gen_key():
    cs=''
    for i in range(4):
        cs += str(int(random() * 25 + 97)) # lower case letter
        cs += str(int(random() * 500 + 161)) # special character
        cs += str(math.floor(random() * 9)) # positive integer
        cs += str(int(random() * 500 + 161)) # special character
        cs += str(int(random() * 25 + 65)) # uppercase letter
    return cs.encode()
    
if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('server')

    db.execute("update user_credentials set active_user = 0")
    check_user_set() # initial call
    
    # serial worker
    sp = serialworker.SerialProcess( q9, q12, q13, q14, q21, q25, qs1, qs2, qs3, qs4, qs5, qs6, qs7, qs8, \
    qs9, qs10, qs11, qs12, qw3, qw5, qw23, qw24, qw27)
    sp.daemon = True
    sp.start()

    # controls worker
    sp1 = cntrl.Controls(q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, q16, q17, q18,q19, q20, \
                 q21, q23, q24, q25, q26, q27, q28, q29, q30, q31, q32, q33, q34, q36, q37, q38, q39, q40, q41, q42, qm1, qm2, qm3, qm4, qm5, qm6, \
                 qm7, qs1, qs2, qs3, qs6, qs7, qs8, qs9, qs10, qs11, qw3, qw4, qw8, qw9, qw10, qw11, qw12, qw13, qw14,\
                 qw15, qw16, qw17, qw18, qw19, qw20, qw21, qw22, qw23, qw24, qw25, qw26, qw27, qw28, qw30, \
                 qw31, qw32, qw33, qw34, qw35, qw36, qw37, qw38, qw39, qw40, qk1, qk2, qk3, qk4, qt2, qt3, qt4, \
                 qtd4, qtd5, qtd6, qb1, qb3, qa1, qa2, qa3, qa4,\
                 qu1, qu3, qts1, qv3, qb2, qd1, qd2)
                 
    sp1.daemon = True
    sp1.start()

    #meter_tcp_dpsptp worker
    sp2 = meter_tcp_dpsptp.Meter_tcp_dpsptp_process(q22, q25, qtd1, qtd4, qtd5, qtd6, qw6, qw29, qw36)
    sp2.daemon = True
    sp2.start()

    #meter_tcp worker
    sp11 = meter_tcp_rw.Meter_tcp_rw_process(q25, q38, q40, qt1, qt2, qt3, qt4, qw31)
    sp11.daemon = True
    sp11.start()    
    
    #meter_serial worker
    #sp10 = meter_serial.meter_serial_process(q25, q35, qts1, qts2, qts3, qts4, qw30)
    #sp10.daemon = True
    #sp10.start()    

    #barometric pressure worker
    sp3 = baro_data.Baro_Process(q25, qb1, qb2, qb3, qw2)
    sp3.daemon = True
    sp3.start()
    
    # motor current worker
    sp4 = motor_current.Mtr_Current_Process(q6, q25, qm1, qm2, qm3, qm4, qm5, qm6, qm7, qw1, qw3, qw22, qwg1)
    sp4.daemon = True
    sp4.start()      

    # settings worker
    sp5 = settings.Settings_Process(q25, qk2, qk4, qw7)
    sp5.daemon = True
    sp5.start()          
    
    # analog_in worker  
    sp6 = analog_in.Ai_Process(q25, q28, q39, q42, qa1, qa2, qa3, qa4, qw26, qw35)
    sp6.daemon = True
    sp6.start()              
    
    # temp worker
    sp7 = usb485.USB485_Process(q20, q25, qu1, qu2, qu3, qw4, qw11)
    sp7.daemon = True
    sp7.start()

    # activity worker
    sp8 = activity.Activity_Process(qv1, qv2, qv3, qv4)
    sp8.daemon = True
    sp8.start()

    # mysql worker
    sp9 = mysql.Mysql_process(qd1, qd2)
    sp9.daemon = True
    sp9.start()    
        
    tornado.options.parse_command_line()

    gk = gen_key()
    settings = { 'websocket_ping_interval':0,
                 'cookie_secret': gk,
                 'login_url':'/login'
    }

    app = tornado.web.Application(
        handlers=[
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/controls", ControlsHandler),
            (r"/settings", SettingsHandler),
            (r"/graphs", GraphsHandler),
            (r"/graph", GraphsHandler),
            (r"/ws/(.*)", WebSocketHandler),
            (r"/activity", ActivityHandler),
            (r"cmds(.*)", CmdsHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {'path':  './'})
        ], **settings
    )

    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port1)
    #httpServer.listen(options.port2)
    #httpServer.listen(options.port3)
    #httpServer.listen(options.port4)
    cprint("Listening on port:%s"%options.port1)
    #cprint("Listening on port:%s"%options.port2)
    #cprint("Listening on port:%s"%options.port3)
    #cprint("Listening on port:%s"%options.port4)

    mainLoop = tornado.ioloop.IOLoop.instance()
    ## adjust the scheduler_interval according to the frames sent by the serial port
    scheduler_interval = 10
    scheduler = tornado.ioloop.PeriodicCallback(checkQueue, scheduler_interval) #, io_loop = mainLoop)
    scheduler.start()
    mainLoop.start()



    '''            
class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        None
       
        self.render('web/login/login.html')
        self.render('web/login/login.js')
        self.render('web/login/login.css')        
        self.render('web/main/main.js')
        self.render('web/main/main.css')
        self.render('web/settings/settings.html')
        self.render('web/settings/settings.js')
        self.render('web/settings/settings.css')        
        self.render('web/graphs/adjgraph.html')
        self.render('web/graphs/adjgraph.js')
        self.render('web/graphs/adjgraph.css')
        '''
