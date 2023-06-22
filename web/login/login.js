 $(document).ready(function(){
  kpv_wmod=[]
  kpv_val = []
  init = 0
    
  window.srvr_ip = '192.168.42.1';
  window.srvr_port = '10120'
  window.base_addr = 'http://' + srvr_ip + ':' + srvr_port;
  var socket = new WebSocket("ws://" + srvr_ip + ":" + srvr_port + "/ws/login");
  var msg_box = $("#msg_box");
  
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

  window.user_set = 0;  // set to one after initial login and new user credentials set
  window.valid_cred = 0;
  var lock_time_m = 5; // minutes to lock out user on att_left failed login attempts
  window.lock_time_s = lock_time_m * 60;
  
    
  socket.onopen = function(){
    console.log("connected");
    $('#username').prop('value','jason');
    $('#password').prop('value','jason1');        
    sendMessage({ 'dest':'qk1', 'purpose':'request_kpv', 'data' : '1'});
  };

  // message received from the socket
  socket.onmessage = function (message) {
    //console.log("receiving: " + message.data);
    if (JSON.parse(message.data).dest == 'check_user_set'){
      user_set = parseInt(JSON.parse(message.data).data)
      let c_user = JSON.parse(message.data).current_user
      //console.log("user_set : " + user_set)
      if (user_set == 0) {
        $('#username').text('skytek')
        $('#password').text('skytek')
      }
      else if (user_set == 1){
        submit_response(1);
      }      
      else if (user_set == 2){
        mod_msg_box("Unit in use by another user")
      }
    }

    if (JSON.parse(message.data).dest == 'check_cred'){
      valid_cred = parseInt(JSON.parse(message.data).valid_cred)
      att_left = parseInt(JSON.parse(message.data).att_left)
      lockout_time = parseInt(JSON.parse(message.data).lockout_time)
      c_user = String(JSON.parse(message.data).user)
      if (valid_cred == 0) {
         mod_msg_box('invalid username (' + c_user + ')');
         $('#submit_btn').text('Login')
      }
      else{
        $('#submit_btn').text('Login')
      }
      if (valid_cred == 1) {        
        mod_msg_box('incorrect password for user ( ' + c_user + ') ' + att_left + ' login attempts left');
      }
      else if (valid_cred == 2) {
        mod_msg_box('login successful for user ( ' + c_user + ')');
        $.ajax({url:'/login',type:'POST',data:{'purpose':'login','user':c_user}})
        setTimeout(function(){window.open(base_addr + '/settings','_self')},1000);  
      }
      else if (valid_cred == 3) {
        lockout_user(c_user,lockout_time);
      }           
    }
  }    

  socket.onclose = function(){
    //console.log("disconnected from server");
  };

  var check_user_set = function(i = 0){
    if (i == 1) {
      $.ajax({url:'/login',type:'POST',data:{'purpose':'check_user_set'}})
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

  var mod_msg_box = function(msg){
    msg_box.empty();
    msg_box.append(msg);
  };

  var lockout_user = function(user_cl, lockout_time){
    lock_time = Math.floor(lockout_time);
    let c_time = Math.floor((new Date().getTime())/1000);
    let elapsed_s = c_time - lock_time;
    if (Math.abs(elapsed_s) > 301) {
      elapsed_s = 0;
    }
    let lock_cd_s = lock_time_s - elapsed_s;
    let display_m = Math.floor(lock_cd_s / 60);
    if (Math.abs(display_m) > 60) {
      display_m = '5'
    }
    let display_s = Math.floor(lock_cd_s % 60);
    if (Math.abs(display_s) > 60) {
      display_s = 0
    }    
    if (display_s < 10) {
        display_s = "0" + display_s;   
    }
    if (document.getElementById('username').value == user_cl){
        mod_msg_box("User (" + user_cl + ") next login attempt prohibited for " + display_m + ":" + display_s + " minutes. \n");
    }
  };
      
  var append_new_user_section = function(){
    $('#submit_btn').prop('disabled',true);
    $('#username').empty();
    $('#password').empty();
    mod_msg_box("Default login success \n Enter new username and password");

    let r0 = document.createElement('div');
    r0.setAttribute('class','s0sr');
    document.getElementById('create_new_user').appendChild(r0);
      let r0l0 = document.createElement('input');
      r0l0.setAttribute('disabled','true');
      r0l0.setAttribute('type','text');
      r0.appendChild(r0l0);
      r0l0.value = ('New username');      
      let r0i0 = document.createElement('input');
      r0i0.setAttribute('type','username');
      r0i0.setAttribute('id','new_user_input');
      r0i0.setAttribute('maxlength','15');
      r0i0.setAttribute('value','jjjjj')
      r0.appendChild(r0i0);

    let r1 = document.createElement('div');
    r1.setAttribute('class','s0sr');
    document.getElementById('create_new_user').appendChild(r1);
      let r1l0 = document.createElement('input');
      r1l0.setAttribute('disabled','true');
      r1l0.setAttribute('type','text');
      r1.appendChild(r1l0);
      r1l0.value = ('New password');      
      let r1i0 = document.createElement('input');
      r1i0.setAttribute('type','username');
      r1i0.setAttribute('id','new_passw_input');
      r1i0.setAttribute('maxlength','15');
      r1i0.setAttribute('value','kkkkk')
      r1.appendChild(r1i0);

    let r2 = document.createElement('div');
    r2.setAttribute('class','s0sr');
    document.getElementById('create_new_user').appendChild(r2);
      let r2l0 = document.createElement('input');
      r2l0.setAttribute('disabled','true');
      r2l0.setAttribute('type','text');
      r2.appendChild(r2l0);
      r2l0.value  = ('Confirm password');      
      let r2i0 = document.createElement('input');
      r2i0.setAttribute('type','username');
      r2i0.setAttribute('id','new_passw_input_confirm');
      r2i0.setAttribute('maxlength','15');
      r2i0.setAttribute('value','kkkkk')
      r2.appendChild(r2i0);

    let r3 = document.createElement('div');
    r3.setAttribute('class','s0sr');
    document.getElementById('create_new_user').appendChild(r3);
      let r3b0 = document.createElement('button');
      r3b0.setAttribute('id','new_user_submit_btn');
      r3.appendChild(r3b0);
      $('#new_user_submit_btn').text("Save new credentials");
  }

  var new_user_submit_btn_function = function(){
    var nui = "";
    var npi = "";
    $('#new_user_submit_btn').click(function(){
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
        mod_msg_box("User credentials saved. Login with new credentials");
        document.getElementById('s0s0').removeChild(create_new_user);
        // post new credentials to database
        $.ajax({url:'/login',type:'POST',data:{'purpose':'new_user','user':nui,'password':npi}})
        $('#submit_btn').prop('disabled',false);
        $('#login_title').prop('value','Login');
        $('#username').prop('value',nui);
        $('#password').prop('value',npi);        
        user_set = 1;
      }
    })
  }

  $('#submit_btn').click(function(){
    check_user_set(1);
  });

  var submit_response = function(i = 0) {
    if (i == 1){
      let user = document.getElementById('username').value;
      let password = document.getElementById('password').value;
      if (user == "" || user == null){
        mod_msg_box("Enter a username");
      }
      else if (user_set == 0) { // default login not accessed yet     
        if (user == 'skytek') {
          if (password == 'skytek') {
            if (document.getElementById('create_new_user').firstElementChild == null) {
              append_new_user_section();
              new_user_submit_btn_function();
            }
          }
          else {
            mod_msg_box("Incorrect default password ");
          }
        }
        else {
          mod_msg_box("Login with default credentials to change username and password");
        }
      }
     else if (user_set == 1) {
        $.ajax({url:'/login',type:'POST',data:{'purpose':'check_cred','user':user,'password':password}})
      }
    }
  }

}); //(document).ready
