$(document).ready(function(){

  window.user_activity_time = (new Date().getTime())/1000
  window.check_activity_sec = 5
  window.addEventListener("mousemove",user_activity);
  window.srvr_ip = '192.168.42.1';
  window.srvr_port = '10120'
  window.base_addr = 'http://' + srvr_ip + ':' + srvr_port;
  var socket = new WebSocket("ws://" + srvr_ip + ":" + srvr_port + "/ws/controls");

  window.kpv_val=[]
  window.kpv_des=[]
  window.kpv_type=[]

  window.onbeforeunload = function(){
    logout_user = get_active_user()
    console.log('logging out user ' + logout_user)
    ajax_request({'purpose':'logout_window_close','user':logout_user})
  }
      
  var main_body = $("#main_body");
  var inch_readings = $("#inch_readings");
  var psi_readings = $("#psi_readings");
  var meter_inch_readings = $("#meter_inch_readings");
  var meter_psi_readings = $("#meter_psi_readings");
  var meter_temp_readings = $("#meter_temp_readings");
  var baro_readings = $("#baro_readings");
  var temp_readings = $("#temp_readings");
  var baro_rdg = $("#baro_rdg");
  var adj_pos_display = $("#adj_pos_display");
  var adj_ST_avg_display = $("#adj_ST_avg_display");
  var adj_LT_avg_display = $("#adj_LT_avg_display");
  var inlet_display = $("#inlet_display");
  var outlet_display = $("#outlet_display");
  var message_box = $("#message_box");
  var msg_log = ""; //copy of message box to save
  var open_eq=$("#open_eq");
  var close_eq=$("#close_eq");
  var readings_active = 0;
  var pid_running_count = 1;
  var hb = 0; // heartbeat signalbtn
  const Url = "lowpsical:";
  var adj_pos,eq_status,prev_eq_status,
      vent_status,prev_vent_status,dp_high_alarm,sp_high_alarm,inlet_angle,outlet_angle,psi_stpt,
      web_running,ap;
  var clr_green = "#00ff00";
  var clr_red = "#ff0000";
  var clr_yellow = "#ffff00";
  var clr_black = "#000000";
  var clr_beam_disabled = "#aaeeee";
  
  var clr_zero = "#D6E8F8"
  var clr_pid_cntrl = "#39b3ff"
  var clr_auto_dp = "#aee7f8"
  var clr_auto_psi = "#669cff"
  var clr_auto_marker = "#aee7f8"
  var clr_send_marker = "#b3f8ee"
  var clr_inlet_outlet = "#D6E8F8"
  var clr_rest = "#ae9dff"
  var clr_adjuster = "#669cff"
  var clr_eq = "#D6E8F8"
  var clr_vent = "#93d5f8"
  var clr_low = "#93d5f8"
  var clr_meter_tcp = "#23ffd3"
  var clr_crystal_alarm = "#aa55ff"
  
  kpv_val = []
  web_running = 0
  eq_status = -1;
  prev_eq_status = -1;
  vent_status = -1;
  prev_vent_status = -1;
  dp_high_alarm = 0;
  sp_high_alarm = 0;
  auto_sp_in_alarm = 0
  dp_high_alarm_display = 0;
  sp_high_alarm_display = 0;
  auto_sp_in_alarm_display = 0;
  
  ma_disp_pos_diff = 20; // above this value to post value to ma display
  prev_adj_ma = -1000;
  adj_max_ma = 0;
  prev_adj_max_ma = 0;
  adjuster_min_ma = 0;
  prev_adjuster_min_ma = 0;
  ma_post_diff = 0.1;
  minmax_post_diff = 40;
  post = 1; // post message to message window
  ap = "    ..";
  
  //var tpe
  document.getElementById("psi_stpt").value = "---";
  document.getElementById("inch_stpt").value = "---";

  window.meter_in_num = 'error'
  window.meter_psi_num = 'error'
  window.meter_temp = 'error'
  window.ref_in_num = 'error'
  window.ref_psi_num = 'error'
  window.ref_temp = 'error'
  window.baro_psi = 'error'

  var kpv_links_index = [241]
  var kpv_links_id = ['meter_ip_address']

  //fitty manipulates layout of text to fit in buttons correctly
  var fitties = fitty(".row_8");
  var fitties = fitty(".pid_table");
  
  //let canvas_beam_inner = document.getElementById("beam_canvas_inner");
  //let cbi = canvas_beam_inner.getContext("2d");
  //cbi.beginPath();
  //cbi.arc(7,7,7 ,0,2 * Math.PI);
  //cbi.fillStyle = "red";
  //cbi.fill();
  //cbi.stroke();
  document.getElementById("beam_inner").style.background = clr_beam_disabled;
  document.getElementById("beam_center").style.background = clr_beam_disabled;
  document.getElementById("beam_outer").style.background = clr_beam_disabled;
  
  // keyboard presses
  window.addEventListener("keydown",keydown,false);
  
  // control button groups - enable / disable buttons
    // readings coming in from crystal
  btn_grp_ctrl_reference_readings = ["auto_25","auto_50","auto_62_5","auto_75","auto_100","auto_0","auto_125","auto_187_5",
               "auto_250","pid_start","pid_stop","pid_pause", "mk5_250","mk5_800","mk5_100","mk3_200_psi",
               "auto_psi_100","auto_psi_200", "auto_psi_500", "auto_psi_650", "auto_psi_1000",
               "auto_psi_1300","auto_psi_0","zero1", "zero2","send_marker_btn","full_test"]

  btn_grp_ctrl_meter_readings = ["full_test"]

  // full auto - enable next and previous buttons
  btn_grp_full_auto = ["next_point","prev_point"]
  
  // enable / disable all buttons             
  btn_grp_ctrl_all = ["zero1", "zero2", "pid_start", "pid_stop", "pid_pause", "send_marker_btn",
                 "auto_0", "auto_25", "auto_50", "rest_mtr",'zero_inlet','zero_outlet',
                 "auto_62_5", "auto_75", "auto_100", "auto_125", "auto_187_5", "auto_250",
                 "fine_up", "fine_down", "adj_up", "adj_down",
                 "adj_stop", "mark_adj_zero", "open_eq",
                 "close_eq", "open_vent", "close_vent","open_low","close_low", "mk5_250","mk5_800","mk3_200_psi",
                 "mk5_100", "next_point", "prev_point",
                 "inlet_bump_up", "inlet_bump_down", "close_inlet_outlet", "outlet_bump_up",
                 "outlet_bump_down", "init_inlet", "auto_psi_100",
                 "auto_psi_200", "auto_psi_500", "auto_psi_650", "auto_psi_1000", "auto_psi_1300",
                 "auto_psi_0","full_test"]

  // full test active
  btn_grp_ctrl_full_test_active = ["zero1", "zero2", "pid_start", "pid_pause", "send_marker_btn",
                 "auto_0", "auto_25", "auto_50", "rest_mtr",'zero_inlet','zero_outlet',
                 "auto_62_5", "auto_75", "auto_100", "auto_125", "auto_187_5", "auto_250",
                 "fine_up", "fine_down",  
                 "inlet_bump_up", "inlet_bump_down", "close_inlet_outlet", "outlet_bump_up",
                 "outlet_bump_down", "init_inlet"]                 
                   
  // color button groups - used to maintain off color of buttons
  btn_grp_clr_zero = ["zero1", "zero2"];
  btn_grp_clr_pid_cntrl = ["pid_start", "pid_stop", "pid_pause"];
  btn_grp_clr_auto_dp = ["auto_0", "auto_25", "auto_50", "auto_62_5", "auto_75", 
                     "auto_100", "auto_125", "auto_187_5","auto_250","mk5_250","mk5_800","mk5_100"];                              
  btn_grp_clr_auto_psi = ["auto_psi_100","auto_psi_200", "auto_psi_500", "auto_psi_650",
                          "auto_psi_1000", "auto_psi_1300","auto_psi_0","mk3_200_psi"]
  btn_grp_clr_auto_marker = ["mk5_250","mk5_800","mk5_100","mk3_200_psi","send_marker_btn","next_point", "prev_point"];                                                                           
  btn_grp_clr_inlet_outlet = ["inlet_bump_up", "inlet_bump_down", "close_inlet_outlet", "outlet_bump_up",
                 "outlet_bump_down", "init_inlet","zero_inlet","zero_outlet"];  
  btn_grp_clr_rest = ["rest_mtr"];                 
  btn_grp_clr_adjuster = ["fine_up", "fine_down", "adj_up", "adj_down", "adj_stop", "mark_adj_zero"];  
  btn_grp_clr_eq = ["open_eq","close_eq"];  
  btn_grp_clr_vent = ["open_vent", "close_vent"]
  btn_grp_clr_low = ["open_low","close_low"]
  btn_grp_clr_meter_tcp = ["meter_tcp_read","meter_tcp_write"]
  btn_grp_clr_crystal_alarm = ["clear_crystal_alarm"]
  
  // color - pid_stop button pressed             
  btn_grp_clr_ctrl_pid_stop = ["auto_25","auto_50","auto_62_5","auto_75","auto_100","auto_0","auto_125","auto_187_5",
               "auto_250","mk5_250","mk5_800","mk5_100","mk3_200_psi", "next_point","send_marker_btn",
               "prev_point","auto_psi_100","auto_psi_200", "auto_psi_500", "auto_psi_650", "auto_psi_1000",
               "auto_psi_1300","auto_psi_0","adj_up","adj_down"];
               
  // color - all button groups
  btn_grps_clr_all = [btn_grp_clr_meter_tcp, btn_grp_clr_zero, btn_grp_clr_pid_cntrl, btn_grp_clr_auto_dp, 
                  btn_grp_clr_auto_psi,btn_grp_clr_auto_marker, btn_grp_clr_inlet_outlet, btn_grp_clr_rest, 
                  btn_grp_clr_adjuster, btn_grp_clr_eq, btn_grp_clr_vent,btn_grp_clr_low,btn_grp_clr_crystal_alarm,];
  
  // color groups to associate with button groups                
  var btn_grps_clrs = [clr_meter_tcp, clr_zero, clr_pid_cntrl, clr_auto_dp, clr_auto_psi,
                       clr_auto_marker, clr_inlet_outlet, clr_rest, clr_adjuster, 
                       clr_eq, clr_vent,clr_low, clr_send_marker, clr_crystal_alarm];                                 
  
  // exclusive color button groups - only one button colored on at a time
  btn_grp_exc_meter_tcp = ["meter_tcp_read","meter_tcp_write"];             
  btn_grp_exc_zero = ["zero1", "zero2"];
  btn_grp_exc_pid_cntrl = ["pid_start", "pid_stop", "pid_pause"];
  btn_grp_exc_auto = ["auto_0", "auto_25", "auto_50", "auto_62_5", "auto_75", "auto_100",
                      "auto_125", "auto_187_5","auto_250","mk5_250","mk5_800","mk3_200_psi","mk5_100","auto_psi_100",
                      "auto_psi_200", "auto_psi_500", "auto_psi_650", "auto_psi_1000", "auto_psi_1300",
                      "auto_psi_0"]
  btn_grp_exc_auto_mk = ["next_point", "prev_point"];                                                                           
  btn_grp_exc_inl_outl = ["inlet_bump_up", "inlet_bump_down", "close_inlet_outlet", "outlet_bump_up",
                          "outlet_bump_down", "init_inlet"];  
  btn_grp_exc_adj  = ["fine_up", "fine_down"];
  btn_grp_exc_adj_lock = ["adj_up", "adj_down", "adj_stop"];  
  btn_grp_exc_eq = ["open_eq","close_eq"];  
  btn_grp_exc_vent = ["open_vent", "close_vent"]
  btn_grp_exc_low = ["open_low","close_low"]
  
  
  // list of exclusive color button groups
  btn_grps_exc = [btn_grp_exc_meter_tcp, btn_grp_exc_zero, btn_grp_exc_pid_cntrl,btn_grp_exc_auto,
                  btn_grp_exc_auto_mk,btn_grp_exc_inl_outl,
                  btn_grp_exc_adj, btn_grp_exc_adj_lock,btn_grp_exc_eq, btn_grp_exc_vent,btn_grp_exc_low]
  
  
  function keydown(e) {
    //console.log(e)
    switch (e.keyCode){
      case 65: // a  center adjuster
        $("#re_center").click();
        break
  
      case 67: // c   close inlet and outlet
        $("#close_inlet_outlet").click();
        break
  
      case 68: // d   expose/hide reference dp
        low_status = 0;
        if (document.getElementById("open_low").value == 1){
          low_status = 1
        }
        if (low_status == 0) {
           $("#open_low").click()
        }
        else {
           $("#close_low").click()
        }
        break
  
      case 69: // e   equalizer control
        eq_status = 1;
        if (document.getElementById("open_eq").value == 1){
          eq_status = 0;
        }
        if (eq_status == 1) {
           $("#open_eq").click();
        }
        else if (eq_status == 0) {
           $("#close_eq").click();
        }
        break
  
      case 71: // g   get KPV
        $("#get_kpv_file").click();
        break
  
      case 75: // k
        if (e.shiftKey){
          document.getElementById("fine_down").click();
          break
        }
        else{
          document.getElementById("inlet_bump_down").click();
          break
        }
  
      case 74: // l
          document.getElementById("outlet_bump_up").click();
          break
  
      case 78: // n   next point
        document.getElementById("next_point").click();
        break
  
      case 73: // i
        if (e.ctrlKey){
          break
        }
        else if (e.shiftKey){
          document.getElementById("fine_up").click();
          break
        }
        else{
          document.getElementById("inlet_bump_up").click();
          break
        }
  
      case 76: // j
          document.getElementById("outlet_bump_down").click();
          break
  
      case 77: // m  mark aduster zero
        $("#mark_adj_zero").click();
        break
  
      case 82: // r  rest_mtr
        $("#rest_mtr").click();
        break
  
      case 86: // v - vent control
        vent_status = 1;
        if (document.getElementById("close_vent").value == 1){
          vent_status = 0;
        }
        if (vent_status == 1 || vent_status == -1) {
          $("#close_vent").click();
        }
        else if (vent_status == 0) {
          $("#open_vent").click();
        }
        break
  
      case 88: // x - stop auto pid
          $("#pid_stop").click();
        break
  
      case 89: // y   initialize inlet angle
        $("#init_inlet").click();
        break
  
      case 90: // z - zero 1
        if (e.shiftKey){
          $("#zero1").click();
          break
        }
        else{
          $("#zero2").click();
          break
        }
        break
        console.log("z pressed");
        break
    }
  }
  
  /* keyboard shortcuts
      case 16: // shift
      case 17: // control
      case 18: // alt
      case 32: // space
  
      case 49: // 1
      case 50: // 2
      case 51: // 3
      case 52: // 4
      case 53: // 5
      case 54: // 6
      case 55: // 7
      case 56: // 8
      case 57: // 9
  
      case 65: // a   center adjuster
      case 66: // b
      case 67: // c   close inlet and outlet
      case 68: // d   expose dp
      case 69: // e   equalizer control
      case 70: // f
      case 71: // g   get KPV
      case 72: // h
      case 73: // i   open inlet
      case 74: // j   open outlet
      case 75: // k   close inlet
      case 76: // l   close outlet
      case 77: // m   mark aduster zero
      case 78: // n   next point
      case 79: // o
      case 80: // p
      case 81: // q
      case 82: // r rest_mtr
      case 83: // s
      case 84: // t
      case 85: // u
      case 86: // v   vent control
      case 87: // w
      case 88: // x   stop auto pid
      case 89: // y   initialize inlet angle
      case 90: // z   zero crystal
  */
  
  // turn on or turn off button group color
  var btn_grp_clr_ctrl = function(btn_grp,i) {
    
    if (i == 0){
      for (key in btn_grp){
        btn_off(btn_grp[key]);
      }
    }
    else if (i == 1){
      for (key in btn_grp){
        btn_on(btn_grp[key]);
      }
    }  
  };
                                                                                          
  // enable or disable button group                                                                                        //
  var btn_grp_ctrl = function(btn_grp,i) {
    if (i == 0){
      for (key in btn_grp){
        try {
          document.getElementById(btn_grp[key]).disabled = true
        }
        catch(err) {
          console.log(btn_grp[key])
        }
      }
    }
  
    else if (i == 1){
      i = false;
      for (key in btn_grp){
        document.getElementById(btn_grp[key]).disabled = false;
      }
    }
  };
  
  pid_fields = ["pid_r1c1", "pid_r1c2", "pid_r1c3", "pid_r2c1", "pid_r2c2", "pid_r2c3",
                "pid_r3c1", "pid_r3c2", "pid_r3c3", "pid_r4c1", "pid_r4c3"]
  var pid_empty_fields = function() {
    for (key in pid_fields){
      document.getElementById(pid_fields[key]).textContent = "-";
    }
  };
  
  socket.onopen = function(){
    //console.log("connected");
    sendMessage({ 'dest':'qk1', 'purpose':'request_kpv', 'data' : '1'});
    pid_empty_fields();
    btn_grp_ctrl(btn_grp_clr_meter_tcp,0);
    sendMessage({"dest":"q22","purpose":"check_meter_tcp","data" : "1"});
    sendMessage({"dest":"qs4","purpose":"dp_high_alarm_display","data" : "0"});
    sendMessage({"dest":"qs5","purpose":"sp_high_alarm_display","data" : "0"});
    sendMessage({"dest":"qs11","purpose":"auto_sp_in_alarm_display","data" : "0"});
    sendMessage({ "dest":"qs12","purpose":"clear_crystal_alarm","data" : "1"});
    setTimeout(function(){user_activity()},5000)
    //heartbeat();
  };
  
  // message received from the socket
  socket.onmessage = function (message) {
    //console.log("receiving: " + message.data);
    if (JSON.parse(message.data).dest == 'kpv'){
      console.log("receiving initial kpv");
      obj = (JSON.parse(message.data))
      kpv = obj.kpv
      kpv_types = obj.kpv_types
      kpv_tags = obj.kpv_tags
      let i = -1
      for (var key in kpv) { 
          kpv_val.push(kpv[key])
      }
      for (var key1 in kpv_tags) { 
          kpv_des.push(kpv_tags[key1])
      }
      for (var key2 in kpv_types) {          
          kpv_type.push(kpv_types[key2])
      }
      init_vals()
      //console.log(kpv_val)
    } // if dest = kpv

    if (JSON.parse(message.data).dest == 'kpv_update'){
      let index = parseInt(JSON.parse(message.data).index);
      let val = JSON.parse(message.data).val;
      kpv_val[index] = castDataType(index,val);
      //init_vals()
      //console.log(kpv_val)
    }

    if (JSON.parse(message.data).dest == 'inactivity_time'){
      let max_inactive_sec = JSON.parse(message.data).max_inactive_sec
      let inactive_sec = JSON.parse(message.data).inactive_sec
      //console.log(inactive_sec)
      let sec_left = max_inactive_sec - inactive_sec
      let min_left = Math.floor(sec_left / 60)
      sec_left = parseInt(sec_left - (min_left * 60))
      if (sec_left < 10){
        sec_left = '0' + sec_left.toString()
      }
      let str = 'auto-logout in ' + min_left + ':' + sec_left
      //console.log(str)
      document.getElementById('inactivity_indicator').setAttribute('value',str)      
      $('#inactivity_indicator').text(str)
    }

    if (JSON.parse(message.data).dest == 'status indicator'){
      let fta = parseInt(JSON.parse(message.data).full_test_active)
      let ta = parseInt(JSON.parse(message.data).test_active)
      let pause = parseInt(JSON.parse(message.data).pause)
      let txt = ''
      let clr = '#eeefff'
      if (ta == 1) {
          txt = 'Test in progress'
          clr = '#00ff00'
        }
      if (fta == 1) {
        txt = 'Full test in progress'
        clr = '#00ff00'
      }
      if (pause == 1) {
        if (ta == 1) {
          txt = 'Test paused'
          clr = '#ee8877'
        }
        if (fta == 1) {
          txt = 'Full test paused'
          clr = '#ee8877'
        }        
      }
      $('#test_status').text(txt)
      document.getElementById('test_status').style.background = clr
    }
    
    if (JSON.parse(message.data).dest == 'baro_lock'){
      let bla = parseInt(JSON.parse(message.data).baro_lock)
      let clr = '#eeefff'
      if (bla == 1) {
          clr = '#00ff00'
      }
      document.getElementById('baro_readings').style.background = clr
    }

    if (JSON.parse(message.data).dest == 'inactivity_logout'){
      let logout_user = get_active_user();
      console.log("logging out user(" + logout_user + " due to inactivity")
      msg_box_chg("logging out user(" + logout_user + " due to inactivity")
      $.ajax({url:'/logout',type:'GET',data:{'purpose':'logout','user':logout_user}})
      setTimeout(function(){window.open(base_addr + '/login','_self')},5000)
    }

    if (JSON.parse(message.data).dest == 'user_logged_out'){
      let lo_user = JSON.parse(message.data).user;
      msg_box_chg('User (' + lo_user + ') logged out. Redirecting')
      setTimeout(function(){window.open(base_addr + '/','_self')},2000);
    }
                
    if(JSON.parse(message.data).dest == "web_pid"){
        //console.log("web_pid")
        obj = (JSON.parse(message.data));
        //console.log(obj)
        i = 0;
        r = 1;
        c = 1;
        for (var key in obj) {
          //console.log(key)
          if (i > 0){
            if (c == 4){
              c = 1;
              r++;
            }
            rc_id = "pid_r" + r + "c" + c;
            if (rc_id == "pid_r4c2"){
              rc_id = "pid_r4c3";
            }
            document.getElementById(rc_id).textContent = Number(obj[key]).toFixed(2)
            c++;
          }
          i++;
        }
      }
  
    if (JSON.parse(message.data).dest == "ref_readings"){ // from serialworker.py
      if (readings_active == 0){
        readings_active = 1;
        btn_grp_ctrl(btn_grp_ctrl_reference_readings,1);
      }
  
      inch_readings.empty();
      psi_readings.empty();
      let tdp = JSON.parse(message.data).ref_in_num
      let tsp = JSON.parse(message.data).ref_psi_num
      ref_in_num = Number(tdp).toFixed(2);
      ref_psi_num = Number(tsp).toFixed(1);
      if (ref_in_num != "error" && ref_psi_num != "error") {
        if (ref_in_num > 3500){
          inch_readings.append("OvrRng");  
        }
        else if (ref_in_num < -30){
          inch_readings.append("BlwRng");  
        }        
        else {
          inch_readings.append(ref_in_num);
        }
        if (ref_psi_num > 3500){
          psi_readings.append("OvrRng");  
        }
        else if (ref_psi_num < -10){
          psi_readings.append("BlwRng");  
        }        
        else {
          psi_readings.append(ref_psi_num);
        }
      }
    }
    
    if (JSON.parse(message.data).dest == "meter_tcp_connection"){  
      if (JSON.parse(message.data).data == '1') {
        console.log("meter tcp connected");
        document.getElementById("meter_ip_address").style.background = "#00ff00";
        btn_grp_ctrl(btn_grp_clr_meter_tcp,1);
      }
      if (JSON.parse(message.data).data == '0') {
        console.log("meter tcp disconnected");
        document.getElementById("meter_ip_address").style.background = "#D6E8F8";
        btn_grp_ctrl(btn_grp_clr_meter_tcp,0)
      }
    }
    
    
    if (JSON.parse(message.data).dest == "set_web_meter_ip"){  
      document.getElementById("meter_ip_address").value = JSON.parse(message.data).data;
    }

    if (JSON.parse(message.data).dest == "next_prev_button_enable"){
      let ctrl = parseInt(JSON.parse(message.data).data)
      btn_grp_ctrl(btn_grp_full_auto,ctrl);
    }    
    
    if (JSON.parse(message.data).dest == "meter_readings"){
      //console.log(JSON.parse(message.data))
      meter_inch_readings.empty();
      meter_psi_readings.empty();
      meter_temp_readings.empty();
      meter_in_num = JSON.parse(message.data).meter_in_num
      meter_psi_num = JSON.parse(message.data).meter_psi_num
      meter_temp = JSON.parse(message.data).meter_temp

      if (meter_in_num != "error") {
        meter_in_num = Number(meter_in_num).toFixed(2);
        if (meter_in_num > 9999.99){
          meter_inch_readings.append("OvrRng");    
        }
        else {
          meter_inch_readings.append(meter_in_num);
        }
      }
      else { // meter_in_num error
        meter_inch_readings.append("---")
      }

      if (meter_psi_num != "error") {
        meter_psi_num = Number(meter_psi_num).toFixed(3);
        if (meter_psi_num > 9999.99){
          meter_psi_readings.append("OvrRng");    
        }
        else {
          meter_psi_readings.append(meter_psi_num);
        }
      }
      else {// meter_psi_num error
        meter_psi_readings.append("---")
      }

      if (meter_temp != "error") {
        meter_temp = Number(meter_temp).toFixed(1);
        if (meter_temp > 9999.99){
          meter_temp_readings.append("OvrRng");    
        }
        else {
          meter_temp_readings.append(meter_temp);
        }
      }
      else { // meter_temp error
        meter_temp_readings.append("---")
      }      
    }
    
    if (JSON.parse(message.data).dest == "baro_readings"){
      baro_readings.empty();
      baro_psi = JSON.parse(message.data).baro_psi;
  
      if (baro_psi != "error"){
        baro_readings.append(baro_psi);
      }
      else {
        baro_readings.append("---");
      }
    }
    
    if (JSON.parse(message.data).dest == "temp_readings"){
      temp_readings.empty();
      ref_temp = JSON.parse(message.data).temp;
      if (ref_temp != "error"){
        if (ref_temp > 99999.9){
          temp_readings.append("OvrRng");  
        }
        else {
          temp_readings.append(ref_temp);
        }      
      }
      else {
        temp_readings.append("---");
      }
    }
      
    if (JSON.parse(message.data).dest == "adj_pos_display"){
      //console.log("adj_pos_status received");
      adj_pos = JSON.parse(message.data).adj_pos;
      //console.log(adj_pos)
      adj_pos_display.empty();
      adj_pos_display.append(adj_pos);
    }
  
    if (JSON.parse(message.data).dest == "mtr_current_readings"){
      //console.log("adj_ma message received")
      post = 0 // post to message display
      adj_ma = JSON.parse(message.data).adj_ma;
      adj_ST_up_avg = JSON.parse(message.data).adj_ST_up_avg;
      adj_ST_down_avg = JSON.parse(message.data).adj_ST_down_avg;
      adj_LT_up_avg = JSON.parse(message.data).adj_LT_up_avg;
      adj_LT_down_avg = JSON.parse(message.data).adj_LT_down_avg;
      if (adj_ma < 5 && adj_ma > -5) {
        adj_ma = 0;
      }
      if (adj_ma != prev_adj_ma && adj_ma != 0 && Math.abs(adj_ma) > ma_disp_pos_diff) {
        if (adj_ma > adj_max_ma) {
          adj_max_ma = adj_ma;
        }
        if (adj_ma <  adjuster_min_ma) {
          adjuster_min_ma = adj_ma;
        }
        if (adj_ma * prev_adj_ma < 0 || adj_ma * prev_adj_ma == 0) {
          adjuster_min_ma = 0;
          adj_max_ma = 0;
        }
        //console.log(adj_ST_up_avg + " / " + adj_ST_down_avg)
        adj_ST_avg_display.empty();
        adj_ST_avg_display.append(adj_ST_up_avg + " / " + adj_ST_down_avg);
        //adj_LT_avg_display.empty();
        //adj_LT_avg_display.append(adj_LT_up_avg + " / " + adj_LT_down_avg);
        prev_adj_ma = adj_ma;
        if (Math.abs(adj_max_ma - prev_adj_max_ma) > minmax_post_diff) {
          post = 1;
          prev_adj_max_ma = adj_max_ma;
        }
        if (Math.abs(adjuster_min_ma - prev_adjuster_min_ma) > minmax_post_diff) {
          post = 1;
          prev_adjuster_min_ma = adjuster_min_ma;
        }
      }
    }
  
  
    if (JSON.parse(message.data).dest == "inlet_display"){
      //console.log("inlet_status received");
      inlet_angle = JSON.parse(message.data).inlet_angle;
      inlet_display.empty();
      inlet_display.append(inlet_angle);
    }
  
    if (JSON.parse(message.data).dest == "outlet_display"){
      //console.log("outlet_status received");
      outlet_angle = JSON.parse(message.data).outlet_angle;
      outlet_display.empty();
      outlet_display.append(outlet_angle);
    }
  
  
    if (JSON.parse(message.data).dest == "stpt_display"){
      stpt = JSON.parse(message.data).data;
      document.getElementById("inch_stpt").value = stpt;
      document.getElementById("psi_stpt").value = "---";
    }
  
    if (JSON.parse(message.data).dest == "psi_stpt_display"){
      stpt = JSON.parse(message.data).data;
      document.getElementById("psi_stpt").value = stpt;
      document.getElementById("inch_stpt").value = '---'
    }
  
    if (JSON.parse(message.data).dest == "ping_web"){
      sendMessage({ "dest":"q10","purpose":"web_running","data" : "1"});
      web_running = 1;
    }
  
    // pid running ticker
    if (JSON.parse(message.data).dest == "pid_running"){
      if (JSON.parse(message.data).data == 1) {
        if (pid_running_count == 1) {
          document.getElementById("pid_r0c0").textContent = ".";
        }
        else if (pid_running_count == 2) {
          document.getElementById("pid_r0c0").textContent = "..";
        }
        else if (pid_running_count == 3) {
          document.getElementById("pid_r0c0").textContent = "...";
        }
        else if (pid_running_count == 4) {
         document.getElementById("pid_r0c0").textContent = "....";
          pid_running_count = 0
        }
        pid_running_count ++;
      }
      else if (JSON.parse(message.data).data == 0) {
        document.getElementById("pid_r0c0").textContent = "x";
        pid_running_count = 1;
      }
    }
    
    if (JSON.parse(message.data).dest == "btn_status"){
      console.log(message)
      btn = JSON.parse(message.data).btn
      data = JSON.parse(message.data).state
      if (data == 1) {
        btn_on(btn,"#00ff00")
      }
      else if (data == 0) {
        btn_off(btn)
      }
      else if (data == -1) {
        btn_grp_cntrl(btn_grp_auto,0)
      }
    }
  
    if (JSON.parse(message.data).dest == "dp_high_alarm"){
      dp_high_alarm = JSON.parse(message.data).data;
        if (dp_high_alarm == 1) {
          document.getElementById("inch_readings").style.background = "#ff0000";
          sendMessage({"dest":"qs4","purpose":"dp_high_alarm_display","data" : "1"});
        }
        else {
          document.getElementById("inch_readings").style.background = "#ffffff";
          sendMessage({"dest":"qs4","purpose":"dp_high_alarm_display","data" : "0"});
        }
    }
  
    if (JSON.parse(message.data).dest == "sp_high_alarm"){
      sp_high_alarm = JSON.parse(message.data).data;
        if (sp_high_alarm == 1) {
          document.getElementById("psi_readings").style.background = "#ff0000";
          sendMessage({"dest":"qs5","purpose":"sp_high_alarm_display","data" : "1"});
        }
        else {
          document.getElementById("psi_readings").style.background = "#ffffff";
          sendMessage({"dest":"qs5","purpose":"sp_high_alarm_display","data" : "0"});
        }
    }

    if (JSON.parse(message.data).dest == "auto_sp_in_alarm"){
      auto_sp_in_alarm = JSON.parse(message.data).data;
        if (auto_sp_in_alarm == 1) {
          document.getElementById("inch_readings").style.background = "#ff0000";
          sendMessage({"dest":"qs11","purpose":"auto_sp_in_alarm_display","data" : "1"});
        }
        else {
          document.getElementById("inch_readings").style.background = "#ffffff";
          sendMessage({"dest":"qs11","purpose":"auto_sp_in_alarm_display","data" : "0"});
        }
    }
    
    if (JSON.parse(message.data).dest == "web_message"){
      msg = JSON.parse(message.data).val;
      clear = 0
      clear = JSON.parse(message.data).clear
      if (ap == "    ."){
        ap = "    ..";
      }
      else{
        ap = "    .";
      }
      //if (msg == "cls"){
      //  message_box.empty();
      //}
      if (clear == 0) {
        msg_box_chg(msg + ap)
      } 
      else{
        msg_box_chg(msg + ap,clear)
      }
    }
  
    if (JSON.parse(message.data).dest == "poll_fail"){
      btn_grp_ctrl(btn_grp_ctrl_reference_readings,0);
      // need to add - stop auto pid ??
      if (readings_active == 1){
        readings_active = 0;
      };
      inch_readings.empty();
      inch_readings.append("---");
      psi_readings.empty();
      psi_readings.append("---");
      msg_box_chg("Crystal disconnected - Attempting to re-connect")
    }

    if (JSON.parse(message.data).dest == "crystal_inhibit"){
      crystal_inhibit = parseInt(JSON.parse(message.data).crystal_inhibit)
      // console.log('crystal_inhibit : ' + crystal_inhibit)
      if (crystal_inhibit == 1) {
        msg_box_chg("Crystal readings disabled from settings page")
        btn_grp_ctrl(btn_grp_ctrl_reference_readings,0)
        if (readings_active == 1){
          readings_active = 0
        }
        inch_readings.empty()
        inch_readings.append("---")
        psi_readings.empty()
        psi_readings.append("---")
      }
      else if(crystal_inhibit == 0) {
        msg_box_chg("Crystal readings enabled from settings page")
        btn_grp_ctrl(btn_grp_ctrl_reference_readings,1)
        if (readings_active == 0){
          readings_active = 1
        }        
      }
    }
    
    if (JSON.parse(message.data).dest == "send_marker"){
      console.log("send calibration marker")
      marker = JSON.parse(message.data).data;
      console.log(marker)
      if (JSON.parse(message.data).unit_type == "0"){ // PCCU send marker
        str = "cmds:/rmark_pccu/" + marker;
        console.log(str)
      }
      else { // ROCLINK send marker
        str = "cmds:/rmark_roclink/" + marker;
        //console.log(str)      
      }
      var wopen = window.open(str,"_blank");
      setTimeout(function(){wopen.close()},1000);
    }

    if (JSON.parse(message.data).dest == "play_sound"){
      console.log("playing sound")
      data = JSON.parse(message.data).data;
      str = "cmds:/rplay_sound/" + data;
      console.log(str)
      var wopen = window.open(str,"_blank");
      //console.log(wopen)
      setTimeout(function(){wopen.close()},1000);
    }    
  
    if (JSON.parse(message.data).dest == "send_cal_low"){
      console.log("command received for cal low")
      marker = JSON.parse(message.data).data;
      str = "cmds:/rsend_cal_low/" + marker;
      var wopen = window.open(str,"_blank");
      setTimeout(function(){wopen.close();},10);
    }
  
    if (JSON.parse(message.data).dest == "send_cal_high"){
      marker = JSON.parse(message.data).data;
      str = "cmds:/rsend_cal_high/" + marker;
      var wopen = window.open(str,"_blank");
      setTimeout(function(){wopen.close();},10);
    }
  
    if (JSON.parse(message.data).dest == "send_cal_mid"){
      marker = JSON.parse(message.data).data;
      str = "cmds:/rsend_cal_mid/" + marker;
      var wopen = window.open(str,"_blank");
      setTimeout(function(){wopen.close();},10);
    }
  
    if (JSON.parse(message.data).dest == "save_msg_log"){
      //console.log(JSON.parse(message.data))
      sendMessage({"dest":"qw12","purpose":"save_msg_log","data" : msg_log});
      //console.log(msg_log)
    }
    
    if (JSON.parse(message.data).dest == "beam_stat"){
      //console.log(JSON.parse(message.data))
      beam_outer_stat = JSON.parse(message.data).outer; // ai0
      beam_center_stat = JSON.parse(message.data).center; // ai0
      beam_inner_stat = JSON.parse(message.data).inner; // ai1     
      switch (beam_outer_stat) { 
        case 0:
          document.getElementById("beam_outer").style.background = clr_green;
          break
        case 1:
          document.getElementById("beam_outer").style.background = clr_red;
          break        
        case 2:
          document.getElementById("beam_outer").style.background = clr_beam_disabled;
          break   
        default:
          document.getElementById("beam_outer").style.background = clr_yellow;
          break
      }
      switch (beam_inner_stat) {
        case 0:
          document.getElementById("beam_inner").style.background = clr_red;
          break
        case 1:
          document.getElementById("beam_inner").style.background = clr_green;
          break
        case 2:
          document.getElementById("beam_inner").style.background = clr_beam_disabled;
          break      
        default:
          document.getElementById("beam_inner").style.background = clr_yellow;
          break                
      }
      switch (beam_center_stat) {
        case 0:
          document.getElementById("beam_center").style.background = clr_red;
          break
        case 1:
          document.getElementById("beam_center").style.background = clr_green;
          break
        case 2:
          document.getElementById("beam_center").style.background = clr_beam_disabled;
          break      
        default:
          document.getElementById("beam_center").style.background = clr_yellow;
          break                
      }                           
      //console.log(msg_log)
    }  

    if (JSON.parse(message.data).dest == "max_poll_fail"){
      $('#clear_crystal_alarm').prop('disabled',false)
    }
    
    if (JSON.parse(message.data).dest == "crystal_alarm_cleared"){
      $('#clear_crystal_alarm').prop('disabled',true)
    }

  };
  
  // -------------------------------------------------------------
  // ----------------------
  socket.onclose = function(){
    btn_grp_ctrl(btn_grp_ctrl_all,0);
    if (readings_active == 1){
      readings_active = 0;
    };
    console.log("disconnected");
    inch_readings.empty();
    psi_readings.empty();
    temp_readings.empty();
    meter_inch_readings.empty();
    meter_psi_readings.empty();    
    meter_temp_readings.empty();    
    inch_readings.append("---");
    psi_readings.append("---");
    temp_readings.append("---");
    meter_inch_readings.append("---");
    meter_psi_readings.append("---");  
    meter_temp_readings.append("---");  
    msg_box_chg("-----Connection to server lost-----");
  };

  var check_kpv_links = function(idx,vl){
    for(let s = 0;s < kpv_links_index.length; s++){
      if(idx == kpv_links_index[s]){
        // console.log(kpv_links_id[s])
        if (document.querySelector('#' + kpv_links_id[s]) != null){
          document.getElementById(kpv_links_id[s]).value = vl;  
        }
        break;
      }
    }
  }

  var castDataType = function(indx, valt){
    if (kpv_type[indx] == 'i') {
      return parseInt(valt)
    }
    else if (kpv_type[indx] == 'f') {
      return parseFloat(valt)
    }
    else if (kpv_type[indx] == 's') {
      return String(valt)
    }
    else {
      console.log("Not able to castDataType for kpv[" + indx + "] kpv_type[indx] = " + kpv_type[indx])
    }
  }

  var init_vals = function(){
    //console.log('initializing field values')
    for (let i = 0;i<kpv_links_index.length;i++) {
      check_kpv_links(kpv_links_index[i],kpv_val[kpv_links_index[i]])
    }
  }
        
  // send a message to the server
  var sendMessage = function(message) {
    //console.log("sending:" + message.data);
    socket.send(JSON.stringify(message));
  };
  
  var msg_box_chg = function(msg,clear=0){
    if (clear == 0) {
      message_box.prepend(msg);  
    }
    else {
      message_box.prepend(msg);  
    }
    message_box.prepend($("<br/>"));
    msg_log += msg;
    msg_log += "<br/>";
  }
  // ----------------------
  // -------------------------------------------------------------

  var get_active_user = function() {
   page_user = document.cookie.split('; ').find(row => row.startsWith('skytek_active_user')).split('=')[1];
   return page_user;
  }
    
  var playaudio = function() {
    //var wopen = window.open("wnc:","_blank");
    //setTimeout(function(){wopen.close();},20);
  };
  
  var heartbeat = function() {
    null
    //hb = !hb;
    //sendMessage({"dest":"q32","purpose":"heartbeat","data" : hb});
    //console.log("hb:" + hb);
    //setTimeout(function(){heartbeat()},1000);
  };
  
  var btn_on = function(btn,clr='#00ff00'){
    var found = 0;
    // de-activate buttons if in exclusive button group
    for (nkey in btn_grps_exc){ 
      for (nkey2 in btn_grps_exc[nkey]) {
        if (btn_grps_exc[nkey][nkey2] == btn) {
          for (nkey3 in btn_grps_exc[nkey]) {
            btn_off(btn_grps_exc[nkey][nkey3]);
          }
          found = 1;
        }
        if (found == 1){break;};
      }
      if (found == 1){break;};
    }
    // turn off other buttons if in exclusive button group
  
    // activate requested button  
    try {
      document.getElementById(btn).value = 1;
      document.getElementById(btn).active = 1;
      document.getElementById(btn).focus = 1;
      document.getElementById(btn).visited = 1;
      document.getElementById(btn).style.background = clr;
      document.getElementById(btn).style.color = "#000000";
    }
    catch (err) {
    };
  };
  
  // de-activate button to color of button group
  var btn_off = function(btn){
    // find button group the button is in
    var found = 0;
    var clr = '#D6E8F8'
    for (key in btn_grps_clr_all){ // search in all button groups
      for (key2 in btn_grps_clr_all[key]) { // search through each button group
        if (btn_grps_clr_all[key][key2] == btn) { // see if btn is in the button group
          clr = btn_grps_clrs[key];
          found = 1
        }
        if (found == 1){break;};
      }
      if (found == 1){break;};
    };
    // find button group the button is in
    try {
      document.getElementById(btn).value = 0;
    }
    catch(err) {
      console.log(btn)
    }
    document.getElementById(btn).active = 0;
    document.getElementById(btn).focus = 0;
    document.getElementById(btn).visited = 0;
    document.getElementById(btn).style.background = clr; // set to group associated color
  }
  
  var btn_grp_clr = function(btn_grp,clr) {
    //console.log("button state entered")
    for (key in btn_grp){
      //console.log(key);
      //console.log(btn_grp[key]);
      document.getElementById(btn_grp[key]).style.background = clr;
    }
  };  
  // initial calls to set button group color
  btn_grp_clr(btn_grp_clr_zero,clr_zero)
  btn_grp_clr(btn_grp_clr_pid_cntrl,clr_pid_cntrl)
  btn_grp_clr(btn_grp_clr_auto_dp,clr_auto_dp)
  btn_grp_clr(btn_grp_clr_auto_psi,clr_auto_psi)
  btn_grp_clr(btn_grp_clr_auto_marker,clr_auto_marker)
  btn_grp_clr(btn_grp_clr_inlet_outlet,clr_inlet_outlet)
  btn_grp_clr(btn_grp_clr_rest,clr_rest)
  btn_grp_clr(btn_grp_clr_adjuster,clr_adjuster)
  btn_grp_clr(btn_grp_clr_eq,clr_eq)
  btn_grp_clr(btn_grp_clr_vent,clr_vent)
  btn_grp_clr(btn_grp_clr_low,clr_low)
  btn_grp_clr(btn_grp_clr_meter_tcp,clr_meter_tcp)
  btn_grp_clr(btn_grp_clr_crystal_alarm,clr_crystal_alarm)
  
  
  $('#settings_btn').click(function(){
    window.open("http://192.168.42.1:10120/settings","_blank");
  });
  
  // click inside input box disables window keyboard listener
  $("#send_marker_btn").click(function(){
    console.log("send marker button")
    inmark = document.getElementById("inch_stpt").value
    //console.log(inmark);
    psimark = document.getElementById("psi_stpt").value
    //console.log(psimark);
    baromark = document.getElementById("baro_readings").textContent
    //console.log(baromark);
    tempmark = document.getElementById("temp_readings").textContent
    marker = "---"
    if (isFinite(inmark) && !isFinite(psimark)) {
      marker = Number(inmark);
      dtype = 'DP'
    }
    else if (isFinite(psimark) && isFinite(baromark) && !isFinite(inmark)) {
      marker = (Number(psimark) + Number(baromark)).toFixed(2);
      dtype = 'SP'
      console.log(marker);
    }
    else if (isFinite(tempmark) && !isFinite(inmark) && !isFinite(psimark)) {
      marker = Number(tempmark).toFixed(1);
      dtype = 'TP'
    }
    else {
      msg_box_chg('no marker to send')
    }
    if (marker >= 0) {
      // console.log(kpv_val[246])
      if (kpv_val[246] == 0){ // PCCU send marker
        if (kpv_val[270] == 0){ // send markers via keystroke
          str = "cmds:/rmark_pccu/" + marker;
          // console.log(str)
          var wopen = window.open(str,"_blank");
          // console.log(wopen);
          setTimeout(function(){wopen.close()},1000);
        }
        else if (kpv_val[270] == 1){ // send markers via comm
          console.log('send marker via comm')
          sendMessage({ "dest":"q36","purpose":"web_send_marker","marker" : marker});
        }
      }
      else { // ROCLINK send marker
        if (kpv_val[270] == 0){ // send markers via keystroke
          str = "cmds:/rmark_roclink/" + marker;
          // console.log(str)
          var wopen = window.open(str,"_blank");
          // console.log(wopen);
          setTimeout(function(){wopen.close()},1000);
        }
        else if (kpv_val[270] == 1){ // send markers via comm
          console.log('send marker via comm')
          sendMessage({ "dest":"q36","purpose":"web_send_marker","marker" : marker});
        }        
        //console.log(str)      
      }
      // database
      console.log(parseFloat(ref_psi_num)+parseFloat(baromark))
      if (dtype == 'DP') {
        sendMessage({ "dest":"qd1","dtype":dtype,"m_read":meter_in_num,"r_read":ref_in_num})
      }
      else if (dtype == "SP") {
        sendMessage({ "dest":"qd1","dtype":dtype,"m_read":meter_psi_num,"r_read":parseFloat(ref_psi_num)+parseFloat(baromark)});
      }
      else if (dtype == "TP") {
        sendMessage({ "dest":"qd1","dtype":dtype,"m_read":meter_temp,"r_read":ref_temp});
      }              
    }
  });
  
  $("#meter_ip_input").click(function(){
    window.removeEventListener("keydown",keydown,false);
  });

  $("#btn_baro_lock").click(function(){
    sendMessage({"dest":"q41","purpose":"baro_lock_button","data" : document.getElementById("baro_readings").textContent});
  });  
  
  //zero port 1 button
  $("#zero1").click(function(){
    console.log("zero 1");
    sendMessage({"dest":"qs6","purpose":"crystal_write","data" : "Z1"});
  });
  
  //zero port 2 button
  $("#zero2").click(function(){
    sendMessage({ "dest":"qs6","purpose":"crystal_write","data" : "Z2"});
  });
  
  // rest outputs button
  $("#rest_mtr").click(function(){
    sendMessage({ "dest":"q26","purpose":"rest_mtr","data" : "1"});
  });
  
  //Auto mark 250 5 points button
  $("#mk5_250").click(function(){
    sendMessage({ "dest":"q15","purpose":"full_auto_checks",'data':{"stpt":"250","mode":"i"}});
    document.getElementById("inch_stpt").value = "250"
    document.getElementById("psi_stpt").value = "---";
    btn_on('mk5_250');
  });

  //Auto mark 250 5 points button
  $("#mk5_800").click(function(){
    sendMessage({ "dest":"q15","purpose":"full_auto_checks",'data':{"stpt":"800","mode":"i"}});
    document.getElementById("inch_stpt").value = "800"
    document.getElementById("psi_stpt").value = "---";
    btn_on('mk5_800');
  });
  
  //Auto mark 100 5 points button
  $("#mk5_100").click(function(){
    sendMessage({ "dest":"q15","purpose":"full_auto_checks",'data':{"stpt":"100","mode":'i'}});
    document.getElementById("inch_stpt").value = "100"
    
    document.getElementById("psi_stpt").value = "---"
    btn_on('mk5_100');
  });

  //Auto mark sp 200 3 points button
  $("#mk3_200_psi").click(function(){
    sendMessage({ "dest":"q15","purpose":"full_auto_checks",'data':{"stpt":"200","mode":'p'}});
    document.getElementById("psi_stpt").value = "200"
    document.getElementById("inch_stpt").value = "---"
    btn_on('mk3_200_psi');
  });  
  
  //Skip to next point button
  $("#next_point").click(function(){
    sendMessage({ "dest":"q18","purpose":"skip_point","data" : "1"});
  });
  
  //Skip to previous point button
  $("#prev_point").click(function(){
    sendMessage({ "dest":"q18","purpose":"skip_point","data" : "-1"});
  });
  
  // Read a Totalflow rs232 register
  $("#meter_rs232_read").click(function(){
      var reg = prompt("Register to read : ","0.0.3");
      if (reg == null || reg == ""){
        alert("No data entered");
      }
      else {
        sendMessage({ "dest":"q35","purpose":"meter_read_reg","data" : reg,"return_to":"web"});
      }  
  });
  
  // Write a Totalflow tcp register
  $("#meter_tcp_write").click(function(){
      var reg = prompt("Register to write : ","8000");
      if (reg == null || reg == ""){
        alert("No data entered");
      }
      var val = prompt("Value to write : ","1");
      if (val == null || val == ""){
        alert("No data entered");
      }    
      var type = prompt("Data type : ","float");
      if (type == null || type == ""){
        alert("No data entered");
      }        
      else {
        sendMessage({ "dest":"qt2","purpose":"meter_write_reg","register" : reg,'value':val,'data_type':type});
      }  
  });
  
  // Read a Totalflow tcp register
  $("#meter_tcp_read").click(function(){
      var reg = prompt("Register to read : ","8000");
      if (reg == null || reg == ""){
        alert("No data entered");
      }
      var type = prompt("Data type : ","float");
      if (type == null || type == ""){
        alert("No data entered");
      }        
      else {
        sendMessage({ "dest":"qt3","purpose":"meter_read_reg","register":reg,"data_type":type,"return_to":"web"});
      }  
  });
  
  // Auto PSI 100
  $("#auto_psi_100").click(function(){
    psi_stpt = 100;
    document.getElementById("psi_stpt").value = 100;
    sendMessage({ "dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  });
  
  // Auto PSI 200
  $("#auto_psi_200").click(function(){
    psi_stpt = 200;
    document.getElementById("psi_stpt").value = 200;
    sendMessage({"dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  });
  
  // Auto PSI 500
  $("#auto_psi_500").click(function(){
    psi_stpt = 500;
    document.getElementById("psi_stpt").value = 500;
    sendMessage({"dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  });
  
  // Auto PSI 650
  $("#auto_psi_650").click(function(){
    psi_stpt = 650;
    document.getElementById("psi_stpt").value = 650;
    sendMessage({"dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  });
  
  // Auto PSI 1000
  $("#auto_psi_1000").click(function(){
    psi_stpt = 1000;
    document.getElementById("psi_stpt").value = 1000;
    sendMessage({"dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  });
  
  // Auto PSI 1300
  $("#auto_psi_1300").click(function(){
    psi_stpt = 1300;
    document.getElementById("psi_stpt").value = 1300;
    sendMessage({"dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  });

  // Auto PSI 0
  $("#auto_psi_0").click(function(){
    psi_stpt = 0;
    document.getElementById("psi_stpt").value = 0;
    sendMessage({"dest":"q27","purpose":"pid_start_psi","data" : psi_stpt});
  })
  
  // set totalflow ip button
  document.querySelector("#meter_ip_address").onchange = (function(){
    vap = document.getElementById("meter_ip_address").value;
    sendMessage({ "dest":"qt1","purpose":"set_meter_ip","data" : vap});
    sendMessage({ "dest":"qtd1","purpose":"set_meter_ip","data" : vap});
  });
  
  // Restart cntrl.py
  $("#restart").click(function(){
    sendMessage({ "dest":"server","purpose":"restart","data":"1"});
  });
  
  //fine up button
  $("#fine_up").click(function(){
    sendMessage({ "dest":"q24","purpose":"manual_control","data" : "fine_up"});
  });
  
  //fine down button
  $("#fine_down").click(function(){
    sendMessage({ "dest":"q24","purpose":"manual_control","data" : "fine_down"});
  });
  
  $("#auto_25").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "25"});
    document.getElementById("inch_stpt").value = "25";
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_50").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "50"});
    document.getElementById("inch_stpt").value = "50";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_75").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "75"});
    document.getElementById("inch_stpt").value = "75";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_100").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "100"});
    document.getElementById("inch_stpt").value = "100";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  
  $("#auto_0").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "0"});
    document.getElementById("inch_stpt").value = "0";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_62_5").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "62.5"});
    document.getElementById("inch_stpt").value = "62.5";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_125").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "125"});
    document.getElementById("inch_stpt").value = "125";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_187_5").click(function(){
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "187.5"});
    document.getElementById("inch_stpt").value = "187.5";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#auto_250").click(function(){
    console.log("250 clicked")
    sendMessage({"dest":"q27","purpose":"pid_start_inch","data" : "250"});
    document.getElementById("inch_stpt").value = "250";
    
    document.getElementById("psi_stpt").value = "---"
  });
  
  $("#pid_start").click(function(){
    console.log("start button pressed")
    var inch_send = $("#inch_stpt").val();
    var psi_send = document.getElementById("psi_stpt").value;
    if (isFinite(inch_send) && !isFinite(psi_send)){
      msg_box_chg("new inch setpoint = " + inch_send);
      document.getElementById("psi_stpt").value = "---";
      sendMessage({ "dest":"q27","purpose":"pid_start_inch","data" : inch_send});
    }
    else if (!isFinite(inch_send) && isFinite(psi_send)){
      msg_box_chg("new psi setpoint = " + psi_send)
      document.getElementById("inch_stpt").value = "---"
      sendMessage({ "dest":"q27","purpose":"pid_start_psi","data" : psi_send});
    }
    else if(!isFinite(inch_send) && !isFinite(psi_send)){
      document.getElementById("psi_stpt").value = "---";
      document.getElementById("inch_stpt").value = "---";
      msg_box_chg("Enter a setpoint first");
    }
    else if (isFinite(inch_send) && isFinite(psi_send)){
      document.getElementById("psi_stpt").value = "---";
      document.getElementById("inch_stpt").value = "---";
      msg_box_chg("Enter either an inch setpoint or psi setpoint")  ;
    }
    else {
      console.log("Something went wrong with sending the setpoint");
    }
  });
  
  // alternate between entry in inch and psi
  document.querySelector("#psi_stpt").onfocus = (function(){
    document.getElementById("inch_stpt").value = "---";
  });
  document.querySelector("#inch_stpt").onfocus = (function(){
    document.getElementById("psi_stpt").value = "---";
  });
  
  
  $("#pid_stop").click(function(){
    console.log("stop button pressed");
    sendMessage({ "dest":"q28","purpose":"pid_stop","data" : "1"});
    document.getElementById("inch_stpt").value = "---";
    document.getElementById("psi_stpt").value = "---";
    pid_empty_fields();
    btn_grp_clr_ctrl(btn_grp_clr_ctrl_pid_stop,0);
  });
  
  $("#pid_pause").click(function(){
    console.log("pause button pressed")
    if (document.getElementById("pid_pause").value == 0) {
      sendMessage({ "dest":"q29","purpose":"pid_pause","data" : "1"});
    }
    else if (document.getElementById("pid_pause").value == 1) {
      sendMessage({ "dest":"q29","purpose":"pid_pause","data" : "0"});
    }
  });
  
  $("#mark_adj_zero").click(function(){
    sendMessage({ "dest":"q1","purpose":"save_inch_center_position","data" : "1"});
  });
  
  $("#close_inlet_outlet").click(function(){
    sendMessage({ "dest":"q2","purpose":"close_inlet","data" : "1"});
    sendMessage({ "dest":"q3","purpose":"close_outlet","data" : "1"});
  });
  
  $("#zero_inlet").click(function(){
    if (document.getElementById("zero_inlet").value == 0){
      var tm = prompt("Enter a temporary inlet maximum angle","180");
      if (tm == null || tm == ""){
        alert("Inlet re-zero procedure canceled");
      }
      else if (isFinite(tm)){
        if (tm >= 100 && tm <= 180){
          sendMessage({ "dest":"q30","purpose":"zero_inlet","data" : tm});
          btn_on("zero_inlet","#aa55ff");
        }
        else{
          alert("Enter a number between 100 and 180");
        }
      }
      else {
        alert("Invalid data entered - inlet re-zero procedure canceled");
      }
    }
    else { // send new zero inlet value
      btn_off("zero_inlet");
      sendMessage({ "dest":"q30","purpose":"zero_inlet","data" : "0"});
    }
  });
  
  $("#zero_outlet").click(function(){
    if (document.getElementById("zero_outlet").value == 0){
      var tm = prompt("Enter a temporary outlet maximum angle","180");
      if (tm == null || tm == ""){
        alert("Outlet re-zero procedure canceled");
      }
      else if (isFinite(tm)){
        if (tm >= 100 && tm <= 180){
          sendMessage({ "dest":"q31","purpose":"zero_outlet","data" : tm});
          btn_on("zero_outlet","#aa55ff");
        }
        else{
          alert("Enter a number between 100 and 180");
        }
      }
      else {
        alert("Invalid data entered - outlet re-zero procedure canceled");
      }
    }
    else {
      btn_off("zero_outlet")
      sendMessage({ "dest":"q31","purpose":"zero_outlet","data" : "0"});
    }
  });
  
  $("#re_center").click(function(){
    sendMessage({ "dest":"q6","purpose":"re_center","data" : "1"});
  });
  
  $("#adj_up").click(function(){
    sendMessage({ "dest":"q24","purpose":"manual_control","data" : "1"});
  });
  
  $("#adj_down").click(function(){
    sendMessage({ "dest":"q24","purpose":"manual_control","data" : "-1"});
  });
  
  $("#adj_stop").click(function(){
    sendMessage({ "dest":"q24","purpose":"manual_control","data" : "0"});
  });
  
  $("#open_eq").click(function(){
    sendMessage({ "dest":"q9","purpose":"eq","data" : "0"});
  });
  
  $("#close_eq").click(function(){
    sendMessage({ "dest":"q9","purpose":"eq","data" : "1"});
  })
  
  $("#open_vent").click(function(){
    sendMessage({ "dest":"q11","purpose":"vent","data" : "1"});
  })
  
  $("#close_vent").click(function(){
    sendMessage({ "dest":"q11","purpose":"vent","data" : "0"});
  })

  $("#open_low").click(function(){
    sendMessage({ "dest":"q19","purpose":"low","data" : "1"});
    console.log("open low button pressed")
  })
  
  $("#close_low").click(function(){
    sendMessage({ "dest":"q19","purpose":"low","data" : "0"});
    console.log("close low button pressed")
  })

  $("#full_test").click(function(){
    sendMessage({ "dest":"q37","purpose":"full_test","data" : "1"})
    // btn_grp_ctrl(btn_grp_ctrl_full_test_active,0)
  })
    
  $("#inlet_bump_up").click(function(){
    sendMessage({ "dest":"q7","purpose":"inlet","data" : "-1"});
  });
  
  $("#inlet_bump_down").click(function(){
    sendMessage({ "dest":"q7","purpose":"inlet","data" : "1"});
  });
  
  $("#outlet_bump_up").click(function(){
    sendMessage({ "dest":"q8","purpose":"outlet","data" : "-1"});
  });
  
  $("#outlet_bump_down").click(function(){
    sendMessage({ "dest":"q8","purpose":"outlet","data" : "1"});
  });
  
  $("#init_inlet").click(function(){
    sendMessage({ "dest":"q4","purpose":"init_inlet","data" : "1"});
    console.log("initialize inlet");
  });

  $("#clear_crystal_alarm").click(function(){
    sendMessage({ "dest":"qs12","purpose":"clear_crystal_alarm","data" : "1"});
  });
  
  function user_activity() {
    let ct = (new Date().getTime())/1000
    if (ct - user_activity_time > check_activity_sec) {
      user_activity_time = ct
      $.ajax({url:'/activity',type:'POST',data:{'purpose':'activity'}})
    }
  }

  function ajax_request(data_s,url_s = '/settings',type_s = 'POST') {
    $.ajax({url:url_s,type:type_s,data:data_s})
  }
       
});

