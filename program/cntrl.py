#!/usr/bin/python3
import sys, time, threading, queue, multiprocessing, serial, board, busio, adafruit_ina260, \
       math, inspect, torndb, MySQLdb, json, logging, logging.config, logging.handlers
from collections import OrderedDict
import shutil

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('cntrl')

db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')

getframe_expr = 'sys._getframe({}).f_code.co_name'
#print(eval(getframe_expr.format(2)))

from adafruit_motorkit import MotorKit
kit = MotorKit(address = 0x60)
p_kit = MotorKit(address = 0x61)

from adafruit_servokit import ServoKit
s_kit = ServoKit(address=0x44,channels=16)
s_kit.servo[0].set_pulse_width_range(500, 2500) 
s_kit.servo[0].actuation_range = 180
#s_kit.servo[1].set_pulse_width_range(500, 2500)
#s_kit.servo[1].actuation_range = 270
s_kit.servo[3].set_pulse_width_range(500, 2500)
s_kit.servo[3].actuation_range = 180

class Controls(multiprocessing.Process):
    def __init__(self,q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, q16, q17, q18,q19, q20, \
                 q21, q23, q24, q25, q26, q27, q28, q29, q30, q31, q32, q33, q34, q36, q37, q38, q39, q40, q41, q42, qm1, qm2, qm3, qm4, qm5, qm6, \
                 qm7, qs1, qs2, qs3, qs6, qs7, qs8, qs9, qs10, qs11, qw3, qw4, qw8, qw9, qw10, qw11, qw12, qw13, qw14,\
                 qw15, qw16, qw17, qw18, qw19, qw20, qw21, qw22, qw23, qw24, qw25, qw26, qw27, qw28, qw30, \
                 qw31, qw32, qw33, qw34, qw35, qw36, qw37, qw38, qw39, qw40, qk1, qk2, qk3, qk4, qt2, qt3, qt4, \
                 qtd4, qtd5, qtd6, qb1, qb3, qa1, qa2, qa3, qa4, \
                 qu1, qu3, qts1, qv3, qb2, qd1, qd2):

        self.kpv_vars_list = [ 'mtr_inrush_time',       'hb_max_time',           'hb_max_restarts',         'adj_max_pos',          \
                               'num_markers',           'marker_time',           'in_stable_dbnd',          'in_stable_time',       \
                               'in_stpt_divisions',     'in_stpt_cal_divisions', 'in_switch_stpt',          'in_fine_sw_der',       \
                               'in_fine_dbnd',          'in_switch_soak',        'stable_der_in',           'psi_stable_dbnd',      \
                               'psi_stable_time',       'psi_stpt_divisions',    'psi_stpt_cal_divisions',  'psi_switch_soak',      \
                               'psi_der_holdoff',       'psi_fine_sw_der',       'psi_switch_stpt_divisor', 'der_cycle_time',       \
                               'psi_fine_dbnd',         'stable_der_psi',        'baro_lock',               'baro_lock_active',    'in_count_time', 'psi_count_time',        \
                               'max_rdg_fail',          'beam_inhibit',          'meter_tcp_inhibit',       'unit_type',           'max_cal_attempts',   'dp_tolerance', \
                               'sp_tolerance',          'tp_tolerance',          'always_calibrate',        'dp_test_url',          \
                               'sp_test_url',           'full_test_active',      'max_marker_min',          'meter_reg_hold', \
                               'meter_reg_bu_tfcold',   'marker_send_method',    'dp_high_stpt',            'sp_high_stpt',\
                               'sounds_active',         'sound_interval',        'meter_reg_sp_mark',       'meter_reg_dp_mark',    \
                               'meter_reg_tp_mark',     'meter_reg_sp_cal_zero', 'meter_reg_sp_cal_0',      'meter_reg_sp_cal_50',  \
                               'meter_reg_sp_cal_100',  'meter_reg_sp_cal_done', 'meter_reg_dp_cal_zero',   'meter_reg_dp_cal_0',   \
                               'meter_reg_dp_cal_25',   'meter_reg_dp_cal_50',   'meter_reg_dp_cal_75',     'meter_reg_dp_cal_100', \
                               'meter_reg_dp_cal_done', 'meter_reg_tp_cal_zero', 'meter_reg_tp_cal_done'   ]

        self.kpv_index_list = [  18,  21,  22,  24,   \
                                 131, 132, 133, 134,  \
                                 136, 137, 138, 141,  \
                                 142, 143, 144, 150,  \
                                 151, 152, 153, 154,  \
                                 155, 159, 160, 162,  \
                                 163, 164, 165, 166, 188, 189,  \
                                 193, 205, 245, 246, 249, 251,  \
                                 252, 253, 254, 255,  \
                                 256, 257, 258, 262,  \
                                 263, 270, 196, 197,  \
                                 271, 272, 273, 274,  \
                                 275, 276, 277, 278,  \
                                 279, 280, 281, 282,  \
                                 283, 284, 285, 286,  \
                                 287, 288, 289  ]

        self.web_running = 0
        self.save_st = time.time() # save values every t seconds
        self.save_dt = 5 # t seconds to save values
        self.initial_web_update_st = time.time() # check comm to web every t seconds until response is received
        self.web_dt = 1
        multiprocessing.Process.__init__(self)
        self.web_prev_msg = ""
        self.sounds_active = 0
        self.status_ind_st = time.time()
        self.status_change=[None,None,None]

        self.q1 = q1 # web save_inch_center_position
        self.q2 = q2 # web close_inlet
        self.q3 = q3 # web close_outlet
        self.q4 = q4 # web initialize inlet
        self.q5 = q5 # cntrl.py init_outlet
        self.q6 = q6 # web re_center and motor current inst ma max
        self.q7 = q7 # web inlet control
        self.q8 = q8 # web outlet control
        self.q9 = q9 # web eq control
        self.q10 = q10 # web web_running
        self.q11 = q11 # web vent control
        self.q12 = q12 # serial_worker open the equalizer for high dp
        self.q13 = q13 # high sp alarm - open vent
        self.q14 = q14 # serial_worker in_vent_alarm
        self.q15 = q15 # web full auto checks
        self.q16 = q16 # full auto checks
        self.q17 = q17 # web in_full_auto_cal
        self.q18 = q18 # web skip point
        self.q19 = q19 # web low control
        self.q20 = q20 # temp readings for cntrl.py
        self.q21 = q21 # serial_worker stop_pid
        self.q23 = q23 # web psi_pid_start_stop
        self.q24 = q24 # manual control
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.q26 = q26 # rest motors
        self.q27 = q27 # start button
        self.q28 = q28 # stop button
        self.q29 = q29 # pause button
        self.q30 = q30 # zero inlet
        self.q31 = q31 # zero outlet
        self.q32 = q32 # heartbeat
        self.q33 = q33 # restart program
        self.q34 = q34 # ROC button
        self.q36 = q36 # web command to send a marker
        self.q37 = q37 # full test (SPDPTP auto)
        self.q38 = q38 # returned data_read_reg
        self.q39 = q39 # re-center command from analog_in.py
        self.q40 = q40 # returned meter_write_reg status code
        self.q41 = q41 # baro lock button
        self.q42 = q42 # zero adjuster position based on center beam sensor

        self.qw3 = qw3 # inlet_display
        self.qw4 = qw4 # temp readings from USB485.py
        self.qw8 = qw8 # pid values for web
        self.qw9 = qw9 # send markers
        self.qw10 = qw10 # ping web
        self.qw11 = qw11 # send_web_message for usb485.py
        self.qw12 = qw12 # save_msg_log
        self.qw13 = qw13 # eq_status
        self.qw14 = qw14 # outlet_display
        self.qw15 = qw15 # adj_pos_display
        self.qw16 = qw16 # stpt_display
        self.qw17 = qw17 # psi_stpt_display
        self.qw18 = qw18 # send_cal_low
        self.qw19 = qw19 # send_cal_high
        self.qw20 = qw20 # send_cal_mid
        self.qw21 = qw21 # send_web_message for cntrl.py
        self.qw22 = qw22 # send_web_message for motor_current.py
        self.qw23 = qw23 # send_web_message for serialworker.py
        self.qw24 = qw24 # btn_status
        self.qw25 = qw25 # pid_running_status
        self.qw26 = qw26 # beam indicators
        self.qw27 = qw27 # disable clear crystal alarm button
        self.qw28 = qw28 # ROC button
        self.qw30 = qw30 # send_web_message for meter_serial.py
        self.qw31 = qw31 # send_web_message for meter_tcp.py
        self.qw32 = qw32 # send_web_message for ssh.py
        self.qw33 = qw33 # sounds
        self.qw34 = qw34 # next/prev button enable/disable
        self.qw35 = qw35 # send_web_message for analog_in.py
        self.qw36 = qw36 # send_web_message for meter_tcp_dpsptp.py
        self.qw37 = qw37 # status indicator
        self.qw38 = qw38 # NA
        self.qw39 = qw39 # NA
        self.qw40 = qw40 # NA

        self.qt2 = qt2 # write register to meter tcp
        self.qt3 = qt3 # read register tcp
        self.qt4 = qt4 # send kpv file to meter_tcp_rw.py

        self.qtd4 = qtd4 # send kpv file to meter_tcp_dpsptp.py
        self.qtd5 = qtd5 # meter dpsptp to cntrl.py
        self.qtd6 = qtd6 # meter tcp connection status for cntrl.py
        
        self.qs1 = qs1 # cntrl.py eq_status
        self.qs2 = qs2 # cntrl.py vent_status
        self.qs3 = qs3 # cntrl.py   in_vent_status
        self.qs6 = qs6 # serial worker write to crystal
        self.qs7 = qs7 # dpsp readings for cntrl.py
        self.qs8 = qs8 # NA
        self.qs9 = qs9 # send auto_pid mode to serialworker
        self.qs10 = qs10 # send kpv file to serialworker.py
        self.qs11 = qs11 # serial worker dp high during SP testing

        self.qm1 = qm1 # motor_current.py motor direction
        self.qm2 = qm2 # motor_current.py adjuster position
        self.qm3 = qm3 # motor_current.py re-center active
        self.qm4 = qm4 # constant ma alarm checking
        self.qm5 = qm5 # request from motor_current.py for kpv list
        self.qm6 = qm6 # send kpv list to motor_current.py
        self.qm7 = qm7 # send kpv list from motor_current.py to cntrl

        self.qk1 = qk1 # settings.py request to cntrl.py for kpv
        self.qk2 = qk2 # send kpv to settings.py
        self.qk3 = qk3 # settings change from settings web page
        self.qk4 = qk4 # change made to kpv - update web

        self.qt4 = qt4 # send kpv file to meter_tcp_rw.py

        self.qtd4 = qtd4 # send kpv file to meter_tcp_dpsptp.py
        self.qtd6 = qtd6 # meter tcp connection status for cntrl.py

        self.qb1 = qb1 # baro set status for baro_data.py
        self.qb3 = qb3 # send kpv file to baro_data.py

        self.qa1 = qa1 # send kpv file to analog_in.py
        self.qa2 = qa2 # send adjuster position to analog_in.py
        self.qa3 = qa3  # re-center complete from cntrl.py
        self.qa4 = qa4 # re-center command from cntrl to analog in

        self.qu1 = qu1 # temp set status for baro_data.py
        self.qu3 = qu3 # send kpv file to usb485.py

        self.qts1 = qts1 # send kpv list to meter_serial.py

        self.qv3 = qv3 # kpv for activity.py

        self.qb2 = qb2 # baro psi for cntrl.py

        self.qd1 = qd1 # write to db
        self.qd2 = qd2 # read from db

        i2c = busio.I2C(board.SCL, board.SDA)
        self.ina260 = adafruit_ina260.INA260(i2c, 0x40)

        # heartbeat status initialization
        self.hb = 0
        self.hb_st = time.time()
        self.ck_hb_st = time.time()
        self.hb_restarts = 0

        # for web update

        self.initial_web_in_vent_status = 0
        self.initial_web_eq_status = 0
        self.initial_web_psi_vent_status = 0
        self.initial_web_inlet_pos = 0
        self.initial_web_outlet_pos = 0

        self.ref_DP_actual = None
        self.ref_SP_actual = 0
        self.ref_DPSP_current = False
        self.ref_TP_actual = None
        self.ref_TP_current = False
        self.pid_run = 0
        self.prev_stpt = None
        self.prev_mode = None
        self.max_dev = 0

        self.switch_to_fine = 1 # initial condition
        self.switch_to_rough = 0 # initial condition
        self.in_rough_dbnd = 0
        self.psi_rough_dbnd = 0.1
        self.psi_switch_stpt_rough = 200
        self.first_inst = 1
        self.new_pid = 0

        self.inlet_angle = 0
        self.inlet_prev_dir = 1
        self.outlet_angle = 0
        self.outlet_prev_dir = 1
        self.rdg_fail_count = 0

        self.skip_point = 0

        self.unit_type = 0 # 0 - Totalflow 1 - ROC
        self.vent = 0
        self.pump = 0
        self.pid_pause = 0
        self.pid_pause_btn = 0
        self.full_auto_stpt = 0
        self.marker_sent = 0
        self.number_markers_sent = 0
        self.num_markers = 2
        self.marker_sent_st = 0 # start timer after marker has been sent

        self.stable = 0  # inch readings stabilized - ready to send marker
        self.marker_countup = 0
        self.marker_send_st = time.time()
        self.stable_st = 0 # start time
        self.sound_playing = 0 # steady indicator
        self.sound_st = 0 # sound playing

        self.meter_DP_actual = 0
        self.meter_SP_actual = 13.4
        self.meter_TP_actual = 60
        self.meter_DPSPTP_current = False

        self.full_auto_cal = 0 # calibration - calibration mode
        self.cal_low_sent = 0
        self.cal_high_sent = 0
        self.cal_mid_sent = 0

        self.stop_one_shot = 0
        self.full_auto = 0 # full auto mode walks through markers / calibration automatically
        self.full_auto_stpt = 0
        self.marker_sent = 0
        self.psi_num_markers_sent = 0
        self.marker_sent_st = 0 # start timer after marker has been sent
        self.purge_active = 0

        self.psi_stable = 0  # inch readings stabilized - ready to send marker

        self.psi_stable_st = 0 # start time
        self.baro_psi = 13.4 # default baro psi - realtime baro pressure replaces this as data comes in
        self.ref_baro_current = False

        self.psi_cal_low_sent = 0
        self.psi_cal_high_sent = 0
        self.psi_cal_mid_sent = 0
        self.avg_der = 1000
        self.avg_der_array = []
        self.avg_der_array_length = 10

        self.avg_der_cycle_count = 0

        self.prev_msg = ""
        self.web_prev_msg = ""

        self.prev_msg = ""

        self.meter_data_received = None # indicate good register read
        self.meter_write_status = None # indicate good register read

        self.adj_centering_in_progress = 0

    def recenter_cmd(self, data):
        '''
            if int(data) == 2:
                if self.Mc.adj_pos > self.Mc.adj_min_move_amp and self.Mc.adjuster_direction > 0:
                    self.cprint("re-center adjuster down")
                    self.Mc.s2(self.Mc.s2_down_spd,self.Mc.adjuster_runout)

                    if self.Mc.s2_down_spd - 0.05 >= self.Mc.s2_down_spd_max:
                        self.Mc.s2_down_spd = self.Mc.s2_down_spd - 0.05
                        self.Mc.mod_kpv_file_entry(37, self.Mc.s2_down_spd)
                        self.cprint("New adjuster down spd : %s"%self.Mc.s2_down_spd)
                    elif self.Mc.s2_up_spd - 0.05 >= self.Mc.s2_up_spd_min:
                        self.Mc.s2_up_spd = self.Mc.s2_up_spd - 0.05
                        self.Mc.mod_kpv_file_entry(36, self.Mc.s2_up_spd)
                        self.cprint("New adjuster up spd : %s"%self.Mc.s2_up_spd)
                    else:
                        self.cprint("Adjuster tuning failed")

                if self.Mc.adj_pos < -1 * self.Mc.adj_min_move_amp and self.Mc.adjuster_direction < 0:
                    self.Mc.s2(self.Mc.s2_up_spd,self.Mc.adjuster_runout)
                    self.cprint("re-center adjuster up")

                    if self.Mc.s2_up_spd + 0.05 <= self.Mc.s2_up_spd_max:
                        self.Mc.s2_up_spd = self.Mc.s2_up_spd + 0.05
                        self.Mc.mod_kpv_file_entry(36, self.Mc.s2_up_spd)
                        self.cprint("New adjuster up spd : %s"%self.Mc.s2_up_spd)
                    elif self.Mc.s2_down_spd + 0.05 <= self.Mc.s2_down_spd_min:
                        self.Mc.s2_down_spd = self.Mc.s2_down_spd + 0.05
                        self.Mc.mod_kpv_file_entry(37, self.Mc.s2_down_spd)
                        self.cprint("New adjuster down spd : %s"%self.Mc.s2_down_spd)
                    else:
                        self.cprint("Adjuster tuning failed")
            else:
        '''
        self.Mc.center_in_adjuster()

    def send_web_message(self, var):
        if var != self.web_prev_msg:
            Dict = {'dest':'web_message', 'val':var}
            self.qw21.put(Dict)
            self.web_prev_msg = var

    def web_run(self, data):
        if int(data) == 1: # initial updates coming in from web
            #self.cprint("WEB RUNNING!")
            self.web_running = 1
            self.save_all(0)
            self.Mc.init_web_valve_states()
        else:
            self.web_running = 0

    def eq_alarm(self, data):
            self.cprint("vent alarm control command received")
            self.send_web_message("vent alarm control command received")
            self.pid_run = 0
            self.Mc.rest_motors()
            self.Mc.equalizer_ctrl(float(data))

    def vent_alarm(self, data):
            self.pid_run = 0
            self.Mc.rest_motors()
            self.Mc.vent_ctrl(float(data))

    def in_vent_alarm(self,data):
            self.pid_run = 0
            self.Mc.rest_motors()

    def full_auto_checks(self, data, mode):
        #self.Mc.rest_motors() # safety control
        try:
            val = float(data)
        except:
            self.cprint("Auto value from did not convert to float")
            self.pid_start = 0
            self.full_auto = 0
            Dict = {'dest':'next_prev_button_enable', 'data':0}
            self.mq(self.qw34, Dict)
            self.pid_run = 0
            self.Mc.rest_motors()
        else:
            if mode == 'i':
                #self.cprint("Commanded inch setpoint = " + str(val))
                self.Mc.vent_ctrl(1) # vent is open for DP checks
            elif mode == 'p':
                self.cprint("Commanded psi setpoint = " + str(val))
                self.Mc.vent_ctrl(0) # vent is closed for SP checks
            if val > -1:
                self.stable = 0
                self.number_markers_sent = 0
                if mode == 'p':
                    self.cprint('1')
                    self.marker_countdown = self.psi_count_time
                elif mode == 'i':
                    self.marker_countdown = self.in_count_time
                self.full_auto_stpt = val
                self.full_auto = 1
                Dict = {'dest':'next_prev_button_enable', 'data':1}
                self.mq(self.qw34, Dict)
                if self.pid_run == 1:
                    self.cprint('2')
                    self.stpt = val
                else:
                    self.cprint('3')
                    val = self.auto_pid(val,'test',mode)
                #self.cprint("self.auto_pid(val,'test',mode) : %s"%val)
                    return val
            else: # auto stop button press
                self.cprint('4')
                self.full_auto = 0
                Dict = {'dest':'next_prev_button_enable', 'data':0}
                self.mq(self.qw34, Dict)
                self.pid_run = 0
                #self.Mc.rest_motors()
                #self.Mc.vent_ctrl(0)
                self.marker_sent = 0

    def full_auto_cal(self,data, mode):
        self.Mc.rest_motors() # safety control
        try:
            val = float(data)
        except:
            self.cprint("Auto value from web did not convert to float")
            self.pid_start = 0
            self.full_auto_cal = 0
            self.Mc.rest_motors()
        else:
            if mode == 'p':
                self.cprint("Commanded inch setpoint = " + str(val))
            elif mode == 'i':
                self.cprint("Commanded psi setpoint = " + str(val))
            if val > -1:
                self.stable = 0
                self.full_auto_stpt = val
                self.full_auto_cal = 1
                if self.pid_run == 1:
                    self.stpt = val
                else:
                    self.auto_pid(val,'test',mode)
            else: # auto stop button press
                self.full_auto_cal = 0
                self.pid_run = 0
                self.Mc.rest_motors()
                self.Mc.vent_ctrl(0)
                self.cal_low_sent = 0
                self.cal_high_sent = 0
                self.cal_mid_sent = 0
                self.marker_sent = 0

    def stop_pid(self, data):
        self.pid_run = 0
        #self.Mc.rest_motors()

    def awaiting_good_data(self,source,interval,attempts,dtype=None,d_low=None,d_high=None): # source, interval, attempts, data type, desired low, desired high
        fta = self.full_test_active
        bad_count = 0
        self.check_input(0) # get current values

        if source == 'ref_DPSP':
            while (not self.ref_DPSP_current or \
                    (self.ref_DPSP_current and dtype != None and \
                      ( (dtype == 'DP' and not (d_low < self.ref_DP_actual < d_high)) or \
                        (dtype == 'SP' and not (d_low < self.ref_SP_actual < d_high)) ) ) ) and \
                   bad_count < attempts + 1:
                if fta and not self.continue_test():
                    return False
                bad_count += 1
                self.send_web_message("bad reference DP/SP reading - trying again")
                time.sleep(interval)
                self.check_input(0)
            if bad_count >= attempts:
                self.send_web_message("bad reference DP/SP reading after %s attempts - no more attempts will be made"%attempts)
                return False
            else:
                return True

        elif source == 'meter_DPSPTP':
            while (not self.meter_DPSPTP_current or \
                    (self.meter_DPSPTP_current and dtype != None and \
                      ( (dtype == 'DP' and not (d_low < self.meter_DP_actual < d_high)) or \
                        (dtype == 'SP' and not (d_low < self.meter_SP_actual < d_high)) or \
                        (dtype == 'DP' and not (d_low < self.meter_TP_actual < d_high)) ) ) ) and \
                   bad_count < attempts + 1:
                if fta and not self.continue_test():
                    return False
                bad_count += 1
                self.send_web_message("bad meter DP/SP/TP reading - trying again")
                time.sleep(interval)
                self.check_input(0)
            if bad_count >= attempts:
                self.send_web_message("bad meter DP/SP/TP reading after %s attempts - no more attempts will be made"%attempts)
                return False
            else:
                return True

        elif source == 'ref_TP':
            while not self.ref_TP_current and bad_count < attempts + 1:
                if fta and not self.continue_test():
                    return False
                bad_count += 1
                send_web_message("bad reference TP reading - trying again")
                time.sleep(interval)
                self.check_input(0)
            if bad_count >= attempts:
                send_web_message("bad reference TP reading after %s attempts - no more attempts will be made"%attempts)
                return False
            else:
                return True

        elif source == 'ref_baro':
            while not self.ref_baro_current or \
                  (self.ref_TP_current and dtype != None and not (d_low < self.ref_TP_actual < d_high)) and \
                   bad_count < attempts + 1:
                if fta and not self.continue_test():
                    return False
                bad_count += 1
                send_web_message("bad reference barometric reading - trying again")
                time.sleep(interval)
                self.check_input(0)
            if not self.ref_TP_current and bad_count >= attempts:
                send_web_message("bad reference barometric reading after %s attempts - no more attempts will be made"%attempts)
                return False
            else:
                return True

    def manual_control(self, data):
        #self.cprint(data)
        if data == "fine_up":
            self.Mc.s2(self.Mc.s2_up_spd, 100)

        elif data == "fine_down":
            self.Mc.s2(self.Mc.s2_down_spd,100)

        elif data == "u_fine_up":
            self.Mc.s2(self.Mc.s2_up_spd / 2, 10)

        elif data == "u_fine_down":
            self.Mc.s2(self.Mc.s2_down_spd / 2, 10)

        elif int(data) == 1:
            self.Mc.web_btn_status('adj_up','1')
            self.check_adj = 1
            while self.check_adj == 1:
                self.check_input(0)
                if self.adj_centering_in_progress == 1:
                    if abs(self.Mc.adj_pos) - abs(self.adj_centering_start_pos) > self.Mc.adjuster_runout:
                        self.adj_centering_in_progress = 0
                        self.check_adj = 0
                        self.cprint('Adjuster centering via center beam sensor failed',1,1)
                        self.mq(self.qa3,{'centering_status':'beam_failed'})
                ca = self.Mc.s2(1,300)
                if ca == 0: # ma_tripped stop loop
                    self.check_adj = 0

        elif int(data) == 0:
            # part of web exclusive button group - turn on to disable other buttons, then off
            if self.adj_centering_in_progress == 1:
                self.adj_centering_in_progress = 0
                self.cprint('Adjuster centering procedure stopped',1,1)
                self.mq(self.qa3,{'centering_status':'manual_stop'})
            self.Mc.web_btn_status('adj_stop','1')
            self.Mc.web_btn_status('adj_stop','0')
            self.Mc.s2(0,0)
            self.check_adj = 0

        elif int(data) == -1:
            self.Mc.web_btn_status('adj_down','1')
            self.check_adj = -1
            while self.check_adj == -1:
                self.check_input(0)
                if self.adj_centering_in_progress == 1:
                    if abs(self.Mc.adj_pos) - abs(self.adj_centering_start_pos) > self.Mc.adjuster_runout:
                        self.adj_centering_in_progress = 0
                        self.check_adj = 0
                        self.cprint('Adjuster centering via center beam sensor failed',1,1)
                        self.mq(self.qa3,{'centering_status':'beam_failed'})
                ca = self.Mc.s2(-1,300)
                if ca == 0: # ma_tripped stop loop
                    self.check_adj = 0
            
    def reset_intg(self):
        None

    def set_rough_fine(self,val):
        if val == 0:
            self.switch_to_fine = 0
            self.switch_to_rough = 1
        else:
            self.switch_to_fine = 1
            self.switch_to_rough = 0

    def auto_pid(self, stpt, test_or_cal='test',mode='i',cal_point=0): #auto pid procedure
        print('\n')
        self.pid_run = 1
        self.cprint("stpt : %s  test_or_cal : %s  mode : %s, cal_point : %s percent"%(stpt,test_or_cal,mode,cal_point))
        self.max_dev = 0
        try:
            self.first_inst = 1
            self.stpt = stpt
            pid_first_inst = 1
            self.cprint('6')
            self.status_ind_st = time.time()
            self.mq(self.qw37,{'dest':'status indicator','full_test_active':self.full_test_active,'test_active':self.pid_run}) # status indicator
            #---------------------Main while loop-----------------------
            while self.pid_run and self.stpt != -1 and self.stpt != None:
                #self.cprint("pid_run = %s" %self.pid_run)
                self.check_input(0)
                if not self.pid_run:
                    return False

                # initialization ---------------------------------------
                if self.stpt != self.prev_stpt or mode != self.prev_mode or pid_first_inst == 1:
                    pid_first_inst = 0
                    st = time.time()
                    self.prev_stpt = self.stpt
                    self.prev_mode = mode
                    self.number_markers_sent = 0
                    self.marker_sent = 0
                    self.stable_st = 0
                    self.marker_send_st = 0
                    self.mq(self.qs9,{'data':mode})
                    self.set_pid_btn(0) # set web start, stop, pause  button state to start
                    self.marker_st = time.time()
                    self.Mc.get_kpv_file() # get kpv values from file
                    self.switch_to_fine = 1 # start in fine mode
                    self.switch_to_rough = 0 # start in fine mode
                    self.outlet = 1
                    self.inlet = 0
                    self.marker_send_in_progress = 0
                    if mode == 'i':
                        self.marker_countdown = self.in_count_time
                        Dict = {'dest':'stpt_display', 'data':self.stpt}
                    elif mode == 'p':
                        self.marker_countdown = self.psi_count_time
                        Dict = {'dest':'psi_stpt_display', 'data':self.stpt}
                    self.mq(self.qw16, Dict)
                    if self.stpt == 0:
                        self.marker_countdown *= 2
                    p = pp = i = d = 0

                    # set valve positions
                    if self.inlet_angle < self.Mc.s0_default_angle - 5: # open past init angle so close
                        self.close_inlet()
                    if self.outlet_angle < self.Mc.s1_default_angle - 5:
                        self.close_outlet()

                    if self.stpt > -1:
                        # used to set button on web page for current marker
                        st = str(self.stpt)
                        st = st.replace(".","_")
                        st = st.replace("_0","")
                        if mode == 'i':
                            btn = 'auto_' + st
                        if mode == 'p':
                            btn = 'auto_psi_' + st
                        self.Mc.web_btn_status(btn,'1')

                        self.check_input(0) # get current dpsptp values
                        if not self.pid_run:
                            return False

                    # stpt divisions and switch stpts
                    if mode == 'p':
                        self.cprint("Setpoint = %s psi" %self.stpt)
                        stpt_div = self.full_auto_stpt / (self.psi_stpt_divisions - 1) # difference between each setpoint for full auto operation
                        psi_stpt_div_cal = self.full_auto_stpt / (self.psi_stpt_cal_divisions - 1) # difference between each calibration setpoint for full auto operation
                        Dict = {'dest':'psi_stpt_display', 'data':self.stpt}
                        self.mq(self.qw17, Dict)
                        self.psi_switch_stpt = self.stpt / self.psi_switch_stpt_divisor # setpoint to switch over from rough pid to fine pid
                        if self.psi_switch_stpt < 0.1:
                            self.psi_switch_stpt = 0.1
                        p = self.stpt - self.ref_SP_actual
                    elif mode == 'i':
                        self.cprint("Setpoint = %s in" %self.stpt)
                        stpt_div = self.full_auto_stpt / (self.in_stpt_divisions - 1) # difference between each setpoint for full auto operation
                        in_stpt_div_cal = self.full_auto_stpt / (self.in_stpt_cal_divisions - 1) # difference between each calibration setpoint for full auto operation
                        Dict = {'dest':'stpt_display', 'data':self.stpt}
                        self.mq(self.qw16, Dict)
                        p = self.stpt - self.ref_DP_actual
                    st = time.time()
                    reset_intg = 0
                    pp = p

                    self.cprint("Centering adjuster",1,1)
                    self.Mc.center_in_adjuster()

                # max time to send a marker reached---------------------
                if self.full_auto == 1 and time.time() - self.marker_st > self.max_marker_min * 60:
                    if self.purge_active == 1:
                        self.purge_active = 0
                        return False
                    else:
                        self.pid_pause = 0
                        self.send_web_message("Max allowable time to send a marker reached")
                        self.skip_point = 1
                        if self.stpt != 0:
                            self.send_web_message("Moving to next marker")
                self.check_input(0) # get current dpsp values
                if not self.pid_run:
                    return False
                if self.pid_pause == 0:
                    cif = 1 # used to skip current scan of pid algorithm
                    pw = 0
                    Dict = {'dest':'pid_running','data':1}
                    self.mq(self.qw25,Dict)

                    # move to next/prev point?
                    if self.full_auto == 1 and self.skip_point != 0:
                        self.stpt = self.stpt - stpt_div * self.skip_point
                        if self.stpt > self.full_auto_stpt:
                            self.stpt = self.full_auto_stpt
                        if self.stpt < 0:
                            return True
                        if stpt_div != 0:
                            if self.stpt % stpt_div != 0:
                                if mode == 'i':
                                    for i in range(int(self.in_stpt_divisions),0,-1):
                                        if stpt_div * i < self.prev_stpt:
                                            #print(stpt_div * i)
                                            self.stpt = stpt_div * i
                                            break
                                elif mode == 'p':
                                    for i in range(int(self.psi_stpt_divisions),0,-1):
                                        if stpt_div * i < self.prev_stpt:
                                            self.stpt = stpt_div * i
                                            break
                        self.skip_point = 0
                        #self.cprint("New setpoint = %s"%self.stpt,1,1)
                        first_inst = 1
                        cif = 0

                    if mode == 'p' and cif == 1:
                        self.Mc.equalizer_ctrl(0) # make sure the equalizer is open
                        self.Mc.low_ctrl(0) # make sure the valve to reference dp is closed
                        if self.stpt != 0:
                            self.Mc.vent_ctrl(0) # make sure the psi vent is closed
                        else:
                            self.Mc.vent_ctrl(1) # make sure the psi vent is open
                    elif mode == 'i' and cif == 1:
                        self.Mc.vent_ctrl(1) # make sure the psi vent is open
                        cif = self.Mc.low_ctrl(1,self.ref_SP_actual) # make sure the valve to reference dp is open
                        if cif == 1: # low valve opened
                            if self.stpt != 0:
                                self.Mc.equalizer_ctrl(1) # make sure the equalizer is closed
                            else:
                                self.Mc.equalizer_ctrl(0) # make sure the equalizer is open
                        else: # low valve not open
                            self.Mc.equalizer_ctrl(0) # make sure the equalizer is open                                

                    # pid --------------------------------------------------------
                    if cif == 1: # conditions correct to run pid
                        dt = time.time() - st # time between pid cycles for algorithm
                        dst = time.time()
                        st = time.time() # reset start time for next cycle
                        pp = p # proportional error value from previous pid iteration
                        if mode == 'p':
                            p = self.stpt - self.ref_SP_actual # calculate new proportional error
                            if abs(p) > self.psi_der_holdoff:
                                d = 0
                            else:
                                d = p - pp # derivative
                        elif mode == 'i':
                            p = self.stpt - self.ref_DP_actual # calculate new proportional error
                            d = p - pp # derivative

                        # calculate avg derivative
                        if time.time() - dst < self.der_cycle_time:
                            self.avg_der_cycle_count += 1
                        else:
                            dst = time.time()
                            self.avg_der_array_length = self.avg_der_cycle_count
                            self.avg_der_cycle_count = 0
                        self.avg_der_array.append(d)
                        while len(self.avg_der_array) > self.avg_der_array_length:
                            self.avg_der_array.pop(0)
                        if len(self.avg_der_array) > 0:
                            self.avg_der = sum(self.avg_der_array) / len(self.avg_der_array)

                        if mode == 'p':
                            if abs(p) > self.psi_switch_stpt + self.psi_fine_dbnd:
                                self.send_web_message("SP outside of setpoint deadband")
                        elif mode == 'i':
                            if abs(p) > self.in_switch_stpt + self.in_fine_dbnd:
                                self.send_web_message("DP outside of setpoint deadband")


                        #-----------------------------------------------
                        #fine pid
                        if self.switch_to_fine == 1:
                            if self.switch_to_rough == 1 or self.first_inst == 1: # reset values if switching to rough to fine pid
                                if self.first_inst == 1:
                                    self.first_inst = 0
                                self.close_inlet()
                                self.close_outlet()
                                d = 0
                                i = 0
                                self.switch_to_rough = 0
                                if mode == 'p':
                                    kp = self.Mc.s2_Kp_psi
                                    ki = self.Mc.s2_Ki_psi
                                    kd = self.Mc.s2_Kd_psi
                                elif mode == 'i':
                                    kp = self.Mc.s2_Kp_in
                                    ki = self.Mc.s2_Ki_in
                                    kd = self.Mc.s2_Kd_in
                                else:
                                    self.cprint("unknown auto pid mode : %s"%mode,1,0,None)

                            # determine if switch to rough is in order
                            if mode == 'p':
                                if abs(p) > self.psi_switch_stpt + self.psi_fine_dbnd:
                                    cif = 0
                                    self.switch_to_rough = 1
                            elif mode == 'i':
                                if abs(p) > self.in_switch_stpt + self.in_fine_dbnd:
                                    cif = 0
                                    self.switch_to_rough = 1

                            # conditions correct to stay in fine pid
                            if cif == 1:
                                # make sure inlet and outlet are fully closed
                                if mode == 'p':
                                    if cif == 1 and self.inlet_angle > self.Mc.s0_min_angle_psi:
                                        self.close_inlet()
                                elif mode == 'i':
                                    if cif == 1 and self.inlet_angle > self.Mc.s0_min_angle_in:
                                        self.close_inlet()
                                if cif == 1 and self.outlet_angle > self.Mc.s1_min_angle:
                                    self.close_outlet()

                                if self.stpt < 0: # command to stop pid
                                    # TODO move next three lines to better/more universal location
                                    self.full_auto = 0
                                    Dict = {'dest':'next_prev_button_enable', 'data':0}
                                    self.mq(self.qw34, Dict)
                                    self.pid_run = 0
                                    return False

                                if self.sounds_active == 1 and self.marker_send_in_progress == 0:
                                    if self.sound_playing == 0 or time.time() - self.sound_st > self.sound_interval:
                                        self.play_sound('psi_stable')
                                        self.sound_playing = 1
                                        self.sound_st = time.time()

                                # integral ----------------------------------------
                                if cif == 1 and mode == 'p':
                                    if abs(p) < .01:
                                        i = 0
                                    if abs(p) < self.Mc.s2_intg_holdoff_psi:
                                        i += p * dt # integral - running sum of errors
                                    if abs(i) > self.Mc.s2_max_intg_psi:
                                        i = (i/abs(i)) * self.Mc.s2_max_intg_psi
                                elif cif == 1 and mode == 'i':
                                    if abs(p) < .03:
                                        i = 0
                                    if abs(p) < self.Mc.s2_intg_holdoff_in:
                                        i += p * dt # integral - running sum of errors
                                    if abs(i) > self.Mc.s2_max_intg_in:
                                        i = (i/abs(i)) * self.Mc.s2_max_intg_in

                                # calculate new adjuster pid --------------------------
                                pid = pid = kp * p + ki * i + kd * d

                                # calculate new adjuster pw ---------------------------
                                pw = 0
                                if self.stpt != 0: #prevent divide by 0
                                    if mode == 'p':
                                        pw = abs(pid/self.psi_switch_stpt) * self.Mc.s2_rng + self.Mc.s2_min
                                    elif mode == 'i':
                                        pw = abs(pid/self.in_switch_stpt) * self.Mc.s2_rng + self.Mc.s2_min
                                self.check_input(0)
                                if not self.pid_run:
                                    return True
                                if self.skip_point != 0:
                                    cif = 0
                                if cif == 1:
                                    if p > -0.00 and self.stpt != 0: # inside deadband - under stpt
                                        self.Mc.s2(self.Mc.s2_up_spd, pw) # run adjuster at the new level / pw - save value as actual value act
                                    if p < 0.00 and self.stpt != 0: #inside deadband - over stpt
                                        self.Mc.s2(self.Mc.s2_down_spd, pw) # run adjuster at the new level / pw - save value as actual value act
                                    if mode == 'p':
                                        self.Mc.s2_soak_scale = 1 - abs(p / self.psi_switch_stpt) # change multiplier to change soak time based on distance from setpoint
                                    if mode == 'i':
                                        self.Mc.s2_soak_scale = 1 - abs(p / self.in_switch_stpt) # change multiplier to change soak time based on distance from setpoint
                                    self.Mc.s2_soak_scaled = self.Mc.s2_soak * self.Mc.s2_soak_scale
                                    if dt > 0.25:
                                        None
                                    self.Mc.s2(0, self.Mc.s2_soak) # stop the adjuster and allow soak time for fluctuations in pressure


                                    # full auto operation of markers-------------------------------------------------------------
                                    if cif == 1 and (self.full_auto == 1 or test_or_cal == 'cal') and self.stpt != -1 and self.stpt != None:
                                        if test_or_cal == 'test':
                                            text = 'marker'
                                        elif test_or_cal == 'cal':
                                            text = 'calibration point'
                                        if self.marker_sent == 0:
                                            if (mode == 'p' and abs(p) <= self.psi_stable_dbnd and abs(d) < self.stable_der_psi) or \
                                                (mode == 'i' and abs(p) <= self.in_stable_dbnd and abs(d) < self.stable_der_in):
                                                if self.stable_st == 0 and self.marker_send_in_progress == 0: # just entered deadband - start the timer
                                                    self.stable_st = time.time() # start the timer to determine inch reading stability for marker
                                                    #self.cprint("Inside deadband - timer started")
                                                    if mode == 'p':
                                                        if self.purge_active == 1:
                                                            self.cprint("filling system with nitrogen for purge - stabilized in %s" %self.marker_countdown,1,1)
                                                        else:
                                                            self.cprint("Inside SP setpoint deadband - Sending %s in %s" %(text,self.marker_countdown),1,1)
                                                    elif mode == 'i':
                                                        self.cprint("Inside DP setpoint deadband - Sending %s in %s" %(text,self.marker_countdown),1,1)
                                                    self.marker_countdown -= 1
                                                    if self.marker_countdown < 0:
                                                        self.marker_countdown = 0
                                                    self.marker_countup += 1
                                                elif (self.marker_countdown <= 0):  # start timer already running - readings stable for enough time to send marker
                                                    self.marker_send_in_progress = 1
                                                    self.marker_sent = 1
                                                    self.stable_st = 0
                                                    self.marker_send_st = time.time()
                                                    self.marker_countup = 0

                                                    if test_or_cal == 'cal':
                                                        self.marker_send_in_progress = 0
                                                        self.marker_sent = 0
                                                        self.marker_send_st = 0                                                    
                                                        self.number_markers_sent = 0
                                            
                                                    if mode == 'i':
                                                        self.marker_countdown = self.in_count_time
                                                        self.cprint("Sending DP %s %s" %(text,self.stpt),1,1)
                                                        if test_or_cal == 'test':
                                                            self.send_marker('DP',self.ref_DP_actual,self.meter_DP_actual,'test',self.stpt)
                                                        elif test_or_cal == 'cal':
                                                            write_success = self.send_marker('DP',self.ref_DP_actual,self.meter_DP_actual,'cal',self.stpt,cal_point)
                                                            self.pid_run = 0
                                                            self.full_auto = 0
                                                            self.full_auto_cal = 0
                                                            return write_success
                                                    elif mode == 'p':
                                                        self.marker_countdown = self.psi_count_time
                                                        if self.purge_active == 1:
                                                            self.purge_active = 0
                                                            self.pid_run = 0
                                                            return True # exit back to full test command
                                                        else:
                                                            self.cprint("Sending SP %s %s" %(text,str(self.stpt+self.baro_psi)))
                                                            if test_or_cal == 'test':
                                                                self.send_marker('SP',self.ref_SP_actual + self.baro_psi,self.meter_SP_actual,'test',self.stpt + self.baro_psi)
                                                            elif test_or_cal == 'cal':
                                                                self.send_marker('SP',self.ref_SP_actual + self.baro_psi,self.meter_SP_actual,'cal',self.stpt + self.baro_psi,cal_point)
                                                                self.pid_run = 0
                                                                return True

                                                # still in deadband - countdown timer to send marker
                                                if time.time() - self.stable_st > self.marker_countup and self.marker_send_in_progress == 0:
                                                    if mode == 'p':
                                                        if self.purge_active == 1:
                                                            self.send_web_message("pre-filling system with nitrogen for purge - closing inlet valve in %s" %self.marker_countdown)
                                                        else:
                                                            self.send_web_message("Inside SP setpoint deadband - Sending %s in %s" %(text,self.marker_countdown))
                                                    elif mode == 'i':
                                                        self.send_web_message("Inside DP setpoint deadband - Sending %s in %s" %(text,self.marker_countdown))
                                                    self.marker_countdown -= 1
                                                    if self.marker_countdown < 0:
                                                        self.marker_countdown = 0
                                                    self.marker_countup += 1
                                            else: # outside of deadband - reset timer
                                                if (mode == 'p' and abs(d) > self.stable_der_psi):
                                                        self.send_web_message("SP derivative too high (%s > %s)- resetting timer"%(format(abs(d),'.2f'), self.stable_der_psi))
                                                elif (mode == 'i' and abs(d) > self.stable_der_in):
                                                        self.send_web_message("DP derivative too high (%s > %s)- resetting timer"%(format(abs(d),'.2f'), self.stable_der_in))
                                                else:
                                                    self.send_web_message("Outside of deadband - timer reset")
                                                self.stable_st = 0
                                                if mode == 'p':
                                                    self.marker_countdown = self.psi_count_time
                                                elif mode == 'i':
                                                    self.marker_countdown = self.in_count_time
                                                if self.stpt == 0:
                                                    self.marker_countdown *= 2
                                                self.marker_countup = 0
                                        # marker already sent
                                        elif (self.marker_send_st != 0 and \
                                              time.time() - self.marker_send_st > self.marker_time) \
                                              or self.number_markers_sent >= self.num_markers:
                                            if self.full_test_active == 0:
                                                self.cprint("time to send a marker elapsed",1,1)
                                            self.marker_send_in_progress = 0
                                            self.stable_st = 0
                                            self.marker_send_st = 0
                                            self.marker_sent = 0
                                            self.number_markers_sent += 1
                                            if self.number_markers_sent >= self.num_markers: # self.num_markers is number of markers per point to send - e.g. duplicate markers
                                                self.stpt = self.stpt - stpt_div # setpoint for next marker
                                                self.number_markers_sent = 0
                                                # test complete
                                                #self.cprint("self.stpt : %s"%self.stpt)
                                                if self.stpt < 0:
                                                    if self.full_test_active == 1:
                                                        self.cprint("Test complete",1,1)
                                                    else:
                                                        if mode == 'p':
                                                            self.cprint("SP test complete",1,1)
                                                        if mode == 'i':
                                                            self.cprint("DP test complete",1,1)
                                                    self.stpt = None
                                                    if self.full_test_active == 0:
                                                        self.stop_button()
                                                    self.Mc.rest_motors()
                                                    self.pid_run = 0
                                                    return True
                                                # move to next point
                                                else:
                                                    self.cprint("Moving to next marker",1,1)
                                                    print('\n')
                                                    self.send_web_message("New setpoint = %s"%self.stpt)
                                                    self.marker_sent = 0
                                                    self.stable_st = 0
                                                    self.marker_send_st = 0

                                    elif cif == 1 and self.full_auto_cal == 0: # not in full auto
                                        self.stable_st = 0 # reset the timer for inch stability for markers
                                        self.marker_sent = 0
                                        self.marker_send_st = 0

                        # fine pid
                        #-----------------------------------------------



                        #-----------------------------------------------
                        #rough pid
                        if self.switch_to_rough == 1:

                            if self.switch_to_fine == 1: # reset values if switching to fine from rough pid
                                i = 0
                                d = 0
                                self.outlet = 1
                                self.inlet = 1
                                self.switch_to_fine = 0

                            # determine if switch to fine is in order
                            cif = 1 # used to bypass rough to get to fine
                            if mode == 'p':
                                if abs(p) < self.psi_switch_stpt and \
                                    (p * pp < 0 or abs(self.avg_der) < self.psi_fine_sw_der):
                                    cif = 0
                                    self.switch_to_fine = 1
                            elif mode == 'i':
                                if abs(p) < self.in_switch_stpt and \
                                    (p * pp < 0 or abs(self.avg_der) < self.in_fine_sw_der):
                                    cif = 0
                                    self.switch_to_fine = 1
                            # determine if switch to fine is in order

                            self.psi_rough_dbnd = 0 # reset rough dbnd
                            in_rough_dbnd = 0 # reset rough dbnd
                            #print(mode == 'i' and p > self.in_switch_stpt + in_rough_dbnd and stpt != 0)

                            #-----------------------------------
                            # outlet pid -----------------------
                            if cif == 1 and \
                            ((mode == 'p' and p < -self.psi_switch_stpt - self.psi_rough_dbnd and self.stpt != 0) or \
                                (mode == 'i' and p < -self.in_switch_stpt - in_rough_dbnd and self.stpt != 0)): # below setpoint
                                # switching from inlet to outlet
                                if self.inlet == 1 or self.first_inst == 1:
                                    if self.first_inst == 1:
                                        self.first_inst = 0
                                    self.close_inlet()
                                    self.inlet = 0
                                    self.outlet = 1
                                    d = 0
                                    self.Mc.s2(0,0) # No need to operate adjuster until outside of rough range
                                    time.sleep(self.psi_switch_soak / 1000)
                                    if mode == 'p':
                                        self.init_outlet('p') # move inlet to angle just before pressure increase
                                        kp = self.Mc.s1_Kp_psi
                                        ki = self.Mc.s1_Ki_psi
                                        kd = self.Mc.s1_Kd_psi
                                    elif mode == 'i':
                                        self.init_outlet('i') # move inlet to angle just before pressure increase
                                        kp = self.Mc.s1_Kp_in
                                        ki = self.Mc.s1_Ki_in
                                        kd = self.Mc.s1_Kd_in
                                    else:
                                        self.cprint("unknown auto pid mode : %s"%mode,1,0,None)
                                    
                                i += p
                                if mode == 'p':
                                    if abs(p) > self.Mc.s1_intg_holdoff_psi:
                                        i = 0
                                    if abs(i) > self.Mc.s1_max_intg_psi:
                                        i = (i/abs(i)) * self.Mc.s1_max_intg_psi
                                elif mode == 'i':
                                    if abs(p) > self.Mc.s1_intg_holdoff_in:
                                        i = 0
                                    if abs(i) > self.Mc.s1_max_intg_in:
                                        i = (i/abs(i)) * self.Mc.s1_max_intg_in

                                pid = (kp * p) + (ki * i) + (kd * d)
                                if pid > 0 and pid != 0:
                                    pw = (pid / self.Mc.s1_pw_holdoff) * self.Mc.s1_move_close_range + (pid /abs(pid)) * self.Mc.s1_move_min
                                elif pid != 0:
                                    if mode == 'p':
                                        pw = (pid / self.Mc.s1_pw_holdoff) * self.Mc.s1_move_open_range_psi + (pid /abs(pid)) * self.Mc.s1_move_min
                                    elif mode == 'i':
                                        pw = (pid / self.Mc.s1_pw_holdoff) * self.Mc.s1_move_open_range_in + (pid /abs(pid)) * self.Mc.s1_move_min

                                self.check_input(0)
                                if not self.pid_run:
                                    return True
                                if self.skip_point != 0:
                                    cif = 0

                                if cif == 1:
                                    # move outlet valve
                                    self.Mc.s1(pw)
                                    time.sleep(self.Mc.s1_soak/1000)
                            # outlet pid -----------------------
                            #-----------------------------------

                            # -----------------------------------------
                            # inlet pid -------------------------------
                            elif cif == 1 and \
                            ((mode == 'p' and p > self.psi_switch_stpt + self.psi_rough_dbnd and self.stpt != 0) or \
                                (mode == 'i' and p > self.in_switch_stpt + in_rough_dbnd and self.stpt != 0)):
                                # switching from outlet to inlet
                                if self.outlet == 1 or self.first_inst == 1:
                                    if self.first_inst == 1:
                                        self.first_inst = 0
                                    self.close_outlet()
                                    d = 0
                                    i = 0
                                    self.outlet = 0
                                    self.inlet = 1
                                    self.Mc.s2(0,0) # No need to operate adjuster until outside of rough range
                                    if mode == 'p':
                                        time.sleep(self.psi_switch_soak / 1000)
                                        self.init_inlet() # move inlet to angle just before pressure increase
                                    if mode == 'i':
                                        time.sleep(self.in_switch_soak / 1000)

                                    if mode == 'p':
                                        self.init_inlet('p') # move inlet to angle just before pressure increase
                                        kp = self.Mc.s0_Kp_psi
                                        ki = self.Mc.s0_Ki_psi
                                        kd = self.Mc.s0_Kd_psi
                                    elif mode == 'i':
                                        self.init_inlet('i') # move inlet to angle just before pressure increase
                                        kp = self.Mc.s0_Kp_in
                                        ki = self.Mc.s0_Ki_in
                                        kd = self.Mc.s0_Kd_in
                                    else:
                                        self.cprint("unknown auto pid mode : %s"%mode,1,0,None)                                    
                                # switching from outlet to inlet

                                i += p
                                if mode == 'p':
                                    if abs(p) > self.Mc.s0_intg_holdoff_psi:
                                        i = 0
                                    if abs(i) > self.Mc.s0_max_intg_psi:
                                        i = (i/abs(i)) * self.Mc.s0_max_intg_psi
                                elif mode == 'i':
                                    if abs(p) > self.Mc.s0_intg_holdoff_in:
                                        i = 0
                                    if abs(i) > self.Mc.s0_max_intg_in:
                                        i = (i/abs(i)) * self.Mc.s0_max_intg_in

                                pid = (kp * p) + (ki * i) + (kd * d)
                                pw = 0
                                if pid > 0:
                                    pw = (pid / self.Mc.s0_pw_holdoff) * self.Mc.s0_move_open_range +  (pid /abs(pid)) *  self.Mc.s0_move_min
                                elif pid < 0:
                                    pw = (pid / self.Mc.s0_pw_holdoff) * self.Mc.s0_move_close_range +  (pid /abs(pid)) *  self.Mc.s0_move_min
                                else:
                                    pw = 0

                                # move inlet valve
                                self.check_input(0)
                                if not self.pid_run:
                                    return True
                                if self.skip_point != 0:
                                    cif = 0
                                if self.stpt != 0 and self.stpt != None and cif == 1 and self.skip_point == 0:
                                    #print('line 1012 self.stpt : %s'%self.stpt)
                                    #print('cntrl.py line 1011 pw : %s'%pw)
                                    self.Mc.s0(-1 * pw,mode)
                                time.sleep(self.Mc.s0_soak/1000)
                                ''' inlet pid'''
                                """-----------------------------"""
                                """-----------------------------"""

                            # inlet pid -------------------------------
                            # -----------------------------------------


                        #rough pid
                        #-----------------------------------------------
                        if dt > 0.25:
                            Dict = {'dest':'web_pid', 'p':p, 'i':i, 'd':d, 'kp':kp, 'ki':ki, 'kd':kd, 'kpp':kp*p, 'kii':ki*i, 'kdd':kd*d, 'pid': kp*p + ki*i + kd*d,'pw':pw}
                            self.send_web_pid(Dict)

                else: # pid paused
                    pass
                self.check_input(0)
                if not self.pid_run:
                    return False
                time.sleep(0.05)
            self.check_input(0)
            if not self.pid_run:
                return False

        # auto_pid failure
        except:
            raise
            self.pid_run = 0
            self.cprint("Failure in auto pid")
            self.Mc.rest_motors()
            return False

    def close_inlet(self):
        self.Mc.s0(self.Mc.s0_max_angle)

    def init_inlet(self, mode = 'i'):
        #self.cprint("initialize inlet angle")
        if mode == 'p':
            self.Mc.s0(self.Mc.s0_init_angle_psi - s_kit.servo[0].angle,mode)
        elif mode == 'i':
            self.Mc.s0(self.Mc.s0_init_angle_in - s_kit.servo[0].angle,mode)

    def zero_inlet(self,data):
        if data > 0:
            self.send_web_message("temporary inlet max angle : %s"%data)
            self.Mc.mod_kpv_file_entry(40,int(data))
            self.Mc.s0_max_angle_prev = self.Mc.s0_max_angle
            self.Mc.s0_max_angle = data
        else:
            self.send_web_message("previous inlet max angle : %s"%self.Mc.s0_max_angle_prev)
            self.Mc.s0_max_angle = int(s_kit.servo[0].angle)
            self.Mc.mod_kpv_file_entry(40,int(self.Mc.s0_max_angle))
            self.send_web_message("new inlet max angle : %s"%self.Mc.s0_max_angle)

    def zero_outlet(self,data):
        self.cprint('zero_outlet')
        if data > 0:
            self.send_web_message("temporary outlet max angle : %s"%data)
            self.Mc.mod_kpv_file_entry(54,int(data))
            self.Mc.s1_max_angle_prev = self.Mc.s1_max_angle
            self.Mc.s1_max_angle = data
        else:
            self.send_web_message("previous outlet max angle : %s"%self.Mc.s1_max_angle_prev)
            #self.Mc.s1_max_angle = int(s_kit.servo[1].angle)
            self.Mc.s1_max_angle = int(s_kit.servo[3].angle)
            self.Mc.mod_kpv_file_entry(54,int(self.Mc.s1_max_angle))
            self.send_web_message("new outlet max angle : %s"%self.Mc.s1_max_angle)

    def save_all(self, user):
        try:
            self.Mc.update_adj_pos_display()
        except:
            self.cprint("not able to update adj position display")
        # Dict =  {'dest':'save_msg_log', 'purpose':'save_msg_log', 'data':'1'}
        # self.mq(self.qw11,Dict)

    def check_heartbeat(self):
        if time.time() - self.hb_st > self.hb_max_time:
            self.hb_restarts = self.hb_restarts + 1
            self.hb_st = time.time()
            if self.hb_restarts > self.hb_max_restarts:
                None
                #self.cprint("max number(%s) of program restarts attempted. Program will terminate"%self.hb_max_restarts)
            else:
                None
                #self.cprint("Attempting program restart - attempt #%s"%self.hb_restarts)
                #self.restart_program()

    def restart_program(self):
        self.mq(self.q33, 1)

    def save_msg_log(self,msg):
        try:
            self.file_o = open("log/msg_log.txt","r+")
        except:
            self.cprint("Not able to open the msg_log.txt file")
        else:
            try:
                rd_all = self.file_o.readlines() # read in all lines of file
            except:
                self.cprint("msg_log file did not read in")
            else: # all lines read in
                self.file_o.truncate(0)
                self.file_o.close()
                try:
                    self.file_o = open("log/msg_log.txt","r+")
                except:
                    self.cprint("not able to open msg_log file")
                else:
                    try:
                        self.file_o.write(rd_all + "\n" + msg)
                    except:
                        self.cprint("not able to write to msg_log file")
                    else:
                        self.file_o.close()
                try: # backup
                    shutil.copy('log/msg_log.txt', 'log/msg_log_bu.txt')
                except:
                    self.cprint("Backup of msg_log file failed")

    def close_outlet(self):
        #self.cprint('close_outlet : %s'%self.Mc.s1_max_angle)
        self.Mc.s1(self.Mc.s1_max_angle)

    def init_outlet(self, mode = 'i'):
        self.cprint("initialize outlet angle",0,0)
        if mode == 'p':
            #self.Mc.s1(self.Mc.s1_init_angle_psi - s_kit.servo[1].angle)
            self.Mc.s1(self.Mc.s1_init_angle_psi - s_kit.servo[3].angle)
        elif mode == 'i':
            #self.Mc.s1(self.Mc.s1_init_angle_in - s_kit.servo[1].angle)
            self.Mc.s1(self.Mc.s1_init_angle_in - s_kit.servo[3].angle)

    def baro_lock_button(self, data):
        if self.baro_lock_active == 1:
            self.baro_lock_active = 0
            self.Mc.mod_kpv_file_entry(166,0)
            self.Mc.web_btn_status('btn_baro_lock','0')
        elif self.baro_lock_active == 0:
            self.baro_lock_active = 1
            self.Mc.mod_kpv_file_entry(166,1)
            self.Mc.web_btn_status('btn_baro_lock','1')
        self.mq(self.qw37,{'dest':'baro_lock','baro_lock':self.baro_lock_active}) # baro lock field color

    def start_button(self, data):
        self.pause_button(0)
        val = float(data['data'])
        self.pid_pause = 0
        self.set_pid_btn(0)
        if data['purpose'] == 'pid_start_inch':
            #self.cprint("Commanded inch setpoint = " + str(val))
            if val > -1:
                self.Mc.vent_ctrl(1)
                if self.pid_run == 1:
                    self.stpt = val
                else:
                    self.auto_pid(val,'test','i')
        elif data['purpose'] == 'pid_start_psi':
            #self.cprint("Commanded psi setpoint = " + str(val))
            if val > -1:
                self.Mc.vent_ctrl(0)
                if self.pid_run == 1:
                    self.stpt = val
                else:
                    self.auto_pid(val,'test','p')

    def stop_button(self,manual = 1):
        #getframe_expr = 'sys._getframe({}).f_code.co_name'
        #self.cprint("stop_button called by %s"%eval(getframe_expr.format(2)))
        self.pid_pause = 0
        self.set_pid_btn(1)
        self.pid_run = 0
        self.full_auto = 0
        if manual == 1:
            self.full_test_active = 0
        Dict = {'dest':'next_prev_button_enable', 'data':0}
        self.mq(self.qw34, Dict)
        self.full_auto_cal = 0
        # have to have try / except because of super call
        try:
            self.s0(self.s0_max_angle)
            self.s1(self.s1_max_angle)
            self.s2(0,0)
        except:
            self.Mc.s0(self.Mc.s0_max_angle)
            self.Mc.s1(self.Mc.s1_max_angle)
            self.Mc.s2(0,0)
        #self.send_web_message("Stop command received")

    def pause_button(self, data):
        self.first_inst = 1
        if data == 1:
            self.close_inlet()
            self.close_outlet()
            if self.pid_run == 1:
                self.stable_st = 0
                self.send_web_message("Auto operation paused")
                self.close_inlet()
                self.close_outlet()
                self.pid_pause = 1
                self.set_pid_btn(2)
            else:
                self.send_web_message("Nothing to pause")
                self.set_pid_btn(1)
        elif data == 0:
            if self.pid_run == 1:
                self.set_pid_btn(0)
                self.send_web_message("Auto operation resumed")
            else:
                self.set_pid_btn(1)
            self.pid_pause = 0

    def set_pid_btn(self,val = 1): # toggle pid auto button display colors
        if val == 0: # start
            try:
                self.web_btn_status('pid_start',1)
            except:
                self.Mc.web_btn_status('pid_start',1)
        elif val == 1: # stop
            try:
                self.web_btn_status('pid_stop',1)
            except:
                self.Mc.web_btn_status('pid_stop',1)
        elif val == 2: # pause
            try:
                self.web_btn_status('pid_pause',1)
            except:
                self.Mc.web_btn_status('pid_pause',1)

    def send_marker(self, dtype='None', r_read = -100.0, m_read = -100.0, test_or_cal='test', marker=-100, cal_point = '0'):
        meter_write_success = 1
        #print("unit_type : %s", self.unit_type)
        self.cprint("dtype : %s  r_read : %s  m_read : %s test_or_cal : %s  marker : %s  cal_point : %s"%(dtype,r_read,m_read,test_or_cal,marker,cal_point))
        Dict = {'dest':'send_marker', 'data':marker, 'unit_type':self.unit_type}
        if self.marker_send_method == 0:
            self.mq(self.qw9, Dict)
        elif self.marker_send_method == 1:
            # get correct register to send
            if dtype == 'SP':
                if test_or_cal == 'test':
                    reg = self.meter_reg_sp_mark
                    #self.cprint("reg : %s"%reg)
                elif test_or_cal == 'cal':
                    if cal_point == 'zero':
                        reg = self.meter_reg_sp_cal_zero
                    elif cal_point == '0':
                        reg = self.meter_reg_sp_cal_0
                    elif cal_point == '50':
                        reg = self.meter_reg_sp_cal_50
                    elif cal_point == '100':
                        reg = self.meter_reg_sp_cal_100
            elif dtype == 'DP':
                if test_or_cal == 'test':
                    reg = self.meter_reg_dp_mark
                elif test_or_cal == 'cal':
                    if cal_point == 'zero':
                        reg = self.meter_reg_dp_cal_zero
                    elif cal_point == '0':
                        reg = self.meter_reg_dp_cal_0
                    elif cal_point == '25':
                        reg = self.meter_reg_dp_cal_25
                    elif cal_point == '50':
                        reg = self.meter_reg_dp_cal_50
                    elif cal_point == '75':
                        reg = self.meter_reg_dp_cal_75
                    elif cal_point == '100':
                        reg = self.meter_reg_dp_cal_100
            elif dtype == 'TP':
                if test_or_cal == 'test':
                    reg = self.meter_reg_tp_mark
                elif test_or_cal == 'cal':
                    if cal_point == 'zero':
                        reg = self.meter_reg_tp_cal_zero
            self.cprint("reg : %s  marker : %s"%(reg,marker))
            if not self.meter_write_reg(str(reg),'float',marker):
                self.cprint("command to write to meter failed",1,1)
                meter_write_success = 0

        # record marker in database
        Dict = {'dest':'record_marker_db', 'dtype':dtype, 'm_read':m_read,'r_read':r_read}
        #self.cprint(Dict)
        self.mq(self.qd1, Dict)

        # track maximum deviation
        dev = abs(m_read - r_read)
        if dev > self.max_dev and test_or_cal == 'test':
            self.max_dev = dev

        r_read = format(r_read,'.2f')
        m_read = format(m_read,'.2f')
        dev = format(dev,'.2f')
        if test_or_cal == 'test':
            self.send_web_message("%s marker sent - desired:%s  reference:%s  meter:%s  deviation:%s"%(dtype,marker,r_read,m_read,dev))
        elif test_or_cal == 'cal':
            if cal_point == 'zero':
                txt = ''
            else:
                txt = '%'
            self.send_web_message("%s calibration point (%s%s - %s) sent"%(dtype,cal_point,txt,marker))

        return meter_write_success


    def full_test_command(self, data):
        if data == 1:
            self.collect = 0
            self.get_found = 0
            self.zero_ref = 0
            self.test_sp = 0
            self.test_dp = 0
            self.test_tp = 1
            self.sp_pass = self.dp_pass = self.tp_pass = 'incomplete'
            if self.beam_inhibit == 1:
                self.cprint("Adjuster beam sensors disabled - enable beam sensors to perform test",0,1,'w')
                return 'beam_inhibit'
            # TODO check for connection type
            if True and self.meter_tcp_inhibit:
                self.cprint("rcc to meter tcp inhibit setting turned on - change setting to perform test",0,1,'w')
                return 'meter_connection_fail'
            #elif True and self.meter_serial_inhibit:
            #    self.cprint("rcc to meter serial inhibit setting turned on - change setting to perform test",0,1,'w')
            #    return 'meter_connection_fail'
            # TODO check for connection type

            self.marker_send_method_prev = self.marker_send_method
            self.marker_send_method = 1
            self.full_test_active = 1
            self.mq(self.qw37,{'dest':'status indicator','full_test_active':self.full_test_active,'test_active':self.pid_run,'pause':self.pid_pause}) # status indicator
            
            ''' collect data / backup ----------------------------------------------------------------------------------'''
            if self.collect == 1:
                self.send_web_message("backing up tfcold in meter")
                if not self.meter_write_reg(self.meter_reg_bu_tfcold,'float',1):
                    self.cprint("command to backup tfcold in meter failed",1,1)
                time.sleep(2)
                                
            ''' put in hold -----------------------------------------------------------------------------------'''
            if True:
                if not self.continue_test():
                    return False
                if not self.meter_hold_command(1):
                    # TODO self.check_meter_ping()
                    return 'meter_connection_fail'

            ''' hold procedure successful - get meter found values ---------------------------------------------------'''
            if self.get_found == 1:
                if not self.continue_test():
                    return False
                self.send_web_message("getting meter found values")
                time.sleep(2)
                bad_count = 0
                if not self.awaiting_good_data('meter_DPSPTP',2,5,None,None,None): # source,sleep interval, total attempts, DPSPTP, low, high
                    return False
                # good meter SP data
                self.dp_found = self.meter_DP_actual
                self.sp_found = self.meter_SP_actual
                self.tp_found = self.meter_TP_actual
                time.sleep(2)
                if not self.continue_test():
                    return False
                self.send_web_message("Meter found values : DP:%s  SP:%s  TP:%s"%(self.dp_found,self.sp_found,self.tp_found))
                time.sleep(2)

            ''' good meter found data - prepare manifold--------------------------------------------------'''
            if True:
                if not self.continue_test():
                    return False

                # TODO if not self.meter_manifold_control('purge'):
                #    return False

            ''' purge procedure successful - zero reference ---------------------------------------------------'''
            if self.zero_ref == 1:
                time.sleep(2)
                self.send_web_message("opening rcc equalizer")
                time.sleep(2)
                self.Mc.equalizer_ctrl(0) # open rcc equalizer
                time.sleep(2)
                self.send_web_message("opening rcc reference DP solenoid")
                time.sleep(2)
                self.Mc.low_ctrl(1) # open rcc equalizer
                time.sleep(2)                
                self.send_web_message("opening rcc vent")
                self.Mc.vent_ctrl(1) # open rcc vent
                time.sleep(2)
                self.send_web_message("waiting for pressures to stabilize")
                if not self.pressure_stabilized():
                    return False
                if not self.continue_test():
                    return False
                self.send_web_message("zeroing reference DP and SP")
                time.sleep(2)
                # TODO only zero if close already
                self.mq(self.qs6,{"purpose":"crystal_write","data" : "Z1"})
                time.sleep(1)
                # TODO only zero if close already
                self.mq(self.qs6,{"purpose":"crystal_write","data" : "Z2"})
                time.sleep(3)
                self.check_input(0) # get current dpsp values
                self.send_web_message("checking for successful reference zero DP and SP")
                time.sleep(2)
                bad_count = 0
                if not self.awaiting_good_data('ref_DPSP',1,5,'DP',-0.05,0.05): # source,sleep interval, total attempts, DPSPTP, low, high
                    self.send_web_message("not able to zero reference DP")
                    return False
                if not self.awaiting_good_data('ref_DPSP',1,5,'SP',-0.1,0.1): # source,sleep interval, total attempts, DPSPTP, low, high
                    self.send_web_message("not able to zero reference SP")
                    return False
                self.send_web_message("reference DP and SP zeroed successfuly")
                time.sleep(2)

            ''' reference zeroed - system ready for checks ---------------------------------------------------'''
            if not self.continue_test():
                return False

            if self.test_sp == 1: # SP checks ---------------------------------------------------
                self.cprint("Starting SP test",1,1)
                checks_complete = 1
                #self.max_dev = 5 # just for testing
                if not self.full_auto_checks(self.sp_test_url,'p'): # multi-point checks
                    self.cprint("SP test failed",1,1)
                    sp_checks_complete = 0 # skip to DP
                if not self.continue_test():
                    return False
                if checks_complete == 1:
                    self.cprint("SP test results - max deviation : %s"%format(self.max_dev,'.3f'),1,1)
                if self.max_dev <= self.sp_tolerance and self.always_calibrate != 1:
                    self.cprint("SP test results within tolerance - no calibration required",1,1)
                    self.sp_pass = 'pass'
                if checks_complete == 1 and (self.max_dev > self.sp_tolerance or self.always_calibrate == 1):
                    if not self.always_calibrate:
                        self.cprint("SP test results not within tolerance",1,1)
                        time.sleep(2)
                    self.cprint("Starting SP calibration",1,1)
                    time.sleep(2)

                    self.sp_cal_attempts = 0
                    while self.full_test_active and \
                          self.max_dev > self.sp_tolerance and \
                          self.sp_cal_attempts < self.max_cal_attempts:

                        self.cprint()
                        # calibrate -------------------------------
                        # test_or_cal argument set to 'cal' allows countdown to send behaviour
                        # meter only requires low and span to calibrate
                        cal_success = 1
                        if not self.auto_pid(0,'cal','p','0'):
                            cal_success = 0
                            self.cprint("SP 0% calibration failed",1,1)                           
                        if not self.continue_test():
                            return False
                        if cal_success == 1:
                            time.sleep(5)
                            if not self.auto_pid(self.sp_test_url,'cal','p','100'):
                                cal_success = 0
                                self.cprint("SP 100% calibration failed",1,1)
                        if not self.continue_test():
                            return False
                        if cal_success == 1 and self.psi_stpt_cal_divisions == 5:
                            time.sleep(5)
                            if not self.auto_pid(self.sp_test_url * 0.75,'cal','p','75'):
                                cal_success = 0
                                self.cprint("SP 75% calibration failed",1,1)
                        if not self.continue_test():
                            return False
                        if cal_success == 1 and self.psi_stpt_cal_divisions == 3 or self.psi_stpt_cal_divisions == 5:
                            time.sleep(5)
                            if not self.auto_pid(self.sp_test_url * 0.5,'cal','p','50'):
                                cal_success = 0
                                self.cprint("SP 50% calibration failed",1,1)
                        if not self.continue_test():
                            return False
                        if cal_success == 1 and self.psi_stpt_cal_divisions == 5:
                            time.sleep(5)
                            if not self.auto_pid(self.sp_test_url * 0.25,'cal','p','25'):
                                cal_success = 0
                                self.cprint("SP 25% calibration failed",1,1)
                        if cal_success == 0:
                            self.sp_cal_attempts += 1
                            self.cprint("SP calibration failure %s / %s"%(self.sp_cal_attempts,self.max_cal_attempts))
                        else: #cal_success == 1
                            # write cal done
                            if not self.meter_write_reg(self.meter_reg_sp_cal_done,'float',1):
                                self.cprint("command to write new calibration values to meter failed",1,1)
                            self.cprint("SP calibration complete",1,1)


                        # test after cal  -------------------------
                        if not self.continue_test():
                            return False
                        if cal_success == 1:
                            self.cprint("performing SP test after calibration",1,1)
                            if not self.full_auto_checks(self.sp_test_url,'p'): # multi-point checks
                                self.cprint("SP test failed",1,1)
                                checks_complete = 0
                                self.max_dev = 0 # skip to dp
                            if not self.continue_test():
                                return False                                
                            if checks_complete == 1:
                                if self.max_dev > self.sp_tolerance:
                                    self.sp_cal_attempts += 1
                                    self.send_web_message('SP calibration failed. Re-attempting SP calibration')
                                else:
                                    self.sp_cal_attempts = 0
                                    self.send_web_message('SP calibration successful')
                                    self.sp_pass = 'pass'
                                    cal_success = 0 # prepare for DP cal
                        if self.sp_cal_attempts >= self.max_cal_attempts:
                            self.send_web_message('Max number of SP calibration attempts reached')
                            self.sp_pass = 'fail'
                            self.sp_cal_fail = 1
            else:
                self.sp_pass = 'skipped'
                
            if self.test_dp == 1: # DP checks ---------------------------------------------------
                self.cprint("Starting DP test",1,1)
                checks_complete = 1
                #self.max_dev = 5 # just for testing
                if not self.full_auto_checks(self.dp_test_url,'i'): # multi-point checks
                    self.cprint("DP test failed",1,1)
                    sp_checks_complete = 0 # skip to DP
                if not self.continue_test():
                    return False
                if checks_complete == 1:
                    self.cprint("DP test results - max deviation : %s"%format(self.max_dev,'.3f'),1,1)
                if self.max_dev <= self.dp_tolerance and self.always_calibrate != 1:
                    self.cprint("DP test results within tolerance - no calibration required",1,1)
                    self.dp_pass = 'pass'
                if checks_complete == 1 and (self.max_dev > self.dp_tolerance or self.always_calibrate == 1):
                    if not self.always_calibrate:
                        self.cprint("DP test results not within tolerance",1,1)
                        time.sleep(2)
                    self.cprint("Starting DP calibration",1,1)
                    time.sleep(2)

                    self.dp_cal_attempts = 0
                    while self.full_test_active and \
                          self.max_dev > self.dp_tolerance and \
                          self.dp_cal_attempts < self.max_cal_attempts:

                        # calibrate -------------------------------
                        # test_or_cal argument set to 'cal' allows countdown to send behaviour
                        # meter only requires low and span to calibrate
                        cal_success = 1
                        if not self.auto_pid(0,'cal','i','0'):
                            cal_success = 0
                            self.cprint("DP 0% calibration failed",1,1)                           
                        if not self.continue_test():
                            return False
                        if cal_success == 1:
                            time.sleep(5)
                            if not self.auto_pid(self.dp_test_url,'cal','i','100'):
                                cal_success = 0
                                self.cprint("DP 100% calibration failed",1,1)
                        if not self.continue_test():
                            return False
                        if cal_success == 1 and self.in_stpt_cal_divisions == 5:
                            time.sleep(5)
                            if not self.auto_pid(self.dp_test_url * 0.75,'cal','i','75'):
                                cal_success = 0
                                self.cprint("DP 75% calibration failed",1,1)
                        if not self.continue_test():
                            return False
                        if cal_success == 1 and self.in_stpt_cal_divisions == 3 or self.in_stpt_cal_divisions == 5:
                            time.sleep(5)
                            if not self.auto_pid(self.dp_test_url * 0.5,'cal','i','50'):
                                cal_success = 0
                                self.cprint("DP 50% calibration failed",1,1)
                        if not self.continue_test():
                            return False
                        if cal_success == 1 and self.in_stpt_cal_divisions == 5:
                            time.sleep(5)
                            if not self.auto_pid(self.dp_test_url * 0.25,'cal','i','25'):
                                cal_success = 0
                                self.cprint("DP 25% calibration failed",1,1)
                        if cal_success == 0:
                            self.dp_cal_attempts += 1
                            self.cprint("DP calibration failure %s / %s"%(self.dp_cal_attempts,self.max_cal_attempts))
                        else: #cal_success == 1
                            # write cal done
                            if not self.meter_write_reg(self.meter_reg_dp_cal_done,'float',1):
                                self.cprint("command to write new calibration values to meter failed",1,1)
                            self.cprint("DP calibration complete",1,1)


                        # test after cal  -------------------------
                        if not self.continue_test():
                            return False
                        if cal_success == 1:
                            self.cprint("performing DP test after calibration",1,1)
                            if not self.full_auto_checks(self.dp_test_url,'i'): # multi-point checks
                                self.cprint("DP test failed",1,1)
                                checks_complete = 0
                                self.max_dev = 0 # skip to dp
                            if not self.continue_test():
                                return False                                
                            if checks_complete == 1:
                                if self.max_dev > self.dp_tolerance:
                                    self.dp_cal_attempts += 1
                                    self.send_web_message('DP calibration failed. Re-attempting calibration')
                                else:
                                    self.sp_cal_attempts = 0
                                    self.send_web_message('DP calibration successful')
                                    self.dp_pass = 'pass'
                                    cal_success = 0 # prepare for DP cal
                        if self.dp_cal_attempts >= self.max_cal_attempts:
                            self.send_web_message('Max number of DP calibration attempts reached')
                            self.dp_pass = 'fail'
                            self.dp_cal_fail = 1
            else:
                self.dp_pass = 'skipped'
                
            if self.test_tp == 1: # TP checks ---------------------------------------------------
                self.cprint("Starting TP test",1,1)
                self.max_dev = 0
                if not self.continue_test():
                    return False
                if not self.awaiting_good_data('meter_DPSPTP',2,5): # source, interval, attempts, data type, desired low, desired high
                    self.test_success_tp = 0
                if not self.awaiting_good_data('ref_TP',2,5): # source, interval, attempts, data type, desired low, desired high
                    self.test_success_tp = 0
                self.send_marker('TP',self.ref_TP_actual, self.meter_TP_actual, 'test', self.ref_TP_actual)
                # TP calibrate if necessary (or always perform)
                time.sleep(3)
                if not self.continue_test():
                    return False
                if self.max_dev <= self.tp_tolerance and self.always_calibrate != 1:
                    self.cprint("TP test results within tolerance - no calibration required",1,1)
                    self.tp_pass = 'pass'
                if self.max_dev > self.tp_tolerance or self.always_calibrate == 1:
                    if self.max_dev > self.tp_tolerance and self.always_calibrate == 0:
                        self.cprint("TP test results not within tolerance - starting calibration",1,1)
                    self.tp_cal_attempts = 0
                    while self.max_dev > self.tp_tolerance and self.tp_cal_attempts < self.max_cal_attempts:
                        # calibrate -------------------------------
                        if not self.continue_test():
                            return False
                        self.send_marker('TP',self.ref_TP_actual, self.meter_TP_actual, 'cal', self.ref_TP_actual,'zero')
                        time.sleep(6)
                        if not self.continue_test():
                            return False                        

                        # write new cal
                        #if not self.meter_write_reg(self.meter_reg_tp_cal_done,'float',1):
                        #    self.cprint("command to write tp calibration to meter failed",1,1)
                            
                        # test after cal  -------------------------
                        self.max_dev = 0
                        self.send_marker('TP',self.ref_TP_actual, self.meter_TP_actual, 'test', self.ref_TP_actual)
                        self.cprint("self.max_dev : %s self.tp_tolerance : %s"%(self.max_dev,self.tp_tolerance))
                        time.sleep(3)
                        if self.max_dev > self.tp_tolerance:
                            self.tp_cal_attempts += 1
                            self.send_web_message('TP calibration failed')
                            if self.tp_cal_attempts >= self.max_cal_attempts:
                                self.send_web_message('Max number of TP calibration attempts reached')
                                self.tp_pass = 'fail'
                                self.tp_cal_fail = 1
                            else:
                                self.send_web_message('Re-attempting TP calibration')                            
                        else:
                            self.tp_cal_attempts = 0
                            self.send_web_message('TP calibration successful')
                            self.tp_pass = 'pass'
            else:
                self.tp_pass = 'skipped'
                                            
            self.cprint('Full test complete- (sp test : %s)  (dp test: %s)  (tp test : %s)'%(self.sp_pass,self.dp_pass,self.tp_pass),0,1)
            # TODO put manifold in normal mode
            #self.meter_manifold_control('run')
            # take out of hold
            self.meter_hold_command(0)
            # TODO generate report

    def meter_hold_command(self, cmd):
        fta = self.full_test_active
        meter_in_hold = None
        attempts = 0
        while meter_in_hold != cmd and attempts < 6:
            # check hold status
            if fta and not self.continue_test():
                return False
            self.cprint("checking meter hold status",0,1)
            self.meter_read_reg(self.meter_reg_hold,'float') # 11.0.3/9000 as int

            data = self.meter_awaiting_data(time.time())
            if data == False:
                return False
            reg = data['register']
            data = data['data']
            txt1 = "" if cmd == 0 else "not"
            txt2 = "remove" if cmd == 0 else ""
            if data != 'timeout' and data != 'error':
                meter_in_hold = int(data)
                if meter_in_hold != cmd:
                    attempts += 1
                    time.sleep(2)
                    self.cprint('Meter %s in hold  - sending %s hold command - attempt #%s'%(txt1,txt2,attempts),0,1)
                    if not self.meter_write_reg(self.meter_reg_hold,'float',cmd):
                        self.cprint("command to write %s hold command to meter failed"%txt2,1,1)                    
            else:
                self.cprint('bad response from meter - sending %s hold command - attempt #%s'%(txt1,attempts),1,1,'d')
                attempts += 1
            if meter_in_hold == cmd:
                time.sleep(2)
                if cmd == 1:
                    self.cprint("meter in hold",0,1)
                elif cmd == 0:
                    self.cprint("meter out of hold",0,1)
                return True
            time.sleep(3)

        if meter_in_hold != cmd: # max number of attempts reached
            if cmd == 1:
                self.cprint('%s attempts to put meter in hold have failed. No more attempts will be made.'%attempts,1,1,'d')
            elif cmd == 0:
                self.cprint('%s attempts to take meter out of hold have failed. No more attempts will be made.'%attempts,1,1,'d')
            return False

    def meter_manifold_control(self,cmd):
        if cmd == 'run':
            self.Mc.m4(0) # protect crystal DP port - close expose crystal solenoid
            time.sleep(1)
            self.Mc.m2(1) # open manifold equalizer
            time.sleep(3)
            self.close_inlet()
            time.sleep(1)
            self.close_outlet()
            # TODO check meter DP close to zero
            self.Mc.m5(0) # open rcc eq
            time.sleep(3)
            self.Mc.m6(0) # close rcc vent to prepare for nitrogen fill
            time.sleep(3)
            self.Mc.m3(1) # energize manifold bottom valves - closes off stream and vents gas
            time.sleep(3)

            ''' pre-fill tubing from rcc to manifold with nitrogen -------------------------------'''
            self.purge_active = 1 # gets set back to 0 in auto_pid after stabilization
            if not self.full_auto_checks(self.sp_found,'p'): # fill with nitrogen and stabilize - then return
                self.send_web_message("Attempt to pre-fill system with nitrogen failed")
                return False

            ''' pre-fill successful - de-energize top manifold valves --------------------------------'''
            self.Mc.m1(0) # de-energize manifold top valves
            time.sleep(3)
            # TODO consider venting isolated nitrogen on rcc ??
              # maybe best to leave in system - valves in rest state safe for crystal
            # TODO check for leaks on meter side
            self.Mc.m3(0) # de-energize manifold bottom valves
            time.sleep(3)
            self.Mc.m2(0) # de-energize manifold equalizer
            return True

        if cmd == 'purge':
            self.Mc.m5(0) # open rcc eq
            time.sleep(3)
            self.Mc.m4(0) # protect crystal DP port
            time.sleep(1)
            self.send_web_message("equalizing meter manifold")
            self.Mc.m2(1) # open manifold equalizer
            time.sleep(4)
            self.send_web_message("checking equalization of meter manifold pressure")
            if not self.awaiting_good_data('meter',2,5,'SP',-5.0,5.0): # source, interval, DPSPTP, desired low, desired high
                return False
            self.close_inlet()
            time.sleep(1)
            self.close_outlet()
            time.sleep(1)
            self.Mc.m6(0) # close rcc vent to prepare for nitrogen fill
            time.sleep(3)
            self.Mc.m3(1) # energize manifold bottom valves - closes off stream and vents gas
            time.sleep(3)


            ''' pre-fill tubing from rcc to manifold with nitrogen'''
            self.purge_active = 1 # gets set back to 0 in auto_pid after stabilization
            if not self.full_auto_checks(self.sp_found,'p'): # fill with nitrogen and stabilize - then return
                self.send_web_message("Attempt to pre-fill system with nitrogen for purge failed")
                return False


            ''' initial purge successful continue procedure ---------------------------------'''
            self.Mc.m1(1) # energize manifold top valves - to allow purge nitrogen in from rcc
            # pre-fill full test system with nitrogen
            self.purge_active = 1 # gets set back to 0 in auto_pid after stabilization
            if not self.full_auto_checks(self.sp_found,'p'): # fill with nitrogen and stabilize - then return
                self.send_web_message("Attempt to fill system with nitrogen for purge failed")
                return False


            ''' second purge successful continue procedure ---------------------------------'''
            self.Mc.m6(1) # vent purge nitrogen / gas mix
            return True

    def pressure_stabilized(self,source='both',dp_dev=0.05,sp_dev=0.2,stable_time=5,max_time=15):
        st = sst = time.time()
        counter = 0
        self.check_input(0)
        m_dp = m_dp_prev = self.meter_DP_actual
        m_sp = m_sp_prev = self.meter_SP_actual
        r_dp = r_dp_prev = self.ref_DP_actual
        r_sp = r_sp_prev = self.ref_SP_actual
        sa = [False,False,False,False]
        while time.time() - st < max_time:
            if not self.continue_test():
                return False
            m_dp = self.meter_DP_actual
            m_sp = self.meter_SP_actual
            r_dp = self.ref_DP_actual
            r_sp = self.ref_SP_actual
            if sst != None:
                if time.time() - sst > stable_time:
                    self.send_web_message("pressures stabilized")
                    return True

            sa[0] = abs(m_dp - m_dp_prev) <= dp_dev
            sa[1] = abs(m_sp - m_sp_prev) <= sp_dev
            sa[2] = abs(r_dp - r_dp_prev) <= dp_dev
            sa[3] = abs(r_sp - r_sp_prev) <= sp_dev

            if source == 'both':
                if sa[0] and sa[1] and sa[2] and sa[3]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None
            elif source == 'meter':
                if sa[0] and sa[1]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None
            elif source == 'ref':
                if sa[2] and sa[3]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None
            elif source == 'meter_dp':
                if sa[0]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None
            elif source == 'meter_sp':
                if sa[1]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None
            elif source == 'ref_dp':
                if sa[2]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None
            elif source == 'ref_sp':
                if sa[3]:
                    if sst == None:
                        sst = time.time()
                else:
                    sst = None

            if sst != None:
                if time.time() - sst > counter:
                    self.send_web_message("pressure stable in %s sec"%abs(stable_time - counter))
                    counter += 1
            else:
                counter = 0
                self.send_web_message("pressure not stable - resetting stable timer")

            m_dp_prev = m_dp
            m_sp_prev = m_sp
            r_dp_prev = r_dp
            r_sp_prev = r_sp

            time.sleep(0.5)

        self.send_web_message("unable to stabilize pressures - cancelling test")
        return False




    def continue_test(self):
        self.check_input(0)
        if not self.full_test_active:
            self.marker_send_method = self.marker_send_method_prev
        return self.full_test_active

    def in_to_psi(self,data):
        return data * 0.036127291827354

    def meter_read_reg(self, reg, data_type, mode = 'tcp'):
        if mode == 'tcp':
            if data_type == 'int': # when reading/writing ints to meter use a -1 offset e.g. to read/write 9000 use 8999
                reg = reg - 1
            self.cprint("read register request : %s  type : %s"%(reg,data_type),0,0,'d')
            Dict = {"purpose":"meter_read_reg","return_to":"cntrl","register":reg,"data_type":data_type}
            #self.cprint(Dict)
            self.mq(self.qt3,Dict)

    def meter_write_reg(self, reg, data_type, val, mode = 'tcp',timeout = None,wait = 1):
        tstamp = time.time()
        if mode == 'tcp':
            self.cprint("Sending command to write to register : %s  val : %s  type : %s"%(reg,val,data_type))
            Dict = {"purpose":"meter_write_reg","register":reg,"data_type":data_type,"value":val,'tstamp':tstamp}
            self.mq(self.qt2,Dict)
            if wait == 1:
                return self.meter_write_success(tstamp)

    def meter_write_success(self,tstamp):
        data = self.meter_awaiting_data(tstamp,'write')
        self.cprint("meter_write_success data : %s  data type : %s"%(data,type(data)),0,0,'d')
        if data != None:
            try:
                code = int(data['code'])
            except:
                self.cprint("meter write status code did not convert to int")
                return False
            else:
                if code == 16: # error code received after attempt to write
                    return True
        return False

    def meter_awaiting_data(self,tstamp,dtype='read',timeout = 10):
        data = None
        st = time.time()
        while time.time() - st < timeout:
            #self.cprint("awaiting data : %s  %s"%(tstamp,time.time()))
            self.check_input(0)
            if dtype == 'read' and self.meter_data_received != None:
                #self.cprint("data received")
                data = self.meter_data_received
                self.meter_data_received = None
                self.cprint("data received %s"%data,0,0,'d')
                return data
            elif dtype == 'write' and self.meter_write_status != None:
                #self.cprint("data received")
                data = self.meter_write_status
                self.meter_write_status = None
                self.cprint("modbus write status received %s  time_stamp : %s"%(data,tstamp),0,0,'d')
                return data                
            time.sleep(0.05)

        self.cprint("timeout waiting on data from meter",1,1,'w')
        return data


    def play_sound(self,data = 'psi_stable'):
        Dict = {'dest':'play_sound', 'data':data}
        self.mq(self.qw33, Dict)

    def send_cal_low(self, marker):
        #self.cprint("1604 send cal low")
        Dict = {'dest':'send_cal_low', 'data':marker}
        self.mq(self.qw18, Dict)

    def send_cal_high(self, marker):
        Dict = {'dest':'send_cal_high', 'data':marker}
        self.mq(self.qw19, Dict)

    def send_cal_mid(self, marker):
        Dict = {'dest':'send_cal_mid', 'data':marker}
        self.mq(self.qw20, Dict)

    def send_web_pid(self, Dict):
        self.mq(self.qw8, Dict)

    def ping_web(self):
        Dict = {'dest':'ping_web', 'data':1}
        self.mq(self.qw10, Dict)

    def ft2(self, data, precision):
        if precision == 2:
            return (format(data,'.2f'))

    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (ctrl%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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

    def init_kpv_to_val(self, index = 'init', val = 0):
        tv = 'int'
        if len(self.kpv_vars_list) > 0:
            if index == 'init':
                for i in range(len(self.kpv_vars_list)):
                    if str(self.Mc.KpvTypes[self.kpv_index_list[i]]) == 'i':
                        tv = 'int'
                    elif str(self.Mc.KpvTypes[self.kpv_index_list[i]]) == 'f':
                        tv = 'float'
                    elif str(self.Mc.KpvTypes[self.kpv_index_list[i]]) == 's':
                        tv = 'str'
                    exec("self." + self.kpv_vars_list[i] + " = " + tv + "(self.Mc.Kpv[" + str(self.kpv_index_list[i]) + "])")
                #self.cprint(self.kpv_vars_list)
                #self.cprint(self.kpv_index_list)
            else:
                index = int(index)
                fv = -1
                for i in range(len(self.kpv_index_list)):
                    if index == self.kpv_index_list[i]:
                        fv = i
                        break
                if str(self.Mc.KpvTypes[index]) == 'i':
                    tv = 'int'
                elif str(self.Mc.KpvTypes[index]) == 'f':
                    tv = 'float'
                elif str(self.Mc.KpvTypes[index]) == 's':
                    tv = 'str'
                if (fv != -1):
                    if tv == 'str':
                        val = val.replace("\n","") # remove eol characters
                        exec("self." + self.kpv_vars_list[fv] + " = str('" + val + "')")
                    else:
                        exec("self." + self.kpv_vars_list[fv] + " = " + tv + "(" + str(val) + ")")

        self.marker_countdown = self.in_count_time
        self.marker_send_method_prev = self.marker_send_method


    def check_input(self, val):
        #self.cprint("cntrl.py running")
        #print("check input  %s"%format(time.time(),".3f"))
        #self.cprint("check input")
        if self.rdg_fail_count > self.max_rdg_fail and self.pid_run == 1:
            self.pid_run = 0
            #self.Mc.rest_motors()
        #self.cprint()

        if not self.q1.empty(): # web save_inch_center_position
            data = self.q1.get()
            self.cprint(data)
            self.Mc.adj_pos = 0
        #self.cprint()
        if not self.q2.empty(): # web close_inlet
            data = self.q2.get()
            self.cprint(data)
            self.close_inlet()
        #self.cprint()
        if not self.q3.empty():  # web close_outlet
            data = self.q3.get()
            self.cprint(data)
            self.close_outlet()
        #self.cprint()
        if not self.q4.empty(): # web initialize inlet
            data = self.q4.get()
            self.init_inlet()
        #self.cprint()
        if not self.q5.empty(): # cntrl.py init_outlet
            data = self.q5.get()
            self.init_outlet()
        #self.cprint()
        if not self.q6.empty(): # web re_center and motor current inst ma max
            data = self.q6.get()
            if data['purpose'] == 're_center':
                self.recenter_cmd(data['data'])
            elif data['purpose'] == 'stop':
                self.manual_control(0)

        #self.cprint()
        if not self.q7.empty(): # web inlet control
            data = self.q7.get()
            d = int(data['data'])
            self.Mc.s0((d/abs(d))*self.Mc.s0_manual_pw,'m')
        #self.cprint()
        if not self.q8.empty(): # web outlet control
            data = self.q8.get()
            d = int(data['data'])
            self.Mc.s1((d/abs(d))*self.Mc.s1_manual_pw)
        #self.cprint()
        if not self.q9.empty(): # web eq control
            data = self.q9.get()
            self.Mc.equalizer_ctrl(float(data['data']))
            #self.stop_button()
        #self.cprint()
        if not self.q10.empty(): # web web_running
            data = self.q10.get()
            self.web_run(data['data'])
        if not self.q11.empty(): # web vent control
            data = self.q11.get()
            #self.cprint(data)
            self.Mc.vent_ctrl(float(data['data']))
        ##self.cprint()
        if not self.q12.empty(): # serial_worker open the equalizer for high dp
            data = self.q12.get()
            self.eq_alarm(data['data'])
        #self.cprint()
        if not self.q13.empty(): # high sp alarm - open vent
            data = self.q13.get()
            self.vent_alarm(data['data'])
            self.stop_button(0)
        if not self.q14.empty(): # serial_worker in_vent_alarm
            data = self.q14.get()
            self.in_vent_alarm(data['data'])
        if not self.q15.empty(): # web full auto checks
            data = self.q15.get()
            data = data['data']
            self.pause_button(0)
            self.full_auto_checks(data['stpt'],data['mode'])
        if not self.q16.empty(): # full auto checks
            data = self.q16.get()
            self.full_auto_checks(data['data'])
        if not self.q17.empty(): # web in_full_auto_cal
            data = self.q17.get()
            self.full_auto_cal(data['data'])
        if not self.q18.empty(): # web skip point
            data = self.q18.get()
            self.pause_button(0)
            self.skip_point = int(data['data'])
        if not self.q19.empty(): # web low control
            data = self.q19.get()
            #self.cprint(data)
            data = int(data['data'])
            self.Mc.low_ctrl(data,self.ref_SP_actual)

        if not self.q21.empty(): # serial_worker stop_pid
            data = self.q21.get()
            self.stop_pid(data['data'])
        if not self.q23.empty(): # web psi_pid_start_stop
            data = self.q23.get()
        if not self.q24.empty(): # manual control
            data = self.q24.get()
            self.manual_control(data['data'])
        if not self.q25.empty(): # kpv mod request from another process
            data = self.q25.get()
            row = data['row']
            val = data['val']
            self.Mc.mod_kpv_file_entry(row, val)
            self.init_kpv_to_val(row,val)
            self.Mc.init_kpv_to_val(row,val)
        if not self.q26.empty(): # rest motors
            data = self.q26.get()
            self.check_adj = 0
            self.Mc.rest_motors()
        if not self.q27.empty(): # start button
            data = self.q27.get()
            self.cprint(data)
            self.start_button(data)
        if not self.q28.empty(): # stop button
            data = self.q28.get()
            self.stop_button(1)
        if not self.q29.empty(): # pause button
            data = self.q29.get()
            self.pause_button(int(data['data']))
        if not self.q30.empty(): # zero inlet
            data = self.q30.get()
            self.zero_inlet(int(data['data']))
        if not self.q31.empty(): # zero outlet
            data = self.q31.get()
            self.zero_outlet(int(data['data']))
        if not self.q32.empty(): # heartbeat received
            data = self.q32.get()
            self.hb_st = time.time() # reset heartbeat timer
            if self.hb_restarts > 0:
                None
                #self.cprint("Program restart successful")
            self.hb_restarts = 0
            #self.cprint("hb:%s"%data['data'])
        if not self.q34.empty(): # ROC button
            self.cprint("Number of markers modified")
            data = self.q34.get()
            self.unit_type = int(data['data'])
            if self.unit_type == 0:
                self.cprint("Number of markers set to 1")
                self.num_markers = 1
                self.Mc.num_markers = 1
                self.Mc.mod_kpv_file_entry(246,0)
                self.Mc.mod_kpv_file_entry(131,2)
            if self.unit_type == 1:
                self.cprint("Number of markers set to 1")
                self.num_markers = 1
                self.Mc.num_markers = 1
                self.Mc.mod_kpv_file_entry(246,1)
                self.Mc.mod_kpv_file_entry(131,1)
            #print("unit_type : %s", self.unit_type)
            #print("self.num_markers : %s", self.num_markers)
            #print("self.Mc.num_markers : %s", self.Mc.num_markers)
        if not self.q36.empty(): # web command to send a marker via comm
            data = self.q36.get()
            data = data['data']
            self.send_marker(data)
        if not self.q37.empty(): # full test (SPDPTP auto)
            data = self.q37.get()
            data = int(data['data'])
            if data == 0:
                if self.full_test_active == 1:
                    self.send_web_message("stopping full test")
                    self.meter_hold_command(0)
                    self.full_test_active = 0
            fts =  self.full_test_command(data) # returns true on successful test
            if fts != True:
                self.cprint("stopping full test",0,1)
            if fts == False: # full test failed
                self.meter_hold_command(0)
                self.stop_button(0)
                self.full_test_active = 0
            elif fts == 'meter_connection_fail': # don't attempt hold command
                self.stop_button(0)
                self.full_test_active = 0

        if not self.q38.empty(): # returned data_read_reg
            data = self.q38.get()
            self.meter_data_received = data

        if not self.q39.empty(): # re-center command from analog_in.py
            self.set_rough_fine(0) # switch to rough
            data = self.q39.get()
            direction = data['direction']
            if direction == 'out':
                self.cprint("Adjuster max inward travel reached - re-centering",1,1)
                self.adj_centering_start_pos = abs(self.Mc.adj_pos)
                self.adj_centering_in_progress = 1
                self.manual_control('-1')
            elif direction == 'in':
                self.cprint("Adjuster max outward travel reached - re-centering",1,1)
                self.adj_centering_start_pos = abs(self.Mc.adj_pos)
                self.adj_centering_in_progress = 1
                self.manual_control('1')
            elif direction == 'centered':
                self.cprint('Adjuster centered via center beam sensor',1,1)
                self.adj_centering_in_progress = 0
                self.Mc.adj_pos = 0
                self.Mc.update_adj_pos_display()
                self.mq(self.qa3,{'centering_status':'beam_passed'})
                self.manual_control('0')
                
        if not self.q40.empty(): # returned meter_write_reg status code
            data = self.q40.get()
            #self.cprint("self.q40 data received - meter write reg / status code : %s"%data)
            self.meter_write_status = data

        if not self.q41.empty(): # baro lock button
            data = self.q41.get('data')
            #self.cprint("self.q41 data received - meter write reg / status code : %s"%data)
            self.baro_lock_button(data)

        if not self.q42.empty(): # zero adjuster position based on center beam sensor
            data = self.q42.get()
            self.Mc.adj_pos = 0
            self.Mc.update_adj_pos_display()
            
        # settings.py queue
        if not self.qk1.empty(): # request from web for kpv file
            data = self.qk1.get()
            self.Mc.get_kpv_file()
            self.Mc.send_kpv('init_web')
        if not self.qk3.empty(): # change made to kpv on web
            data = self.qk3.get()
            data = data['data']
            row = int(data['row'])
            #self.cprint(row)
            dtype = self.Mc.KpvTypes[row]
            if dtype == 'i':
                val = int(data['val'])
            elif dtype == 'f':
                val = float(data['val'])
            elif dtype == 's':
                val = str(data['val']).replace("\n","")
            else:
                self.cprint("Bad data type imported from web settings page")
            #self.cprint("Change made to web Kpv[%s]  old : %s  new : %s  type : %s"%(row, self.Mc.Kpv[row],val,type(val)))
            #self.cprint("cntrl.py 1569  row : %s   val : %s"%(row, val))
            self.Mc.mod_kpv_file_entry(row, val)
            self.init_kpv_to_val(row,val)
            self.Mc.init_kpv_to_val(row,val)

        # motor_current.py queue
        if not self.qm7.empty(): # send kpv list from motor_current.py to cntrl
            self.Mc.Kpv = self.qm7.get()

        if not self.qw12.empty(): # NA
            data = self.qw12.get()
            msg = data['data']
            #self.cprint(msg)
            #self.save_msg_log(msg)

        if not self.qb2.empty(): # baro psi for cntrl.py
            data = self.qb2.get()
            if data['data'] != 'good':
                self.ref_baro_current = False
            else:
                self.ref_baro_current = True
                self.baro_psi = float(data['baro_psi'])

        if not self.qtd5.empty(): # meter dpsptp for cntrl.py
            data = self.qtd5.get()
            if data['data'] != 'good':
                self.meter_DPSPTP_current = False
            else:
                self.meter_DPSPTP_current = True
                self.meter_DP_actual = float(data['meter_in_num'])
                self.meter_SP_actual = float(data['meter_psi_num'])
                self.meter_TP_actual = float(data['meter_temp'])

        if not self.qs7.empty(): # reference dpsp
            data = self.qs7.get()
            if data['data'] != 'good':
                self.ref_DPSP_current = False
            else:
                self.ref_DPSP_current = True
                self.ref_DP_actual = float(data['ref_in_num'])
                self.ref_SP_actual = float(data['ref_psi_num'])

        if not self.q20.empty(): # reference tp
            data = self.q20.get()
            if data['data'] != 'good':
                self.ref_TP_current = False
            else:
                self.ref_TP_current = True
                self.ref_TP_actual = float(data['temp'])

        # update status indicator if necessary
        if self.full_test_active != self.status_change[0] or \
           self.pid_run != self.status_change[1] or \
           self.pid_pause != self.status_change[2] or \
           time.time() - self.status_ind_st > 10: # periodically update status indicator
            self.status_ind_st = time.time()
            self.mq(self.qw37,{'dest':'status indicator','full_test_active':self.full_test_active,'test_active':self.pid_run,'pause':self.pid_pause}) # status indicator
        self.status_change=[self.full_test_active,self.pid_run,self.pid_pause]
        
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

    def run(self):
        #self.cprint("cntrl.py running")
        self.Mc = Pid_class(self.q24, self.q25, self.q26, self.q28, self.qw3, self.qw4, self.qw11, self.qw12, self.qw13, self.qw14, self.qw15, \
        self.qw16, self.qw21, self.qw22, self.qw23, self.qw24, self.qw25, self.qw26, self.qw27, self.qw28, \
        self.qw30, self.qw31, self.qw32, self.qw33, self.qw34, self.qw35, self.qw36, self.qw37,\
        self.qw38, self.qw39, self.qw40, self.qm1, self.qm2, self.qm3, self.qm4, self.qm6, self.qm7, self.qs1, \
        self.qs2, self.qs3, self.qs9, self.qs10, self.qs11, self.qk2, self.qk4, self.qt4, self.qtd4, self.qb1, self.qb3, self.qa1, self.qa2, self.qa3, self.qa4, \
        self.qu1, self.qu3, self.qts1, self.qv3, self.qd1, self.qd2)  # pid object

        self.Mc.get_kpv_file()
        self.Mc.print_duty()
        while len(self.Mc.Kpv) == 0:
            #self.cprint("waiting %s"%time.time())
            None
        self.init_kpv_to_val('init')
        self.Mc.rest_motors()

        self.check_input(0)
        while True: #self.pid_run == 0:
            try:
                #print("cntrl.py  %s"%time.time())
                if time.time() - self.save_st > self.save_dt:
                    self.save_st = time.time()
                    self.save_all(0)
                    #if abs(self.Mc.adj_pos) > self.adj_max_pos + 200:
                    #    self.cprint("Adjuster max position reached")
                    #    self.send_web_message("Adjuster max position reached")
                    #    self.Mc.center_in_adjuster()
                if time.time() - self.ck_hb_st > 1: # check every second
                    self.check_heartbeat()
                    self.ck_hb_st = time.time()
                if self.web_running == 0 and time.time() - self.initial_web_update_st > self.web_dt:
                    self.initial_web_update_st = time.time()
                    self.ping_web() # see if ui is connected yet
                self.check_input(0)
            except:
                raise
            time.sleep(0.05)
        time.sleep(0.05)



class Pid_class(Controls): # pid class

    def __init__(self, q24, q25, q26, q28, qw3, qw4, qw11, qw12, qw13, qw14, qw15, qw16, qw21, qw22, qw23, \
                       qw24, qw25, qw26, qw27, qw28, qw30, qw31, qw32, qw33, qw34, \
                       qw35, qw36, qw37, qw38, qw39, qw40, qm1, qm2, qm3, qm4, qm6, qm7, qs1, \
                       qs2, qs3, qs9, qs10, qs11, qk2, qk4, qt4, qtd4, qb1, qb3, qa1, qa2, qa3, qa4, qu1, qu3, qts1, qv3, \
                       qd1, qd2):


        self.kpv_vars_list = ['s0_Kp_psi',            's0_Ki_psi',           's0_Kd_psi',            's1_Kp_psi',           \
                              's1_Ki_psi',            's1_Kd_psi',           's2_Kp_psi',            's2_Ki_psi',           \
                              's2_Kd_psi',            'm3_Kp',               'm3_Ki',                'm3_Kd',               \
                              'm4_Kp',                'm4_Ki',               'm4_Kd',                'adjuster_runout',     \
                              'adj_min_move_amp',     's0_min_angle_in',     's0_manual_pw',         's0_move_min',         \
                              's0_move_close_max',    's0_move_open_max',    's0_max_intg_psi',      's0_soak',             \
                              's0_min_angle_psi',     's0_max_angle',        's0_pw_holdoff',        's0_intg_holdoff_psi', \
                              's0_default_angle',     's0_init_angle_psi',   's0_init_angle_in',     's0_intg_holdoff_in',  \
                              's0_max_intg_in',       's1_move_min',         's1_move_close_max',    's1_max_intg_psi',     \
                              's1_soak',              's1_min_angle',        's1_max_angle',         's1_pw_holdoff',       \
                              's1_move_open_max_psi', 's1_default_angle',    's1_init_angle_psi',    's1_move_open_max_in', \
                              's1_init_angle_in',     's1_manual_pw',        's1_intg_holdoff_psi',  's1_intg_holdoff_in',  \
                              's2_min',               's2_max',              's2_max_intg_psi',      's2_soak',             \
                              's2_intg_holdoff_psi',  's2_intg_holdoff_in',  's2_max_intg_in',       's2_up_spd',           \
                              's2_down_spd',          's2_up_spd_max',       's2_down_spd_min',      's2_up_spd_min',       \
                              's2_down_spd_max',      'm2_level',            'm3_min',               'm3_max',              \
                              'm3_max_intg',          'm3_soak',             'm3_level',             'm3_manual_pw',        \
                              'm2_min',               'm2_max',              'm4_soak',                                     \
                              'm4_level_min',         'm4_level_max',        'm4_off_delay',         'm5_min',              \
                              'm5_max',               'm6_min',              'm6_max',               'num_markers',         \
                              'avg_pw_count',         'cycles_per_div_ST',   'cycles_per_div_LT',    'open_low_safe_psi',  's0_Kp_in',            \
                              's0_Ki_in',             's0_Kd_in',            's1_Kp_in',             's1_Ki_in',            \
                              's1_Kd_in',             's2_Kp_in',            's2_Ki_in',             's2_Kd_in'  ]

        self.kpv_index_list = [  0,   1,   2,   4,
                                 5,   6,   8,   9,
                                 10,  12,  13,  14,
                                 16,  17,  18,  25,
                                 26,  32,  33,  34,
                                 35,  36,  37,  38,
                                 39,  40,  41,  42,
                                 43,  44,  45,  46,
                                 47,  49,  50,  51,
                                 52,  53,  54,  55,
                                 56,  57,  58,  59,
                                 60,  61,  63,  64,
                                 69,  70,  71,  72,
                                 73,  74,  75,  76,
                                 77,  78,  79,  80,
                                 81,  87,  92,  93,
                                 94,  95,  96,  97,
                                 102, 103, 105,
                                 107, 108, 111, 116,
                                 117, 124, 125, 131,
                                 156, 158, 161, 203, 292,
                                 293, 294, 295, 296,
                                 297, 298, 299, 300  ]

        self.KpvTypes = []
        self.q24 = q24 # web manual_control
        self.q25 = q25 # send kpv from py processes to cntrl.py
        self.q26 = q26 # rest motors
        self.q28 = q28 # stop button

        self.qw4 = qw4 # temp readings from USB485.py
        self.qw3 = qw3 # inlet_display
        self.qw11 = qw11 # NA
        self.qw12 = qw12 # NA
        self.qw13 = qw13 # eq_status
        self.qw14 = qw14 # outlet_status
        self.qw15 = qw15 # adj_pos_display
        self.qw16 = qw16 # stpt_display
        self.qw21 = qw21 # send_web_message for cntrl.py
        self.qw23 = qw23 # send_web_message for serialworker.py
        self.qw24 = qw24 # btn_status
        self.qw25 = qw25 # pid_running_status
        self.qw26 = qw26 # beam indicators
        self.qw27 = qw27 # disable clear crystal alarm button
        self.qw28 = qw28 # ROC button
        self.qw30 = qw30 # send_web_message for meter_serial.py
        self.qw31 = qw31 # send_web_message for meter_tcp.py
        self.qw32 = qw32 # send_web_message for ssh.py
        self.qw33 = qw33 # sounds
        self.qw34 = qw34 # next/prev button enable/disable
        self.qw35 = qw35 # send_web_message for analog_in.py
        self.qw36 = qw36 # NA
        self.qw37 = qw37 # status indicator
        self.qw38 = qw38 # NA
        self.qw39 = qw39 # NA
        self.qw40 = qw40 # NA

        self.qm1 = qm1 # motor_current.py motor direction
        self.qm2 = qm2 # motor_current.py adjuster position
        self.qm3 = qm3 # motor_current.py re-center active
        self.qm6 = qm6 # send kpv list to motor_current.py
        self.qm4 = qm4 # constant ma alarm checking
        self.qs1 = qs1 # cntrl.py eq_status
        self.qs2 = qs2 # cntrl.py vent_status
        self.qs3 = qs3 # cntrl.py   in_vent_status
        self.qs9 = qs9 # send auto_pid mode to serialworker
        self.qs10 = qs10 # send kpv file to serialworker.py
        self.qs11 = qs11 # serial worker dp high during SP testing
        self.qts1 = qts1 # send kpv list to meter_serial.py

        self.qk2 = qk2 # send kpv to settings.py
        self.qk4 = qk4 # change made to kpv update web

        self.qt4 = qt4 # send kpv file to meter_tcp_rw.py

        self.qtd4 = qtd4 # send kpv file to meter_tcp_dpsptp.py

        self.qb1 = qb1 # baro set status for baro_data.py
        self.qb3 = qb3 # send kpv file to baro_data.py

        self.qa1 = qa1 # send kpv file to analog_in.py
        self.qa2 = qa2 # send adjuster position to analog_in.py
        self.qa3 = qa3  # re-center complete from cntrl.py
        self.qa4 = qa4 # re-center command from cntrl to analog in

        self.qu1 = qu1 # temp set status for baro_data.py
        self.qu3 = qu3 # send kpv file to usb485.py

        self.qts1 = qts1 # send kpv list to meter_serial.py

        self.qv3  = qv3 # kpv for activity.py

        self.qd1 = qd1 # write to db
        self.qd2 = qd2 # read from db

        self.prev_msg = ""
        self.Kpv = []
        self.KpvTypes = [] # array to hold 'types' of data in Kpv

        self.get_kpv_file()
        self.init_kpv_to_val('init')
        self.send_kpv('init')

        self.web_prev_msg = ""
        self.prev_msg = ""

        self.adjuster_direction = 0

        self.avg_pw_array = []
        for i in range(int(self.avg_pw_count)): # set up derivative average array
            self.avg_pw_array.append(0)
        self.avg_pw = sum(self.avg_pw_array) / len(self.avg_pw_array) # average derivative ofer a number of cycles

        self.get_adj_pos_value()
        self.prev_adj_pos = 0

        self.inhibit_up = 0
        self.inhibit_down = 0


    def get_kpv_file(self):
        self.Kpv = []
        self.KpvTypes = []
        self.KpvTags = []
        try:
            self.dbq_kpv_tags = db.get("SELECT * FROM kpv where user = 'tags'")
        except:
            cprint("kpv tags database did not read in")
        else:
            try:
                self.dbq_kpv_vals = db.get("SELECT * FROM kpv where user = 'default_user'")
            except:
                cprint("kpv vals database did not read in")
            else:
                for i in range(len(self.dbq_kpv_tags)-1):
                    fullstr = str(self.dbq_kpv_tags['row' + str(i)])
                    self.KpvTypes.append(str(fullstr[1]))
                    self.KpvTags.append(fullstr[3:len(fullstr)])
                    val = self.dbq_kpv_vals['row' + str(i)]
                    dtype = self.KpvTypes[i]
                    if dtype == 'i':
                        self.Kpv.append(int(val))
                    elif dtype == 'f':
                        self.Kpv.append(float(val))
                    elif dtype == 's':
                        self.Kpv.append(str(val))
                    else:
                        self.cprint("Unknown data type imported from Kpv database")
                    #print("[%s]{%s}(%s) : %s"%(i,self.KpvTags[i],self.KpvTypes[i],self.Kpv[i]))

    def mod_kpv_file_entry(self, index, val):
        #self.cprint("mod kpv file entry ([%s]:%s)1864"%(index,val))
        db.execute("update kpv set `row" + str(index) + "` = '" + str(val) + "' where user = 'default_user';")
        self.Kpv[index] = val # update local process kpv entry
        self.send_kpv(index, val) # send new kpv to web and processes

    def send_kpv(self, index = 0, val = 0): # send kpv settings to web settings page
        #self.cprint("send_kpv  index : %s  val : %s"%(index,val))
        if index == 'init_web':
            self.mq(self.qk2,  [self.Kpv, self.KpvTypes, self.KpvTags]) # send kpv to web
        elif index == 'init':
            self.mq(self.qs10, [self.Kpv, self.KpvTypes]) # update kpv in serialworker.py
            self.mq(self.qt4,  [self.Kpv, self.KpvTypes]) # update kpv in meter_tcp_rw.py
            self.mq(self.qtd4,  [self.Kpv, self.KpvTypes]) # update kpv in meter_tcp_dpsptp.py
            self.mq(self.qts1, [self.Kpv, self.KpvTypes]) # update kpv in meter_serial.py
            self.mq(self.qb3,  [self.Kpv, self.KpvTypes]) # update kpv in baro_data.py
            self.mq(self.qm6,  [self.Kpv, self.KpvTypes]) # update kpv in motor_current.py
            self.mq(self.qa1,  [self.Kpv, self.KpvTypes]) # update kpv in analog_in.py
            self.mq(self.qu3,  [self.Kpv, self.KpvTypes]) # update kpv in usb485.py
            self.mq(self.qv3,  [self.Kpv, self.KpvTypes]) # update kpv in activity.py
        else:
            self.mq(self.qk4,  [index,val]) # change made to kpv - update web
            self.mq(self.qs10, [index,val]) # update kpv in serialworker.py
            self.mq(self.qt4,  [index,val]) # update kpv in meter_tcp_rw.py
            self.mq(self.qtd4,  [index,val]) # update kpv in meter_tcp_rw.py
            self.mq(self.qts1, [index,val]) # update kpv in meter_serial.py
            self.mq(self.qb3,  [index,val]) # update kpv in baro_data.py
            self.mq(self.qm6,  [index,val]) # update kpv in motor_current.py
            self.mq(self.qa1,  [index,val]) # update kpv in analog_in.py
            self.mq(self.qu3,  [index,val]) # update kpv in usb485.py
            self.mq(self.qv3,  [index,val]) # update kpv in activity.py

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

        self.m3_rng = self.m3_max - self.m3_min
        self.m3_soak_scaled = self.m3_soak
        self.m3_pw = self.m3_min
        self.m4_max = self.m2_max
        self.m4_min = self.m2_min
        self.m4_rng = self.m4_max - self.m4_min
        self.m4_soak_scaled = self.m4_soak
        self.m4_soak_default = self.m4_soak
        self.m4_level_rng = self.m4_level_max - self.m4_level_min
        self.m4_pw = self.m4_min
        self.m5_rng = self.m5_max - self.m5_min
        self.m6_rng = self.m6_max - self.m6_min
        self.s0_angle_range = self.s0_max_angle - self.s0_min_angle_psi
        self.s0_move_close_range = self.s0_move_close_max - self.s0_move_min
        self.s0_move_open_range = self.s0_move_open_max - self.s0_move_min
        self.s0_prev_angle = 0
        self.s0_max_angle_prev = self.s0_max_angle
        self.s1_move_close_range = self.s1_move_close_max - self.s1_move_min
        self.s1_move_open_range_psi = self.s1_move_open_max_psi - self.s1_move_min
        self.s1_move_open_range_in = self.s1_move_open_max_in - self.s1_move_min
        self.s1_prev_angle = 0
        self.s1_max_intg_in = self.s1_max_intg_psi
        self.s1_max_angle_prev = self.s1_max_angle
        self.s2_soak_scaled = self.s2_soak
        self.s2_rng = self.s2_max - self.s2_min
        self.s2_pw = self.s2_min
        self.s2_nonstop = self.m3_manual_pw

        self.prev_eq_status = -1
        self.prev_vent_status = -1
        self.prev_in_vent_status = -1

        self.cycle_reset_time_ST = self.cycles_per_div_ST
        self.cycle_reset_time_LT = self.cycles_per_div_LT

    def cprint(self, msg = "",printout = True, web = False, lvl = 'i'):
        if (printout or lvl == None) and msg != self.prev_msg:
            print("%s  (ctrl%s)  %s"%(msg,inspect.currentframe().f_back.f_lineno, time.time()))
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

    def center_in_adjuster(self):
        #self.cprint("center_in_adjuster")
        #self.cprint("adj_pos : %s"%self.Mc.adj_pos,1,1)
        self.mq(self.qa4,{'purpose':'re-center'})
        '''
        if self.Mc.adj_pos > 0:
            self.manual_control(-1)
            #spd = self.s2_down_spd
        else:
            self.manual_control(1)
            #spd = self.s2_up_spd
        move = abs(self.Mc.adj_pos)
        if move > self.adjuster_runout:
            move = self.adjuster_runout
        self.s2(spd, move)
        '''

    def check_ma(self):
        #getframe_expr = 'sys._getframe({}).f_code.co_name'
        #self.cprint("check_ma called by %s"%eval(getframe_expr.format(2)))
        cont = 1
        if not self.qm4.empty():
            try:
                data = self.qm4.get()
                if data['purpose'] == 'stop':
                    self.rest_motors()
                    send_web_message("Max ma - Adjuster  stopped")
                    cont = 0
                    return cont
                if data['purpose'] == 'inhibit_up':
                    self.inhibit_up = int(data['data'])
                if data['purpose'] == 'inhibit_down':
                    self.inhibit_down = int(data['data'])
            except:
                self.cprint("exception at check_ma")
                cont = 0
                return cont
        return cont

    def check_stop(self):
        if not self.q28.empty():
            return False
        else:
            return True

    def get_adj_pos_value(self):
        self.get_kpv_file()
        self.adj_pos = float(self.Kpv[82])
        return self.adj_pos

    def m1(self, spd): # manifold_top
        if spd == 0:
            spd = None
        kit.motor1.throttle = spd

    def m2(self, spd): # manifold_equalize
        if spd == 0:
            spd = None
        kit.motor2.throttle = spd

    def m3(self, spd): # manifold_bottom
        if spd == 0:
            spd = None
        kit.motor3.throttle = spd

    def m4(self, spd): # expose reference DP port
        #self.cprint("m4 spd : %s"%spd)
        if spd == 0 or spd == None:
            spd = None
            self.web_btn_status('close_low','1')
        else:
            self.web_btn_status('open_low','1')            
        kit.motor4.throttle = spd
        #Dict = {'dest':'qs8', 'purpose':'low_status', 'data':self.get_pwm_state(4,1)}
        #self.mq(self.qs8,Dict)        

    def m5(self, spd): # equalizer
        #self.cprint("equalizer called by %s"%eval(getframe_expr.format(2)))
        if spd == 0 or spd == None:
            self.web_btn_status('open_eq','1')
        else:
            self.web_btn_status('close_eq','1')
        if spd == 0 or spd == None:
            spd = 0
        p_kit.motor1.throttle = spd
        # eq status for serialworker
        Dict = {'dest':'qs1', 'purpose':'eq_status', 'data':self.get_pwm_state(5,1)}
        self.mq(self.qs1, Dict)

    def m6(self, spd): # psi vent
        #self.cprint("psi vent called by %s"%eval(getframe_expr.format(2)))
        if spd == 0 or spd == None:
            self.web_btn_status('close_vent','1')
        else:
            self.web_btn_status('open_vent','1')
        p_kit.motor2.throttle = spd
        # psi vent status for serialworker
        Dict = {'dest':'qs2', 'purpose':'vent_status', 'data':self.get_pwm_state(6,1)}
        self.mq(self.qs2,Dict)

    def m7(self, spd): # NA
        if spd == 0:
            spd = None
        kit.motor3.throttle = spd

    def m8(self, spd): # NA
        if spd == 0:
            spd = None
        kit.motor4.throttle = spd

    def s0(self, angle, mode='i'): # inlet servo
        getframe_expr = 'sys._getframe({}).f_code.co_name'
        #print("s0 called by %s"%eval(getframe_expr.format(2)))
        if mode == 'p' or mode == 'm':
            min_angle = self.s0_min_angle_psi
        elif mode == 'i':
            min_angle = self.s0_min_angle_in
        if angle  < 0:
            self.web_btn_status('inlet_bump_up','1')
        elif angle  > 0:
            self.web_btn_status('inlet_bump_down','1')
        fpos = s_kit.servo[0].angle + angle
        if fpos > self.s0_max_angle:
            self.s0_commanded = self.s0_max_angle
            #s_kit.servo[0].angle = self.s0_max_angle
        elif fpos < min_angle:
            self.s0_commanded = min_angle
            #s_kit.servo[0].angle = min_angle
        else:
            self.s0_commanded = fpos
            #s_kit.servo[0].angle = fpos

        # set servo position
        s_kit.servo[0].angle = self.s0_commanded

        if angle  < 0:
            self.web_btn_status('inlet_bump_up','0')
        elif angle  > 0:
            self.web_btn_status('inlet_bump_down','0')
        # web inlet position display
        state = s_kit.servo[0].angle
        Dict = {'dest':'inlet_display', 'inlet_angle':str(int(state))}
        self.mq(self.qw3, Dict)

    def s1(self, angle): # outlet servo
        #self.cprint("s1 called by %s"%eval(getframe_expr.format(2)))
        #self.cprint('s1 angle called : %s'%angle)
        if angle  < 0:
            self.web_btn_status('outlet_bump_up','1')
        elif angle  > 0:
            self.web_btn_status('outlet_bump_down','1')
        #fpos = s_kit.servo[1].angle + angle
        fpos = s_kit.servo[3].angle + angle
        #self.cprint(fpos)
        if fpos > self.s1_max_angle:
            self.s1_commanded = self.s1_max_angle
            #s_kit.servo[1].angle = self.s1_max_angle
            #s_kit.servo[3].angle = self.s1_max_angle
        elif fpos < self.s1_min_angle:
            self.s1_commanded = self.s1_min_angle
            #s_kit.servo[1].angle = self.s1_min_angle
            #s_kit.servo[3].angle = self.s1_min_angle
        else:
            self.s1_commanded = fpos
            #s_kit.servo[1].angle = fpos
            #s_kit.servo[3].angle = fpos
        if angle  < 0:
            self.web_btn_status('outlet_bump_up','0')
        elif angle  > 0:
            self.web_btn_status('outlet_bump_down','0')

        # set servo position
        #s_kit.servo[1].angle = self.s1_commanded
        #self.cprint("self.s1_commanded : %s"%self.s1_commanded)
        s_kit.servo[3].angle = self.s1_commanded

        # web outlet position display
        #state = s_kit.servo[1].angle
        state = s_kit.servo[3].angle
        #self.cprint(state)
        Dict = {'dest':'outlet_display', 'outlet_angle':str(int(state))}
        self.mq(self.qw14, Dict)

    def s2(self, spd, pw): # adjuster continuous servo
        #self.cprint("s2 pw : %s"%pw)
        #self.cprint("s2 spd : %s"%spd)
        #getframe_expr = 'sys._getframe({}).f_code.co_name'
        #self.cprint("s2 called by %s"%eval(getframe_expr.format(2)))
        btn_on = 0
        if spd == 0 or spd == None: #allows for soak time
            pass
        if pw <0:
            pw = 0
        if pw > self.adjuster_runout:
            pw = self.adjuster_runout
        self.prev_adjuster_direction = self.adjuster_direction
        if spd != None and spd != 0:
            btn_on = 1
            if spd > 0:
                self.web_btn_status('fine_up','1')
            elif spd < 0:
                self.web_btn_status('fine_down','1')
            else:
                self.web_btn_status('fine_up','0')
                self.web_btn_status('fine_down','0')
        cl = 1
        ca = 1
        if spd > 0 and self.inhibit_up == 1 or \
           spd < 0 and self.inhibit_down == 1:
            spd = 0
            cl = 0
        s_kit.continuous_servo[2].throttle = spd
        if spd != None and spd != 0:
            self.adjuster_direction = (spd/abs(spd))
            self.mq(self.qm1, self.adjuster_direction)
        st = time.time()
        while cl == 1:
            dt = time.time() - st
            cl = self.check_ma()
            if cl == 1:
                cl = self.check_stop()
            if cl == False:
                ca = 0
                break
            if dt > pw / 1000:
                cl = 0
                break
        s_kit.continuous_servo[2].throttle = 0
        if btn_on == 1:
            if spd > 0:
                self.web_btn_status('fine_up','0')
            elif spd < 0:
                self.web_btn_status('fine_down','0')

        if spd != None and spd != 0:
            if pw != self.adjuster_runout:
                self.adj_pos = self.adj_pos + ((spd/abs(spd)) * ((time.time() - st) * 1000))
                self.update_adj_pos_display()
            '''
            elif pw == self.adjuster_runout and centered == False:
                self.adj_pos = 0
                self.update_adj_pos_display()
                self.mq(self.qm3, 0) # motor_current.py re-center active
                self.mq(self.qa3,{'purpose':'re_center_complete'}) # re-center complete for analog_in.py
                self.mq(self.q24,{'data':'0'}) # if adjuster was manually set to run continuously, stop after re-center

        if centered == True:
            self.adj_pos = 0
            self.update_adj_pos_display()
        '''

        self.mq(self.qm2, self.adj_pos) # send adjuster position to motor_current.py
        self.mq(self.qa2, {'position':self.adj_pos,'direction':self.adjuster_direction}) # send adjuster position to analog_in.py
        return ca

    def rest_motors(self):
        #getframe_expr = 'sys._getframe({}).f_code.co_name'
        #self.cprint("rest_motors called by %s"%eval(getframe_expr.format(2)))
        self.m4(None)
        self.m5(None)
        self.m6(None)
        self.s0(self.s0_max_angle)
        #self.cprint('close s1 called in rest motors : %s'%self.s1_max_angle)
        self.s1(self.s1_max_angle)
        self.s2(0,0)

    def equalizer_ctrl(self, val):
        if val == 1: # close the equalizer
            self.m5(0.9)
        else:
            self.m5(None)

    def vent_ctrl(self, val): # psi vent
        if val == 1:
            self.m6(1)
        elif val == 0:
            self.m6(None)

    def low_ctrl(self, val, sp = 0): # expose DP reference
        state = self.get_pwm_state(4,1)
        if state == val:
            return 1
        if state == 0 and val == 1:
            if sp < self.open_low_safe_psi:
                self.m4(1)
                return 1
            else:
                self.cprint('Unsafe to open reference DP solenoid - high PSI',1,1)
                return 0
        elif val == 0 or val == None:
            self.m4(None)

    def web_btn_status(self,btn,state):
        Dict = {'dest':'btn_status','btn':btn,'state':state}
        self.mq(self.qw24,Dict)


    def send_web_message(self, var):
        if var != self.web_prev_msg:
            Dict = {'dest':'web_message', 'val':var}
            self.qw21.put(Dict)
            self.web_prev_msg = var

    def init_web_valve_states(self): # show correct state of buttons on web
        st = self.get_pwm_state(5)
        if st == None or st == 0:
            self.web_btn_status('open_eq','1')
        else:
            self.web_btn_status('close_eq','1')

        st = self.get_pwm_state(6)
        if st == None or st == 0:
            self.web_btn_status('close_vent','1')
        else:
            self.web_btn_status('open_vent','1')
        st = self.get_pwm_state(4)
        if st == None or st == 0:
            self.web_btn_status('close_low','1')
        else:
            self.web_btn_status('open_low','1')            

    def get_pwm_state(self,m, rv = 0):
        # get duty_cycle from pwm pins
        if m == 1 or m == 5:
            p1 = 9
            p2 = 10
            if m == 1:
                p1 = kit._pca.channels[p1].duty_cycle
                p2 = kit._pca.channels[p2].duty_cycle
            elif m == 5:
                p1 = p_kit._pca.channels[p1].duty_cycle
                p2 = p_kit._pca.channels[p2].duty_cycle
        elif m == 2 or m == 6:
            p1 = 11
            p2 = 12
            if m == 2:
                p1 = kit._pca.channels[p1].duty_cycle
                p2 = kit._pca.channels[p2].duty_cycle
            elif m == 6:
                p1 = p_kit._pca.channels[p1].duty_cycle
                p2 = p_kit._pca.channels[p2].duty_cycle
        elif m == 3 or m == 7:
            p1 = 3
            p2 = 4
            if m == 3:
                p1 = kit._pca.channels[p1].duty_cycle
                p2 = kit._pca.channels[p2].duty_cycle
            elif m == 7:
                p1 = p_kit._pca.channels[p1].duty_cycle
                p2 = p_kit._pca.channels[p2].duty_cycle
        elif m == 4 or m == 8:
            p1 = 5
            p2 = 6
            if m == 4:
                p1 = kit._pca.channels[p1].duty_cycle
                p2 = kit._pca.channels[p2].duty_cycle
            elif m == 8:
                p1 = p_kit._pca.channels[p1].duty_cycle
                p2 = p_kit._pca.channels[p2].duty_cycle
        else:
            return(0)

        # determine pwm direction
        if p1 == p2 == 0: # None
            if rv != 0:
                return 0
            else:
                return None
        elif p1 > 0 and p2 > 0: # 0
            return(0)
        elif p1 == 0 and p2 > 0:
            if rv != 0:
                return 1
            else:
                return(-1)
        elif p1 > 0 and p2 == 0:
            return(1)

    def print_duty(self):
        None
        #self.cprint("\n")
        #print("m1 dir : %s\n"%self.get_pwm_state(1))
        #print("m2 dir : %s\n"%self.get_pwm_state(2))
        #print("m3 dir : %s\n"%self.get_pwm_state(3))
        #print("m4 dir : %s\n"%self.get_pwm_state(4))
        #print("m5 dir : %s\n"%self.get_pwm_state(5))
        #print("m6 dir : %s\n"%self.get_pwm_state(6))
        #print("m7 dir : %s\n"%self.get_pwm_state(7))
        #print("m8 dir : %s\n"%self.get_pwm_state(8))

    def update_adj_pos_display(self):
        if abs(self.adj_pos - self.prev_adj_pos) > 50:
            Dict = {'dest':'adj_pos_display', 'adj_pos':str(int(self.adj_pos))}
            self.mq(self.qw15, Dict)
            self.prev_adj_pos = self.adj_pos
            self.mod_kpv_file_entry(82, self.adj_pos)

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
