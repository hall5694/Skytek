$(document).ready(function(){

  window.user_activity_time = (new Date().getTime())/1000
  window.check_activity_sec = 5
  window.addEventListener("mousemove",user_activity);  
  kpv_wmod=[]
  kpv_val = []
  init = 0
  window.srvr_ip = '192.168.42.1';
  window.srvr_port = '10120'
  window.base_addr = 'http://' + srvr_ip + ':' + srvr_port;
  var socket = new WebSocket("ws://" + srvr_ip + ":" + srvr_port + "/ws/graphs");  

  socket.onopen = function(){
    console.log("connected");
    dir = 0;
    p_dir = 0;
    vr = draw_axis();
    x = 0;
    y = 0;
    p_x = 0;
    p_y = 0;
    x_avg_up = 0;
    y_avg_up = 0;
    p_x_avg_up = 0;
    p_y_avg_up = 0;    
    x_avg_down = 0;
    y_avg_down = 0;    
    p_x_avg_down = 0;
    p_y_avg_down = 0;        
    min_ma_record = 5;
    setTimeout(function(){user_activity()},5000)
  };

  // message received from the socket
  socket.onmessage = function (message) {
    //console.log("receiving: " + message.data);    
    if (JSON.parse(message.data).dest == 'web_graph_adj_ma'){
      p_dir = dir
      dir = JSON.parse(message.data).dir;      
      dt = JSON.parse(message.data).dt;
      adj_ma = JSON.parse(message.data).adj_ma;
      adj_ST_up_avg = JSON.parse(message.data).adj_ST_up_avg;
      adj_ST_down_avg = JSON.parse(message.data).adj_ST_down_avg;
      adj_LT_up_avg = JSON.parse(message.data).adj_LT_up_avg;
      adj_LT_down_avg = JSON.parse(message.data).adj_LT_down_avg;      
      adj_up_inst_max = JSON.parse(message.data).adj_up_inst_max;      
      adj_down_inst_max = JSON.parse(message.data).adj_down_inst_max;   
      adj_up_avg_max = JSON.parse(message.data).adj_up_avg_max;
      adj_down_avg_max = JSON.parse(message.data).adj_down_avg_max;
   
      adj_data(dir, dt, adj_ma, adj_ST_up_avg, adj_ST_down_avg, adj_up_inst_max, adj_down_inst_max, 
               adj_up_avg_max, adj_down_avg_max)   
    }; // socket.onmessage

    if (JSON.parse(message.data).dest == 'inactivity_logout'){
      let logout_user = get_active_user;
      console.log("logging out user(" + logout_user + " due to inactivity")
      mod_msg_box("logging out user(" + logout_user + " due to inactivity")
      $.ajax({url:'/logout',type:'GET',data:{'purpose':'logout','user':logout_user}})
      setTimeout(function(){window.open(base_addr + '/login','_self')},5000)
    }
    
  socket.onclose = function(){
    console.log("disconnected");
  };

  var get_active_user = function() {
   page_user = document.cookie.split('; ').find(row => row.startsWith('skytek_active_user')).split('=')[1];
   return page_user;
  }
  
  var draw_axis = function(){
    vr = [];
    w = 600; // canvas width
    h = 300; // canvas height
    aw = 30; // axis width
    xo = aw; // origin x coordinate
    yo = h - aw; // origin y coordinate
    ys = 3000; // y scale
    xs = 4; // x scale
    dedm = 0; // deduct count up seconds to redraw graph
    ded = xs;
    cded = ded * dedm;
    xti = 50; // number of tick marks on x axis
    xid = xs / xti; // x index divisions
    xtid = (w - aw) / xti; // distance between tick marks on x axis
    yti = 25; // number of tick marks on y axis
    yid = ys / yti; // y index divisions
    ytid = (h - aw) / yti; // distance between tick marks on y axis
    td = 0.1 * aw; // tick mark length
    vr = [w,h,aw,xo,yo, xs, ys];
    
    let canvas = document.querySelector("canvas");
    let cx = canvas.getContext("2d");
    cx.fillStyle = "white";
    cx.fillRect(0, 0, w, h);
    cx.beginPath();
    // axis
    cx.moveTo(aw, 0);
    cx.lineTo(aw, w);
    cx.moveTo(0, h-aw);
    cx.lineTo(w, h-aw);
    
    
    // x ticks - left to right
    xi = xid; // beginning y index marker
    sx = xo + xtid
    sy = yo
    cx.textAlign="center";
    cx.textBaseline="middle";
    for (let i = 0; i<xti; i++){
      ctd = td // current tick length
      if (i % 2 == 0) {
        ctd = td * 1.2
      }
      if (i % 3 == 0) {
        ctd = td * 1.4
      }
      if (i % 4 == 0) {
        ctd = td * 1.8
        cx.strokeText(xi.toFixed(1), sx, sy + aw / 2);        
      }      
      cx.moveTo(sx, sy);  
      cx.lineTo(sx, sy + ctd);
      //cx.fillText(xi, sx, sy + aw / 2);
      xi += xid;
      sx += xtid;
    }
    
    
    // y ticks - bottom to top
    yi = yid; // beginning y index marker
    sx = xo
    sy = yo - ytid
    cx.textAlign="right";
    cx.textBaseline="middle";
    for (let i = 0; i<xti; i++){
      ctd = td // current tick length
      if (i % 2 == 0) {
        ctd = td * 1.2
      }
      if (i % 3 == 0) {
        ctd = td * 1.4
      }
      if (i % 4 == 0) {
        ctd = td * 1.8
        cx.strokeText(Math.floor(yi), aw - 5, sy);        
      }      
      cx.moveTo(sx, sy);  
      cx.lineTo(sx - ctd, sy);
      yi += yid;
      sy -= ytid
    }
        
    cx.stroke();
    cx.strokeStyle="blue";
    cx.closePath();
    return vr
  }
  
  var calc_y = function(yc){
    return((h-aw) - (h-aw) * (yc/ys))
  }
  
  var calc_x = function(xc){
    return((w-aw) * (xc/xs) + aw)
  }  
  
  var adj_data = function(dir, dt, adj_ma, adj_ST_up_avg, adj_ST_down_avg, adj_up_inst_max, adj_down_inst_max, 
                          adj_up_avg_max, adj_down_avg_max){
   //console.log(dt, adj_ma, adj_ST_up_avg, adj_ST_down_avg)
    let canvas = document.querySelector("canvas");
    let cx = canvas.getContext("2d");

    //--------------------------
    // calculate new coordinates
    // x
    num = (dt - dt % xs) / xs;
    cded_prev = cded;
    cded = xs * num;    
    gdt = dt - cded;    
    x = calc_x(gdt);
    x_avg_up = x;
    x_avg_down = x;
    // y
    y = calc_y(adj_ma);
    y_avg_up = calc_y(adj_ST_up_avg);
    y_avg_down = calc_y(adj_ST_down_avg);
    y_alarm_up = calc_y(adj_up_inst_max);
    y_alarm_down = calc_y(adj_down_inst_max);
    y_alarm_avg_up = calc_y(adj_up_avg_max);
    y_alarm_avg_down = calc_y(adj_down_avg_max);
    //--------------------------
    // calculate new coordinates
    
    //--------------------------
    // clear graph if needed
    if (cded != cded_prev){// || (dir != p_dir && dir != 0)) {
      console.log(dir)
      cx.fillStyle = "white";
      cx.fillRect(aw + 1, 0, w, h - aw - 1);
    }
    //--------------------------
    // clear graph if needed
    
    //--------------------------
    // draw data        
    if (dir == 1){
        cx.strokeStyle = "orange"
        cx.beginPath();
       //----------------------
       // avg up
       if (p_x_avg_up > aw){
         cx.moveTo(p_x_avg_up, p_y_avg_up);
       }
       if (p_x_avg_up < x_avg_up && x_avg_up > aw){
         cx.lineTo(x_avg_up, y_avg_up);
       }
       p_x_avg_up = x_avg_up
       p_y_avg_up = y_avg_up
       cx.stroke();
       cx.closePath();
       // avg  up		            
       //----------------------	   
       // alarm avg up
       cx.beginPath();
       cx.moveTo(aw + 1, y_alarm_avg_up);
       cx.lineTo(w, y_alarm_avg_up);
       cx.stroke();
       cx.closePath();
	     // alarm avg up	   
       //----------------------	          
       // alarm up
       cx.strokeStyle = "red"
       cx.beginPath();                
       cx.beginPath();
       cx.moveTo(aw + 1, y_alarm_up);
       cx.lineTo(w, y_alarm_up);
       cx.stroke();
       cx.closePath();
       // alarm up    
       //----------------------     
      }
    else if (dir == -1) {
        cx.strokeStyle = "blue"
        cx.beginPath();
        //----------------------
        // avg down
        if (p_x_avg_down > aw){
          cx.moveTo(p_x_avg_down, p_y_avg_down);
        }
        if (p_x_avg_down < x_avg_down && x_avg_down > aw){
          cx.lineTo(x_avg_down, y_avg_down);
        }
        p_x_avg_down = x_avg_down
        p_y_avg_down = y_avg_down
        cx.stroke();
        cx.closePath();
        // avg  down  		
        //----------------------         
        // alarm avg down
        cx.beginPath();
        cx.moveTo(aw + 1, y_alarm_avg_down);
        cx.lineTo(w, y_alarm_avg_down);
        cx.stroke();
        cx.closePath();
        // alarm avg down  	
        //---------------------- 
        // alarm down        
        cx.strokeStyle = "green"
        cx.beginPath();
        cx.beginPath();
        cx.moveTo(aw + 1, y_alarm_down);
        cx.lineTo(w, y_alarm_down);
        cx.stroke();
        cx.closePath();
        // alarm down    
        //----------------------                   
 		
      }      
    //----------------------
    // current      
    
    if (dir == 1){    
      cx.strokeStyle = "red"
      cx.beginPath(); 
    }
    if (dir == -1){    
      cx.strokeStyle = "green"
      cx.beginPath();             
    }
    if (p_x > aw){
      cx.beginPath();
      cx.moveTo(p_x, p_y);
    }
    if (adj_ma > min_ma_record){
      if (p_x < x && x > aw){
        cx.lineTo(x, y);
      }
      p_x = x
      p_y = y
      cx.stroke();   
      cx.closePath();  
    }
    //----------------------
    // current  
      
    
    //--------------------------
    // draw data  
      
  }   
   
  // send a message to the server
  var sendMessage = function(message) {
    //console.log("sending:" + message.data);
    socket.send(JSON.stringify(message));
  };

  function user_activity() {
    let ct = (new Date().getTime())/1000
    if (ct - user_activity_time > check_activity_sec) {
      console.log("sending user activity")
      user_activity_time = ct
      $.ajax({url:'/activity',type:'POST',data:{'purpose':'activity'}})
    }
  }
    
});

