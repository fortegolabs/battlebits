var bot = require('bot-io');
var mqtt = require("mqtt");
var max7219 = require("max7219");
var clear = require("cli-clear");
var miff = require("miff");

myIP = require('my-ip');
var cfg = miff.load("/var/lib/cloud9/battlebits/player_decks/ShmooDeckConfig.conf");



//Set this to true to print out a bunch of debugging msgs to the console
DEBUG = false;
// DEBUG = false;


console.log("=====================");
console.log("Shoodeck.js Started!");
console.log("=====================");
console.log("\tTrying to connect to mqtt server...");

//GLOBALS
count = 1;
var SHMOO_DECK_ID = cfg.SHMOO_DECK_ID;

/*======================================================\
||        MAX7219 7 SEGMENT CONTROLLER CODDE        ||   
========================================================*/
// var disp = new max7219("/dev/spidev1.1");  //sets up spi1.1 up

// disp.setDecodeAll();
// disp.setScanLimit(8);
// disp.startup();
// disp.setDigitSymbol(0, "H");
// disp.setDigitSymbol(1, "E");
// disp.setDigitSymbol(2, "L");
// disp.setDigitSymbol(3, "P");



/*====================================================
||                TOPICS and MSGS                    ||   
=====================================================*/
//PUB
var PLAYER_READY = 'battlebits/game_status';
var PLAYER_JOIN = 'battlebits/join'

var BB_ERR = 'battlebits/err';
var BB_MSG = 'battlebits/decks/message'
//sub
var SUB_GAME_STATUS = 'battlebits/status';
var SUB_GAME_STATE = 'battlebits/game/state';
var SUB_PLAYER_ID = 'battlebits/result/'+SHMOO_DECK_ID.toString();
var SUB_GAME_BYTES = 'battlebits/game/bytes';
var SUB_GAME_RESET  = 'battlebits/game/reset';

var disp = new max7219("/dev/spidev1.0");

var GAME_STARTED = false;

//This is the byte the player has loaded in from the buttons
var CURRENT_BYTE = 0x00;
var GAME_IS_ACTIVE = false;

// this is to get a secret Fortego playerid loaded before the game starts
var FORTEGO_REGISTRATION_MODE = false;
var FRM_COUNTER = 0;


//SUB
var SUB_TOPICS = [
  SUB_GAME_STATE,
  SUB_GAME_STATUS,
  SUB_PLAYER_ID,
  SUB_GAME_BYTES,
  SUB_GAME_RESET];




/*====================================================
||                MQTT CODE INIT                    ||   
=====================================================*/
//var client = mqtt.connect('mqtt://192.168.86.123');
//var client  = mqtt.connect('mqtt://test.mosquitto.org');
var client = mqtt.connect('mqtt://bbcontroller.bb.lan');
console.log("\tCONNECTED!");


client.on('connect', function () {
  //Subscribe to all topics
  for(i=0; i<SUB_TOPICS.length; i++){
    console.log("Subscribing to : " + SUB_TOPICS[i]);
    client.subscribe(SUB_TOPICS[i]);
  }
  
  client.publish(BB_MSG, "SHMOODECK: #"+SHMOO_DECK_ID.toString()+ " connected! IP:"+myIP());
  console.dir("My Ip is: " + myIP());// return external IPv4 
  
});


var debugMsg = function(msg){
  if(DEBUG)
    console.log("DEBUG: " + msg);
}


client.on('message', function(topic, msg){
  //Execute callbacks by msg
  switch(topic) {
    case SUB_GAME_RESET:
      debugMsg("Game Reset!"); 
      doMasterReset();
      break;
    case SUB_GAME_BYTES:
      GAME_BYTES = msg;
      break;
      
    case SUB_PLAYER_ID:
      //got a score msg
      if(msg == "1"){
        console.log("CORRECT");
        CURRENT_BYTE = 0x00;
        console.log("BYTE WIPED: 0x00 now!");
        updateDisplay();
        
      }else{
        console.log("NOPE!");
      }
      break;
      
    case 'battlebits/game/state':
      debugMsg(msg);
      if(msg == "started"){
        console.log("[ BATTLEBITS HAS STARTED ] " + msg);
        CURRENT_BYTE = 0;
        updateDisplay();
        GAME_STARTED = true;
        break;
      }else if(msg == "finished"){
        GAME_STARTED = false;
        GAME_IS_ACTIVE = false;
        CURRENT_BYTE = 0x00;
        console.log("[ BATTLEBITS IS OVER! ]");
        disp.setDecodeNone();
        disp.setDigitSegments(0, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(1, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(2, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(3, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(4, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(5, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(6, [1, 0, 0, 0, 0, 0, 0, 0]);
        disp.setDigitSegments(7, [1, 0, 0, 0, 0, 0, 0, 0]);
        
        break;
      }
    default:
      console.log("Invalid Switch" + "MSG: " + msg.toString());
  }
});

/*====================================================
||                INPUT CODE INIT                   ||   
=====================================================*/
// button1 = new bot.Button(bot.pins.p9_11);
// button2 = new bot.Button(bot.pins.p8_08);

button1 = new bot.Button(bot.pins.p9_11);
button2 = new bot.Button(bot.pins.p9_12);
button3 = new bot.Button(bot.pins.p9_13);
button4 = new bot.Button(bot.pins.p9_14);
button5 = new bot.Button(bot.pins.p9_15);
button6 = new bot.Button(bot.pins.p9_16);
button7 = new bot.Button(bot.pins.p9_17);
button8 = new bot.Button(bot.pins.p9_18);
ready_button = new bot.Button(bot.pins.p9_23);


//Create a new parameter on the button object
//to track which button fired in the callback.
button1.number = 1;
button1.mask = 1;

button2.number = 2;
button2.mask = 2;

button3.number = 3;
button3.mask = 4;

button4.number = 4;
button4.mask = 8;

button5.number = 5;
button5.mask = 16;

button6.number = 6;
button6.mask = 32;

button7.number = 7;
button7.mask = 64;

button8.number = 8;
button8.mask = 128;

ready_button.number = 9;


//Put all buttons into an array to register callback functions in 1 loop
var BUTTONS = [
  button1,
  button2,
  button3,
  button4,
  button5,
  button6,
  button7,
  button8,
  ready_button ]
  

var doMasterReset = function(){
  CURRENT_BYTE = 0;
  GAME_IS_ACTIVE = false;
  GAME_STARTED = false;
  client.publish(BB_MSG, "SHMOODECK #"+SHMOO_DECK_ID.toString()+ " has been reset.. Now waiting...");
}
  
// var consoleGameDisplay = function(){
//   clear();
//   console.log("NEXT-BYTE: " + CONTROLLER_NEXT_BYTE);
// }

var writeByteToAllDigits = function(char){
  for(i=0; i<8; i++){
    debugMsg("Writing: to digit #" + i.toString()  + " number " + char.toString());
    disp.setDigitSymbol(i, char.toString(), false);
  }
}

var displayInit = function(){
  disp.setDecodeAll();
  disp.setScanLimit(8);
  disp.setDisplayIntensity(10);
  disp.startup();
  disp.clearDisplay();
  disp.stopDisplayTest();
  // writeByteToAllDigits(0);
  CURRENT_BYTE = SHMOO_DECK_ID;
  updateDisplay();
  
}




var updateDisplay = function(){
  disp.setDecodeAll();
  //This code makes sure we always have 8 bits of data.  
  //vs if you just toggled the first bit it would  be 1 vs 00000001
  CB = ("00000000"+CURRENT_BYTE.toString(2)).slice(-8)
  
  debugMsg("CB IS : " + CB.toString());
  for(i=0; i<8; i++){
    debugMsg("b[i] IS : " + CB[i].toString());
    b = CB[i];
    disp.setDigitSymbol(i, b);
  }
}


displayInit();




count = 0;

//BUTTON CALLBACK
var btnFired = function(btn){
  
  //DEBUG MSGS
  if(DEBUG){
    console.log("\n============================================");
    console.log("DEBUG: BTN#: " + btn.number.toString());
    console.log("DEBUG: CLIENT: " + client.connected.toString());
    console.log("DEBUG: PLAYER_ACTIVE: " + GAME_IS_ACTIVE.toString());
    console.log("GAME_STARTED: "+ GAME_STARTED.toString());
    console.log("============================================");
  }
  
  if(client.connected && GAME_IS_ACTIVE && GAME_STARTED){
    //Check to see if we are active in a game. and if the game is started
    //Here we do the bit manipulations on the current byte
    if(btn.number == 9){ //During a game the start player button acts as a reset
      CURRENT_BYTE = 0x00;
      updateDisplay();
      console.log("!!! BITWIPER called... CURRENT BYTE IS 0x00 now!");
      client.publish('battlebits/guess/'+SHMOO_DECK_ID.toString(), CURRENT_BYTE.toString()   ); //This is just to update the display so that when wipe is called the "last byte" shows 0x00
      client.publish(BB_MSG, "SHMOODECK #>> " + SHMOO_DECK_ID.toString() +  " BITWIPER called... CURRENT BYTE IS 0x00 now!");
    } else {
      // clear();
      if(count == 10){
        count = 0;
      }
      // writeByteToAllDigits(count);
      count = count + 1;
      

      CURRENT_BYTE = CURRENT_BYTE ^ btn.mask; 
      updateDisplay();
      
     
      
      console.log("BYTE VALUE: " + CURRENT_BYTE);
    
      client.publish('battlebits/guess/'+SHMOO_DECK_ID.toString(), CURRENT_BYTE.toString()   );
      // client.publish('battlebits/submit_byte/'+SHMOO_DECK_ID.toString(), CURRENT_BYTE.toString()   );
      
    }
  }else if(!GAME_IS_ACTIVE){
    //We are connected but the game has not started (aka player is not active)
    if( btn.number == 9){
      
      //Button 9 is the join game button.
      GAME_IS_ACTIVE = true;
      
      if (FORTEGO_REGISTRATION_MODE) {
        // we are in FORTEGO REGISTRATION MODE
        // so the CURRENT_BYTE is the fortego playeor_id
        console.log('SHMOODECK: #'+SHMOO_DECK_ID.toString()+' entering FORTEGO MODE with FORTEGO_PLAYER_ID = '+CURRENT_BYTE.toString());  
        // publish a message that tells the controller that we are registering a "fortego" game
        client.publish('battlebits/fortegomode/'+SHMOO_DECK_ID.toString(), CURRENT_BYTE.toString()); //This tells the controller we are joinin in fortego mode
        client.publish(BB_MSG,"exiting FORTEGO MODE");
        FORTEGO_REGISTRATION_MODE = false;
      }

      console.log("SHMOODECK: #"+SHMOO_DECK_ID.toString()+" joining the game.");
      client.publish(PLAYER_JOIN, SHMOO_DECK_ID.toString()); //This tells the controller we are ready to join
      client.publish(BB_MSG,"TRYING TO JOIN NOW");
    }
    // they pushed a number button
    else {
      
      // if we are not in FORTEGO_REGISTRATION_MODE, then watch for 5 128's in a row
      if (!FORTEGO_REGISTRATION_MODE){
        
        if(btn.number == 8) {
          // btn 8 is pushed increment counter
          FRM_COUNTER = FRM_COUNTER + 1;
        }
        else {
          // if another button is pushed, reset counter
          FRM_COUNTER = 0;
        }
        
        if (FRM_COUNTER == 5){
          // we hit button 8 5 times in a row, enter FORTEGO_REGISTRATION_MODE
          client.publish(BB_MSG,"exiting FORTEGO MODE");
          FORTEGO_REGISTRATION_MODE = true;
          FRM_COUNTER = 0;
          // 
          // here is where we would add the FTG letters on the display
          CURRENT_BYTE = 0xf0;
          updateDisplay();
          client.publish(BB_MSG,"SHMOODECK #" + SHMOO_DECK_ID.toString() + " has entered FORTEGO REGISTRATION MODE");
        }
      }
      else {
        // we have switched to registration mode, expecting person to enter playerid
        CURRENT_BYTE = CURRENT_BYTE ^ btn.mask;
        console.log("CURRENT_BYTE for secret player VALUE: " + CURRENT_BYTE);
        updateDisplay();
      }
    }
  }
  
  else if(!GAME_STARTED){
    console.log("Game is not started chill out Shmoodeck #" + SHMOO_DECK_ID.toString());
    client.publish(BB_ERR, "Game is not started chill out Shmoodeck #" + SHMOO_DECK_ID.toString());
  }
  
  else {
    console.log("Client not connected to MQTT server!");
    client.publish(BB_ERR, "SHMOO_DECK #" + SHMOO_DECK_ID + " is not connected to the MQTT server");
  }//else

  
  
  
} //btnFired


BUTTONS.forEach(function (button) {
  button.on('released', function(){
    btnFired(button);
  });
});





