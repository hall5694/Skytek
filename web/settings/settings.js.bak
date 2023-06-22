$(document).ready(function(){
  
  window.user_activity_time = (new Date().getTime())/1000
  window.check_activity_sec = 5
  window.addEventListener("mousemove",user_activity);  
  kpv_wmod=[]

  window.kpv_val=[]
  window.kpv_des=[]
  window.kpv_type=[]

  del_icon_src = 'del.png'
  window.srvr_ip = '192.168.42.1';
  window.srvr_port = '10120'
  window.base_addr = 'http://' + srvr_ip + ':' + srvr_port;
  var socket = new WebSocket("ws://" + srvr_ip + ":" + srvr_port + "/ws/settings");
  // list of exclusive color button groups
  btn_grps_exc = [];

  window.root_sections = ['add_new_user_btn','remove_user_btn','change_root_btn','show_users_sec_btn']
  
  var btn_clr = "#D6E8F8";
  var clr2 = "#eeefff";
  var clr3 = "#dddddd";
  var clr4 = "#D6E8F8";
  var clr5 = "#cceeee";
  var clr6 = "#000000";
  var clr7 = "#626a6a";
  var clr8 = "#82c9ff";
  var clr9 = "#ffffff";
  var clr10 = "#b3b3b3";
  var clr11 = "#ddffff";
  var clr12 = "#dfdfdf";
  var clr13 = "#aaccee";
  var clr14 = "#aaeeee";
  var clr15 = "#bbddee";
  var clr16 = "#eeffff";
  var clr17 = "#00ff00";
  var clr18 = "#D6E8F8";
  var dark_grey = "#414141";

  var btn_kpv = [207,223,226,233,245,250];
  var btn_id_on = ['beam_on','usb_485_on','pc_tcp_on','meter_232_on','meter_tcp_on','per_auto_on'];
  var btn_id_off = ['beam_off','usb_485_off','pc_tcp_off','meter_232_off','meter_tcp_off','per_auto_off'];
  var kpv_links_index = [133,134,136,137,
                         150,151,152,153];
  var kpv_links_id = ['steady_dbnd_dp','steady_time_dp','num_mark_dp','num_cal_pts_dp',
                      'steady_dbnd_sp','steady_time_sp','num_mark_sp','num_cal_pts_sp'];
    
  socket.onopen = function() {
    console.log("connected");
    sendMessage({ 'dest':'qk1', 'purpose':'request_kpv', 'data' : '1'});
    setTimeout(function(){user_activity()},5000)
  }

  socket.onclose = function(){
    //console.log("disconnected from server");
    logout_user = get_active_user();
    $.ajax({url:'/settings',type:'POST',data:{'purpose':'logout','user':logout_user}})
    document.getElementById('s0').remove();
    if (exists('s1')){
      document.getElementById('s1').remove()
    }
    var dis = document.createElement('div');
    dis.setAttribute('id','dis');
    dis.setAttribute('class','dis');
    document.getElementById('body').appendChild(dis);
    document.getElementById('dis').textContent = "Disconnected from server";
  };

  // message received from the socket
  socket.onmessage = function (message) {
    //console.log("receiving: " + message.data);
    if (JSON.parse(message.data).dest == 'get_user_list'){
      window.user_list = JSON.parse(message.data).all_users
      show_users_sec_function(1);
    }
    
    if (JSON.parse(message.data).dest == 'user_privilege_level'){
      let user = JSON.parse(message.data).user;
      let root_user = parseInt(JSON.parse(message.data).root_user);
      //console.log('user(' + user + ') root(' + root_user + ')')
      if (root_user != 1) {
        remove_root_sections(1)
      }
      // post current user on page
      window.skytek_active_user = user;
      window.active_user_root = root_user;
      post_user(skytek_active_user, active_user_root);
    }

    if (JSON.parse(message.data).dest == 'message'){
      message = JSON.parse(message.data).message;
      mod_msg_box(message);
    }

    if (JSON.parse(message.data).dest == 'add_user'){
      let success = JSON.parse(message.data).success
      if (parseInt(success)==1) {
        $('#sec_new_user').remove()
      }
    }
      
    if (JSON.parse(message.data).dest == 'user_removal'){
      let user = JSON.parse(message.data).user;
      let found = parseInt(JSON.parse(message.data).found);
      let root = parseInt(JSON.parse(message.data).root);
      if (found == 1) {
        if (root == 0){
          console.log('user not root');
          $('#remove_user_input').prop('disabled',true);
          $('#remove_user_submit_btn').prop('disabled',true);
          if (document.querySelector('#confirm_remove_user_btn') == null){
            let ss = document.getElementById('sec_remove_user');
              append_row(ss)
                append_btn(ss,3,'confirm_remove_user_btn','Confirm user removal')
                confirm_remove_user_btn_function(user);
          }          }
        else { // user is root
          mod_msg_box('Cannot remove root user - Assign root privilege to different user first')
        }
      }
      else { // user not found
        mod_msg_box('User (' + user + ') not found');
      }
    }

    if (JSON.parse(message.data).dest == 'user_removed'){
      if (document.querySelector('#sec_remove_user') != null) {
        $('#sec_remove_user').remove();
      }
    }


    if (JSON.parse(message.data).dest == 'change_root'){
      let user = JSON.parse(message.data).user;
      let found = parseInt(JSON.parse(message.data).found);
      if (found == 1) {
        $('#change_root_input').prop('disabled',true);
        $('#change_root_submit_btn').prop('disabled',true);
        if (document.querySelector('#confirm_change_root_btn') == null){
          let ss = document.getElementById('sec_change_root');
            append_row(ss)
              append_btn(ss,2,'confirm_change_root_btn','Confirm change root')
              confirm_change_root_btn_function(user);
        }
      }
      else { // user not found
        mod_msg_box('User (' + user + ') not found');
      }
    }

    if (JSON.parse(message.data).dest == 'root_changed'){
      new_user = JSON.parse(message.data).user;
      if (exists('sec_change_root')){
        $('#sec_change_root').remove();
      }
      let cookie = get_active_user();
      if (cookie != new_user){
        remove_root_sections(1);
        post_user(cookie, 0);
      }
    }

    if (JSON.parse(message.data).dest == 'user_logged_out'){
      let lo_user = JSON.parse(message.data).user;
      mod_msg_box('User (' + lo_user + ') logged out. Redirecting')
      setTimeout(function(){window.open(base_addr + '/','_self')},2000);
    }

    if (JSON.parse(message.data).dest == 'inactivity_logout'){
      let logout_user = get_active_user;
      console.log("logging out user(" + logout_user + " due to inactivity")
      mod_msg_box("logging out user(" + logout_user + " due to inactivity")
      $.ajax({url:'/logout',type:'GET',data:{'purpose':'logout','user':logout_user}})
      setTimeout(function(){window.open(base_addr + '/login','_self')},5000)
    }

    if (JSON.parse(message.data).dest == 'kpv'){
      //console.log("receiving initial kpv");

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

      //console.log("initial kpv received");
      load_s0() // generate main default sections
      init_states()
      init_vals()
      //console.log(kpv_val)
    } // if dest = kpv

    if (JSON.parse(message.data).dest == 'kpv_update'){
      let index = parseInt(JSON.parse(message.data).index);
      let val = JSON.parse(message.data).val;
      kpv_val[index] = castDataType(index,val);
      if (exists('s1')){ 
        check_kpv_links(index,val);
        c0inp_id = "s1r" + index + "c0inp";
        document.getElementById(c0inp_id).value = kpv_val[index]
      }
      init_states();
      init_vals()
    }
    
  }; // socket.onmessage

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
      console.log("Not able to castDataType for kpv[" + indx + "]")
    }
  }
  
  // update values in input boxes in section 0
  var check_kpv_links = function(idx,vl){
    for(let s = 0;s < kpv_links_index.length; s++){
      if(idx == kpv_links_index[s]){      
        if (document.getElementById('s0').querySelector('#' + kpv_links_id[s]) != null){
          document.getElementById(kpv_links_id[s]).value = vl;  
        }
        break;
      }
    }
  }

  var init_vals = function(){
    for (let i = 0;i<kpv_links_index.length;i++) {
      check_kpv_links(kpv_links_index[i],kpv_val[kpv_links_index[i]])
    }
  }

  // generate main default sections
  var load_s0 = function(){
    // main settings section
    let ss00 = append_ss('sec_user_lbl');
      append_row(ss00);
        append_msg_box(ss00,1,'user_lbl');
    let ss0 = append_ss('message');
      let ssr = append_row(ss0);
        append_msg_box(ss0,1,'msg_box');
    let ss1 = append_ss('sec_user');
      ssr = append_row(ss1);
        append_btn(ss1,1,'logout_btn','Logout');
        logout_btn_function();
        append_btn(ss1,1,'add_new_user_btn','Add new user');
        add_new_user_btn_function();
        append_btn(ss1,1,'show_users_sec_btn','Show user list');
        show_users_sec_btn_function()
      append_row(ss1);        
        append_btn(ss1,2,'remove_user_btn','Remove a user');
        remove_user_btn_function();
        append_btn(ss1,2,'change_root_btn','Change root user');
        change_root_btn_function();
        append_btn(ss1,2,'kpv_database_btn','Settings database');
        kpv_database_btn_function()
    let ss2 = append_ss('sec_ctrl_link');    
      ssr = append_row(ss2)
        append_btn(ss2,1,'controls_btn','Controls page');
        controls_btn_function()
        append_btn(ss2,1,'graphs_btn','Graphs');
        $('#graphs_btn').click(function(){window.open(base_addr + '/graphs','_blank')})        
    sub_sec = append_ss_wt('sec_main','Main settings');
      ssr1 = append_row(sub_sec);
        append_lbl(sub_sec,1,'PC TCP connection to RPI)');
        btn_grp_exc_pc_tcp = ['pc_tcp_on','pc_tcp_off'];
        btn_grps_exc.push(btn_grp_exc_pc_tcp);
        append_btn(sub_sec,1,'pc_tcp_on','Enable');
        append_btn(sub_sec,1,'pc_tcp_off','Disable');
        pc_tcp_on_btn_function();
        pc_tcp_off_btn_function();
      ssr2 = append_row(sub_sec);
        append_lbl(sub_sec,2,'RPI TCP to flowmeter');
        btn_grp_exc_meter_tcp = ['meter_tcp_on','meter_tcp_off'];
        btn_grp_exc_meter_tcp = ['meter_tcp_on','meter_tcp_off'];
        btn_grps_exc.push(btn_grp_exc_meter_tcp);
        append_btn(sub_sec,2,'meter_tcp_on','Enable');
        append_btn(sub_sec,2,'meter_tcp_off','Disable');
        meter_tcp_on_btn_function();
        meter_tcp_off_btn_function();
      ssr3 = append_row(sub_sec);
        append_lbl(sub_sec,3,'RPI beam sensor signals');
        btn_grp_exc_beam_enable = ['beam_on','beam_off'];
        btn_grps_exc.push(btn_grp_exc_beam_enable);
        append_btn(sub_sec,3,'beam_on','Enable');
        append_btn(sub_sec,3,'beam_off','Disable');
        beam_on_btn_function();
        beam_off_btn_function();
      ssr4 = append_row(sub_sec);
        append_lbl(sub_sec,4,'RPI USB485 temperature signals');
        btn_grp_exc_usb_485_enable= ['usb_485_on','usb_485_off'];
        btn_grps_exc.push(btn_grp_exc_usb_485_enable);
        append_btn(sub_sec,4,'usb_485_on','Enable');
        append_btn(sub_sec,4,'usb_485_off','Disable');
        usb_485_on_btn_function();
        usb_485_off_btn_function();
      ssr5 = append_row(sub_sec);
        append_lbl(sub_sec,5,'RPI rsS32 to flowmeter');
        btn_grp_exc_meter_232_enable= ['meter_232_on','meter_232_off'];
        btn_grps_exc.push(btn_grp_exc_meter_232_enable);
        append_btn(sub_sec,5,'meter_232_on','Enable');
        append_btn(sub_sec,5,'meter_232_off','Disable');
        meter_232_on_btn_function();
        meter_232_off_btn_function();
      ssr6 = append_row(sub_sec);
        append_lbl(sub_sec,6,'Periodic auto calibration check');
        btn_grp_exc_per_auto= ['per_auto_on','per_auto_off'];
        btn_grps_exc.push(btn_grp_exc_per_auto);
        append_btn(sub_sec,6,'per_auto_on','Enable');
        append_btn(sub_sec,6,'per_auto_off','Disable');
        per_auto_on_btn_function();
        per_auto_off_btn_function();
    // main settings section

    // calibration section
    sub_sec1 = append_ss_wt('sec_cal','Calibration settings');
      ssr1 = append_row(sub_sec1);
        append_lbl(sub_sec1,1,'DP steady deadband (inh20)');
        append_input(sub_sec1,1,'steady_dbnd_dp','number','0');
        steady_dbnd_dp_input_function();
      ssr2 = append_row(sub_sec1);
        append_lbl(sub_sec1,2,'DP steady time (seconds)');
        append_input(sub_sec1,2,'steady_time_dp','number','0');
        steady_time_dp_input_function();
      ssr3 = append_row(sub_sec1);
        append_lbl(sub_sec1,3,'SP steady deadband (psi)');
        append_input(sub_sec1,3,'steady_dbnd_sp','number','0');
        steady_dbnd_sp_input_function();
      ssr4 = append_row(sub_sec1);
        append_lbl(sub_sec1,4,'SP steady time (seconds)');
        append_input(sub_sec1,4,'steady_time_sp','number','0');
        steady_time_sp_input_function();
    // calibration section
  };

  var load_s1 = function(){
    var s = 1;
    var s_id = "s" + s;
    for(let r = 0; r < kpv_val.length; r++) {
      check_kpv_links(r,kpv_val[r]);
      let row = document.createElement('div')
      r_id = "s" + s + "r" + r
      row.setAttribute('id',r_id)
      row.setAttribute('class','kpv_row')

      let val = document.createElement('div')
      c0_id = "s" + s + "r" + r + "c0"
      val.setAttribute('id',c0_id)
      val.setAttribute('class','val')

      let inp = document.createElement('input')
      c0inp_id = "s" + s + "r" + r + "c0inp"
      inp.setAttribute('id',c0inp_id)
      inp.setAttribute('type','text')
      inp.setAttribute('class','number_input')
      //inp.setAttribute('value',Number(kpv_val[r]))
      inp.setAttribute('value',(kpv_val[r]))

      let index = document.createElement('div')
      c1_id = "s" + s + "r" + r + "c1";
      index.setAttribute('id',c1_id)
      index.setAttribute('class','index')

      let des = document.createElement('div')
      c2_id = "s" + s + "r" + r + "c2";
      des.setAttribute('id',c2_id)
      des.setAttribute('class','des')

      document.getElementById(s_id).appendChild(row)
      document.getElementById(r_id).appendChild(val)
      document.getElementById(c0_id).appendChild(inp)
      document.getElementById(r_id).appendChild(index)
      document.getElementById(c1_id).textContent = "[" + r + "] {" + kpv_type[r] + "}"
      document.getElementById(r_id).appendChild(des)
      document.getElementById(c2_id).textContent = kpv_des[r]

      // convert to jquery spinner
      sel = "#" + c0inp_id
      $(function() {
        if (kpv_type[r] == 'f'){
          $( sel ).spinner({
            step : 0.1,
            min : -10.0,
            max : 10000.0,
            change: function(){mod_kpv(this.id, this.value)}
          });
        }
        else if (kpv_type[r] == 'i'){
          $( sel ).spinner({
            step : 1,
            min : -10,
            max : 10000,
            change: function(){mod_kpv(this.id, this.value)}
          });
        }
        else if (kpv_type[r] == 's'){
          $(sel).change(function(){
          mod_kpv(this.id, this.value);
          });
        }
      }); // convert to jquery spinner
    } // create row elements
    remove_temp()
  }

  var remove_temp = function(){
    document.getElementById('temp').remove() // loading indicator
  }
  
  var init_states = function(){
    let user = get_active_user();
    $.ajax({url:'/settings',type:'POST',data:{'purpose':'check_user_privilege_level','user':user}})
    for (let i = 0 ; i < btn_kpv.length ; i++){
      if (kpv_val[btn_kpv[i]] == 0) {
        document.getElementById(btn_id_on[i]).click();
      }
      else {
        document.getElementById(btn_id_off[i]).click();
      }
    }
  }
  
  var mod_kpv = function(id, val, type=0) {
    row = id;
    //console.log("id : " + id + "  val : " + val);
    if (type == 0) {
      row = id.slice(3,Number(id.indexOf("c")))
    }
    if (val != kpv_val[row]) {
      Dict = {"row":row, "val":val}
      sendMessage({ 'dest':'qk3', 'purpose':'mod_kpv', 'data':Dict});
    }
  }

  // send a message to the server
  var sendMessage = function(message) {
    //console.log("sending:" + message.data);
    socket.send(JSON.stringify(message));
  };

  var btn_on = function(btn,clr='#00ff00'){
    var found = 0;
    for (nkey in btn_grps_exc){
      for (nkey2 in btn_grps_exc[nkey]) {
        if (btn_grps_exc[nkey][nkey2] == btn) {
          for (nkey3 in btn_grps_exc[nkey]) {
            if (btn_grps_exc[nkey][nkey3] == btn) {
              btn_on_exc(btn_grps_exc[nkey][nkey3]);
            }
            else {
              btn_off(btn_grps_exc[nkey][nkey3]);
            }
          };
          found = 1;
        };
        if (found == 1){break;};
      };
      if (found == 1){break;};
    };
    // turn off other buttons if in exclusive button group

    // button not in exclusive button group - activate button
    if (found == 0) {
      document.getElementById(btn).disabled = false;
      document.getElementById(btn).value = 1;
      document.getElementById(btn).active = 1;
      document.getElementById(btn).focus = 1;
      document.getElementById(btn).visited = 1;
      document.getElementById(btn).style.background = clr;
      document.getElementById(btn).style.color = "#000000";
    };
  };

  var btn_off = function(btn, clr=btn_clr){
    document.getElementById(btn).disabled = false;
    document.getElementById(btn).value = 0;
    document.getElementById(btn).active = 0;
    document.getElementById(btn).focus = 0;
    document.getElementById(btn).visited = 0;
    document.getElementById(btn).style.background = clr;
    document.getElementById(btn).style.color = "#000000";
  };

  var btn_grp_enable = function(btn_grp){
    for (key in btn_grp) {
      document.getElementById(btn_grp[key]).disabled = false;
    };
  };

  var btn_grp_disable = function(btn_grp){
    for (key in btn_grp) {
      document.getElementById(btn_grp[key]).disabled = true;
    };
  };

  var btn_on_exc = function(btn){
    //console.log(btn)
    document.getElementById(btn).disabled = true;
    document.getElementById(btn).value = 0;
    document.getElementById(btn).active = 0;
    document.getElementById(btn).focus = 0;
    document.getElementById(btn).visited = 0;
    document.getElementById(btn).style.background = clr17;
    document.getElementById(btn).style.color = dark_grey;
  };

  var btn_enable = function(btn){
    document.getElementById(btn).disabled = false;
  };

  var btn_disable = function(btn){
    document.getElementById(btn).disabled = true;
  };

  var add_new_user_btn_function = function(){
    $('#add_new_user_btn').click(function(){
      if (document.querySelector('#sec_new_user') == null) {
        let ss = append_ss_wt('sec_new_user','Add new user');
          append_row(ss)
            append_lbl(ss,1,'New user');
            append_input(ss,1,'new_user_input')
          append_row(ss)
            append_lbl(ss,2,'Password');
            append_input(ss,2,'new_passw_input')
          append_row(ss)
            append_lbl(ss,3,'Confirm password');
            append_input(ss,3,'new_passw_input_confirm')          
          append_row(ss)
            append_btn(ss,4,'save_new_user_btn','Save new user');
            save_new_user_btn_function();
          append_row(ss)
            append_btn(ss,5,'cankeydowncel_new_user_btn','Cancel');
            cancel_new_user_btn_function();            
      }
      else {
        $('#sec_new_user').remove();
      }
    })
  }

  var save_new_user_btn_function = function(){
    $('#save_new_user_btn').click(function(){
      nui = document.getElementById('new_user_input').value;
      npi = document.getElementById('new_passw_input').value;
      npic = document.getElementById('new_passw_input_confirm').value;
      if (nui == null || nui.length < 5 || nui == ""){
        mod_msg_box("Username must be at least 5 character long");
      }
      else if (nui == "skytek" && npi == "skytek"){
        mod_msg_box("Username and password must be changed from default");
      }
      else if (nui == npi){
        mod_msg_box("Username and password must be different");
      }          
      else if (npi == null || npi.length < 5 || npi == ""){
        mod_msg_box("Password must be at least 5 character long");
      }
      else if (npic != npi){
        mod_msg_box("Passwords do not match");
      }
      else {
        $.ajax({url:'/settings',type:'POST',data:{'purpose':'new_user','user':nui,'password':npi}})
      }      
    })
  }

  var cancel_new_user_btn_function = function() {
    $('#cancel_new_user_btn').click(function(){
      if (document.querySelector('#sec_new_user') != null) {
        $('#sec_new_user').remove();
      }
    })
  }
  
  var remove_user_btn_function = function(){
    $('#remove_user_btn').click(function(){
      if (document.querySelector('#sec_remove_user') == null) {
        let ss = append_ss_wt('sec_remove_user','Remove user');
          append_row(ss)
            append_lbl(ss,1,'User');
            append_input(ss,1,'remove_user_input')
          append_row(ss)
            append_btn(ss,2,'remove_user_submit_btn','Remove user');
            remove_user_submit_btn_function();
          append_row(ss)
            append_btn(ss,3,'cancel_remove_user_btn','Cancel');
            cancel_remove_user_btn_function();
      }
      else {
        $('#sec_remove_user').remove();
      }
    })
  }

  var remove_user_submit_btn_function = function(){
    $('#remove_user_submit_btn').click(function(){
      let r_user = document.getElementById('remove_user_input').value;
      if (r_user == '' || r_user == null) {
        mod_msg_box('Enter a username');
      }
      else {
        $.ajax({url:'/settings',type:'POST',data:{'purpose':'user_removal','user':r_user}})
      }
    })
  }

  var confirm_remove_user_btn_function = function(user){
    $('#confirm_remove_user_btn').click(function(){
      let user = document.getElementById('remove_user_input').value;
      $.ajax({url:'/settings',type:'POST',data:{'purpose':'remove_user','user':user}})
      $('#sec_new_user').remove();
    })
  }

  var cancel_remove_user_btn_function = function() {
    $('#cancel_remove_user_btn').click(function(){
      if (document.querySelector('#sec_remove_user') != null) {
        $('#sec_remove_user').remove();
      }
    })
  }

  var change_root_btn_function = function(){
    $('#change_root_btn').click(function(){
      if (document.querySelector('#sec_change_root') == null) {
        let ss = append_ss_wt('sec_change_root','Assign new root user');
          append_row(ss)
            append_lbl(ss,1,'User');
            append_input(ss,1,'change_root_input')
          append_row(ss)
            append_btn(ss,2,'change_root_submit_btn','Assign new root user');
            change_root_submit_btn_function();
          append_row(ss)
            append_btn(ss,3,'cancel_change_root_btn','Cancel');
            cancel_change_root_btn_function();
      }
      else {
        $('#sec_change_root').remove();
      }
    })    
  }

  var change_root_submit_btn_function = function(){
    $('#change_root_submit_btn').click(function(){
      let r_user = document.getElementById('change_root_input').value;
      if (r_user == '' || r_user == null) {
        mod_msg_box('Enter a username');
      }
      else {
        $.ajax({url:'/settings',type:'POST',data:{'purpose':'change_root_check','user':r_user}})
      }
    })
  }  

  var confirm_change_root_btn_function = function(user){
    $('#confirm_change_root_btn').click(function(){
      let user = document.getElementById('change_root_input').value;
      $.ajax({url:'/settings',type:'POST',data:{'purpose':'change_root','user':user}})
      $('#sec_change_root').remove();
    })
  }

  var cancel_change_root_btn_function = function() {
    $('#cancel_change_root_btn').click(function(){
      if (document.querySelector('#sec_change_root') != null) {
        $('#sec_change_root').remove();
      }
    })
  }
  
  var pc_tcp_on_btn_function = function(){
    $("#pc_tcp_on").click(function(){
      btn_on('pc_tcp_on');
      mod_kpv(226,0,1)
	    sub_sec = append_ss_wt('sec_local_pc','Local PC connection');
        ssr1 = append_row(sub_sec);
	  	    append_lbl(sub_sec,1,'Type of flowmeter (for PC to RPI local)');
          btn_grp_exc_tflow_roc = ['meter_type_totalflow','meter_type_roc'];
          btn_grps_exc.push(btn_grp_exc_tflow_roc);
          append_btn(sub_sec,1,'meter_type_totalflow','Totalflow');
          append_btn(sub_sec,1,'meter_type_roc','ROC');
          meter_type_totalflow_btn_function();
          meter_type_roc_btn_function();
	  	  ssr2 = append_row(sub_sec);
	  	    append_lbl(sub_sec,2,'Number of DP markers for auto-mark');
	  	    append_input(sub_sec,2,'num_mark_dp','number','5');
          num_mark_dp_input_function();
	  	  ssr3 = append_row(sub_sec);
          append_lbl(sub_sec,3,'Number of DP calibration points for auto-cal');
          append_input(sub_sec,3,'num_cal_pts_dp','number','5');
          num_cal_pts_dp_input_function();
	  	  ssr4 = append_row(sub_sec);
  	  	  append_lbl(sub_sec,4,'Number of SP markers for auto-mark');
	  	    append_input(sub_sec,4,'num_mark_sp','number','3');
          num_mark_sp_input_function();
	  	  ssr5 = append_row(sub_sec);
          append_lbl(sub_sec,5,'Number of SP calibration points for auto-cal');
          append_input(sub_sec,5,'num_cal_pts_sp','number','3');
          num_cal_pts_sp_input_function();
    });
  };

  var pc_tcp_off_btn_function = function(){
    $("#pc_tcp_off").click(function(){
      btn_on('pc_tcp_off');
      mod_kpv(226,1,1)
      if (document.getElementById('s0').querySelector('#sec_local_pc') != null){
        document.getElementById('s0').removeChild(sec_local_pc);
      };
    });
  };

  var meter_tcp_on_btn_function = function(){
    $("#meter_tcp_on").click(function(){
      btn_on('meter_tcp_on');
      mod_kpv(245,0,1)
    });
  };

  var meter_tcp_off_btn_function = function(){
    $("#meter_tcp_off").click(function(){
      btn_on('meter_tcp_off');
      mod_kpv(245,1,1)
    });
  };

  var beam_on_btn_function = function(){
    $("#beam_on").click(function(){
      btn_on('beam_on');
      mod_kpv(207,0,1)
    });
  };

  var beam_off_btn_function = function(){
    $("#beam_off").click(function(){
      btn_on('beam_off');
      mod_kpv(207,1,1)
    });
  };

  var usb_485_on_btn_function = function(){
    $("#usb_485_on").click(function(){
      btn_on('usb_485_on');
      mod_kpv(223,0,1)
    });
  };

  var usb_485_off_btn_function = function(){
    $("#usb_485_off").click(function(){
      btn_on('usb_485_off');
      mod_kpv(223,1,1)
    });
  };

  var meter_232_on_btn_function = function(){
    $("#meter_232_on").click(function(){
      btn_on('meter_232_on');
      mod_kpv(233,0,1)
    });
  };

  var meter_232_off_btn_function = function(){
    $("#meter_232_off").click(function(){
      btn_on('meter_232_off');
      mod_kpv(233,1,1);
    });
  };

  var per_auto_on_btn_function = function(){
    $("#per_auto_on").click(function(){
      btn_on('per_auto_on');
      mod_kpv(250,0,1);
      sub_sec = append_ss_wt('sec_per_type','Periodic Auto Calibration Interval Type');
        append_row(sub_sec);
        btn_grp_exc_per_auto = ['period_btn','schedule_btn','specific_dates_btn'];
        btn_grps_exc.push(btn_grp_exc_per_auto);
        append_btn(sub_sec,1,'period_btn','Period');
        period_btn_function();
        append_btn(sub_sec,1,'schedule_btn','Schedule');
        schedule_btn_function();
        append_btn(sub_sec,1,'specific_dates_btn','Specific Dates');
        specific_dates_btn_function();        
    });
  };

  var per_auto_off_btn_function = function(){
    $("#per_auto_off").click(function(){
      btn_on('per_auto_off');
      mod_kpv(250,1,1);
      if (document.getElementById('s0').querySelector('#sec_per_type') != null){
        document.getElementById('s0').removeChild(sec_per_type);
      };
      if (document.getElementById('s0').querySelector('#sec_per_auto') != null){
        document.getElementById('s0').removeChild(sec_per_auto);
      };
    });
  };

  var period_btn_function = function(){
    $("#period_btn").click(function(){
    btn_on('period_btn');
    //mod_kpv(250,1,1);
    if (document.getElementById('s0').querySelector('#sec_per_auto') != null){
      document.getElementById('s0').removeChild(sec_per_auto);
    };
    sub_sec = append_ss_wt('sec_per_auto','Period interval');
      ssr1 = append_row(sub_sec);
        append_btn(sub_sec,1,'start_per_auto_button','Submit auto test interval');            
      ssr2 = append_row(sub_sec);
        btn_grp_exc_months_days = ['months_btn','days_btn'];
        btn_grps_exc.push(btn_grp_exc_months_days);
        append_lbl(sub_sec,2,'Every');
        append_input(sub_sec,2,'per_interval','number','1');
        append_btn(sub_sec,2,'days_btn','Days');
        days_btn_function();
        append_btn(sub_sec,2,'months_btn','Months');
        months_btn_function()
      ssr3 = append_row(sub_sec);
        append_lbl(sub_sec,3,'at');
        append_input(sub_sec,3,'auto_time','time','00:00');
    });
  };

  var schedule_btn_function = function(){
    $("#schedule_btn").click(function(){
    btn_on('schedule_btn');
    //mod_kpv(250,1,1);
    if (document.getElementById('s0').querySelector('#sec_per_auto') != null){
      document.getElementById('s0').removeChild(sec_per_auto);
    };
    sub_sec = append_ss_wt('sec_per_auto','Schedule interval');
      ssr1 = append_row(sub_sec);
        append_btn(sub_sec,1,'start_per_auto_button','Submit auto test interval');            
      ssr2 = append_row(sub_sec);
        append_lbl(sub_sec,2,'Test time');
        append_input(sub_sec,1,'auto_time','time','00:00');
  });
  };

  var days_btn_function = function(){
    $("#days_btn").click(function(){
    btn_on('days_btn');
    //mod_kpv(250,1,1);
  });
  };

  var months_btn_function = function(){
    $("#months_btn").click(function(){
    btn_on('months_btn');
    //mod_kpv(250,1,1);
  });
  };  
  
  var specific_dates_btn_function = function(){
    $("#specific_dates_btn").click(function(){
    btn_on('specific_dates_btn');
    //mod_kpv(250,1,1);
    if (document.getElementById('s0').querySelector('#sec_per_auto') != null){
      document.getElementById('s0').removeChild(sec_per_auto);
    };
    sub_sec = append_ss_wt('sec_per_auto','Specific dates interval');
      ssr1 = append_row(sub_sec);
        append_btn(sub_sec,1,'start_per_auto_button','Submit auto test interval');        
      ssr2 = append_row(sub_sec);
        append_lbl(sub_sec,2,'Test at');
        append_input(sub_sec,2,'auto_time','time','00:00');
        append_lbl(sub_sec,2,' on the following dates');
      ssr3 = append_row(sub_sec);
        append_btn(sub_sec,3,'add_date_btn','Add date');        
        add_date_btn_function();
      ssr4 = append_row(sub_sec);
        append_input(sub_sec,4,'date_0','date','00/00/00');
        append_img_btn(sub_sec,4,'del_btn_0',del_icon_src);
  });
  };

  var add_date_btn_function = function() {
    $('#add_date_btn').click(function(){
      let idn = get_next_idn();
      let nd = document.getElementById('sec_per_auto').childNodes.length;
      let ssr = append_row(sec_per_auto);
        append_input(sub_sec,nd,'date_' + idn,'date','00/00/00');
        append_img_btn(sub_sec,nd,'del_btn_' + idn,del_icon_src);
    });
  };

  // keep delete buttons in order
  var get_next_idn = function(){
    cna = [];
    cn = document.getElementById('sec_per_auto').childNodes;
    if (cn.length < 5) { // all date rows were deleted
      return 0;
    }
    for (let i=4;i<cn.length;i++) {
      let cid = cn[i].lastChild.id;
      cid = cid.replace('del_btn_','')
      cid = parseInt(cid)
      cna.push(cid);
    }
    cna.sort(function(a,b){return a - b});
    jk = 0;
    for (let i=0;i<365;i++) {
      if (jk < cna.length) {
        if(cna[jk] != i) {
          return i;
        }
        else {
          jk ++;
        }
      }
      else {
        return cna[jk-1] + 1;
      } 
    }
  };
  
  var meter_type_totalflow_btn_function = function(){
    if (kpv_val[246] == 0) {
      btn_on('meter_type_totalflow');
    };
    $("#meter_type_totalflow").click(function(){
      btn_on('meter_type_totalflow');
      mod_kpv(246,0,1)
    });
  };

  var meter_type_roc_btn_function = function(){
    if (kpv_val[246] == 1){
      btn_on('meter_type_roc');
    };
    $("#meter_type_roc").click(function(){
      btn_on('meter_type_roc');
      mod_kpv(246,1,1);
    });
  };

  var steady_dbnd_dp_input_function = function() {
    $('#steady_dbnd_dp').change(function(){
      mod_kpv(133, this.value,1);
    });
  };

  var steady_time_dp_input_function = function() {
    $('#steady_time_dp').change(function(){
      mod_kpv(134, this.value,1)
    });
  };  
  
  var steady_dbnd_sp_input_function = function() {
    $('#steady_dbnd_sp').change(function(){
      mod_kpv(150, this.value,1)
    });
  };  
  
  var  steady_time_sp_input_function = function() {
    $('#steady_time_sp').change(function(){
      mod_kpv(151, this.value,1)
    });
  };     
  
  var  num_mark_dp_input_function = function() {
    $('#num_mark_dp').change(function(){
      mod_kpv(136, this.value,1)
    });
  };     
  
  var  num_cal_pts_dp_input_function = function() {
    $('#num_cal_pts_dp').change(function(){
      mod_kpv(137, this.value,1)
    });
  };     
  
  var  num_mark_sp_input_function = function() {
    $('#num_mark_sp').change(function(){
      mod_kpv(152, this.value,1)
    });
  };     
  
  var  num_cal_pts_sp_input_function = function() {
    $('#num_cal_pts_sp').change(function(){
      mod_kpv(153, this.value,1)
    });
  };       

  var controls_btn_function = function() {
    $('#controls_btn').click(function(){
      var sw = window.screen.width * window.devicePixelRatio;
      var sh = window.screen.height * window.devicePixelRatio;
      var ww = Math.floor(sw * 0.3);
      var wh = Math.floor(sh * 0.95);
      window.open(base_addr + '/controls','_blank','width=' + ww + ', height=' + wh);
    });
  };

///////////////////////////////////////////////////////////////
  var getSibling = function(ss,row){
    rown = ss.firstChild
    for (let i = 0;i < row;i++) {
      rown = rown.nextSibling;
    };
    return rown;
  };

  var append_msg_box = function(ss,row,id){
    let div = document.createElement('div');
    div.setAttribute('id',id);
    div.setAttribute('class','message');
    rown = getSibling(ss,row);
    rown.appendChild(div);
    mod_msg_box('---');
  }
  
  var append_lbl = function(ss,row,text){
    var lbl = document.createElement('input');
    lbl.setAttribute('value',text);
    lbl.setAttribute('disabled','1');
    rown = getSibling(ss,row);
    rown.appendChild(lbl);
  };

  var append_img = function(ss,row,id,img_src) {
    var img = document.createElement('img');
    img.setAttribute('id','del_icon_' + id);
    img.setAttribute('src',img_src);
    img.setAttribute('class','del_icon');
    rown = getSibling(ss,row);
    rown.appendChild(img);
  };

  var append_input = function(ss,row,id,type,val=''){
    var input = document.createElement('input');
    input.setAttribute('id',id);
    input.setAttribute('type',type);
    input.setAttribute('value',val);
    rown = getSibling(ss,row);
    rown.appendChild(input);
  };

  var append_ss = function(id){
    main = document.getElementById('s0');
    var s_id = document.createElement('div');
    s_id.setAttribute('id',id);
    s_id.setAttribute('class','s0s');
    main.appendChild(s_id);
    ss = document.getElementById(id);
    var ssr = document.createElement('div');
    ssr.setAttribute('class','s0sr');
    ss.appendChild(ssr);
    return ss;
  };

  var append_ss_wt = function(id,text){
    main = document.getElementById('s0');
    var s_id = document.createElement('div');
    s_id.setAttribute('id',id);
    s_id.setAttribute('class','s0s');
    main.appendChild(s_id);
    ss = document.getElementById(id);
    var ssr = document.createElement('div');
    ssr.setAttribute('class','s0sr');
    ss.appendChild(ssr);
    row = ss.firstChild;
    var title = document.createElement('input');
    title.setAttribute('type','text');
    title.setAttribute('class','sec_title');
    title.setAttribute('value',text);
    row.appendChild(title);
    return ss;
  };

  var append_row = function(ss){
    var row = document.createElement('div');
    row.setAttribute('class','s0sr');
    ss.appendChild(row);
  };

  var append_btn = function(ss,row,id,text){
    var btn = document.createElement('button');
    btn.setAttribute('id',id);
    rown = getSibling(ss,row);
    rown.appendChild(btn);
    jq_id = "#" + id;
    $(jq_id).text(text);
  };

  var append_img_btn = function(ss,row,id,img_src){
    var btn = document.createElement('img');
    btn.setAttribute('id', id);
    btn.setAttribute('src',img_src);
    btn.setAttribute('class','del_icon');
    rown = getSibling(ss,row);
    rown.appendChild(btn);
    img_btn_function(id);
  };  

  var img_btn_function = function(id) {
    $('#' + id).click(function(){
      document.getElementById(id).parentNode.remove();
    });
  };     

  var mod_msg_box = function(msg){
    $('#msg_box').empty();
    $('#msg_box').append(msg);
    setTimeout(function(){$('#msg_box').empty();},5000)
  };

  var remove_root_sections = function(i = 0){
    if (i == 1){
      for (sec in root_sections) {
        if (exists(root_sections[sec])) {
          $('#'+root_sections[sec]).remove();
        }
      }
    }
  }

  var get_active_user = function() {
   page_user = document.cookie.split('; ').find(row => row.startsWith('skytek_active_user')).split('=')[1];
   return page_user;
  }

  var post_user = function(user, root_user){
    txt = 'no';
    if (root_user == 1) {
      txt = 'yes';
    }
    $('#user_lbl').text('(User)  ' + user + '   (root) : ' + txt);
  }

  var toggle_element = function(element) {
    if (exists(element)) {
      $('#'+element).remove()
      return true
    }
    return false
  }
  
  var get_user_list = function(){
    $.ajax({url:'/settings',type:'POST',data:{'purpose':'get_user_list'}})        
  }

  var show_users_sec_btn_function = function() {
    $('#show_users_sec_btn').click(function(){
      if (toggle_element('sec_show_users')) {
        null
      }
      else {
        get_user_list();
      }
    })
  }
  
  var show_users_sec_function = function(i=0) {
    if (i == 1) {
      let ss = append_ss('sec_show_users')
      append_row(ss); // 1
        append_lbl(ss,0,'Current users')
        let table = document.createElement('div')
          table.setAttribute('id','user_list_table')
          table.setAttribute('class','user_list_table')
          document.getElementById('sec_show_users').firstChild.append(table)
          for (var r in user_list){
            let tr = document.createElement('div')
            document.getElementById('user_list_table').append(tr)
              append_lbl(table,r,user_list[r])
      }
    }
  }

  var kpv_database_btn_function = function(){
    $('#kpv_database_btn').click(function(){
      if (!toggle_element('s1')){
        let s1 = document.createElement('div')
        s1.setAttribute('class','s1')
        s1.setAttribute('id','s1')
        document.getElementById('body').appendChild(s1)
          let temp = document.createElement('div')
          temp.setAttribute('class','temp')
          temp.setAttribute('id','temp')
          temp.setAttribute('style','text-align:center')
          document.getElementById('s1').appendChild(temp)
          $('#temp').text('Loading')
          setTimeout(function(){load_s1()},2000)
      }
    })
  }
  
  var exists = function(id){
    if(document.querySelector('#'+id) == null){
      return false
    }
    else{
      return true
    }
  }

  var logout_btn_function = function() {
    $('#logout_btn').click(function(){
      let logout_user = get_active_user;
      $.ajax({url:'/settings',type:'POST',data:{'purpose':'logout','user':logout_user}})
    })
  }

  function user_activity() {
    let ct = (new Date().getTime())/1000
    if (ct - user_activity_time > check_activity_sec) {
      console.log("sending user activity")
      user_activity_time = ct
      $.ajax({url:'/activity',type:'POST',data:{'purpose':'activity'}})
    }
  }
    
}); //(document).ready
