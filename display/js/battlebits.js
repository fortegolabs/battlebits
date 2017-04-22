/* simple angular js script for managing the game board */

var bbApp = angular.module('bbApp', ['ngResource', 'ngAudio']);

bbApp.controller('gameController', function($scope, ngAudio) {
    
    /* Network Com,=ms Setup */
    //Internet Test Server
    //$scope.mqttServer = "test.mosquitto.org";
    //$scope.mqttPort = Number(8080);
    
    //Rileys Test Server
    //$scope.mqttServer = "192.168.4.10";
    $scope.mqttServer = "bbcontroller.bb.lan";
    $scope.mqttPort = Number(9001);
    
    
    /* GAME SETUP */
    $scope.gameState = "";
    $scope.gameBytes = [];
    $scope.gameDuration = "";
    $scope.gameNumber = -1;
    $scope.playerOne = -1;
    $scope.guessOne = -1;
    $scope.playerTwo = -1;
    $scope.guessTwo = -1;
    
    /*previous game stats*/
    $scope.lastPlayerOne = -1;
    $scope.lastPlayerOneTime = -1;
    $scope.lastPlayerTwo = -1;
    $scope.lastPlayerTwoTime = -1;
    $scope.lastGameBytesLength = -1;
    
    /* timers */
    $scope.gameCountDown = 0;
    $scope.playerCountDown = 10;
    
    /* Sound */
    $scope.sound = ngAudio.load("sounds/button-2.mp3");
    $scope.titleMusic = ngAudio.load("sounds/11-final-showdown.mp3")
    //$scope.gameMusic = ngAudio.load("sounds/02-operation-overlord.mp3")
    $scope.gameMusic = ngAudio.load("sounds/01-super-mario-bros.mp3")
    // 10-king-koopa-s-castle.mp3
    // 08-water-world.mp3
    // 06-underground.mp3
    // 01-super-mario-bros.mp3
    // 03-hurry-super-mario-bros.mp3
    $scope.p1JoinGameEffect = ngAudio.load("sounds/smb-powerup.mp3");
    $scope.p2JoinGameEffect = ngAudio.load("sounds/smb-1up.mp3");
    $scope.p1Right = ngAudio.load("sounds/smb-coin-short.mp3");
    $scope.p2Right = ngAudio.load("sounds/smb-fireball-short.mp3");  
    
    $scope.p1JoinGameEffect.volume = .4;
    $scope.p2JoinGameEffect.volume = .4;
    $scope.p1Right.volume = .3;
    $scope.gameMusic.volume = .5;
    $scope.titleMusic.volume = .3;
    $scope.titleMusic.loop = true;
    
    //Game Screen Music
    $scope.startTitleMusic = function(){
        
        $scope.gameMusic.pause();
        //$scope.titleMusic.loop = true;
        $scope.titleMusic.play();
        
    }
    
    //Title Game Music
    $scope.startGameMusic = function(){
        $scope.titleMusic.pause();
        $scope.gameMusic.play();
            
    }
    
    $scope.clientId = Math.floor((Math.random() * 10000) + 1).toString();
    
    $scope.scoreboard = [];
    $scope.fortegoScoreboard = [];
    
    var playerTimer;
    var gameTimer;
    
    $scope.formatHex = function(num){
        return (Number(num).toString(16)).toUpperCase();
    }
    
    $scope.getClass = function(score){
        if(Number(score.game_num) == Number($scope.gameNumber))
            return "success";
        else
            return "";
    }
    
    $scope.resetGame = function(){
        // called on error, on game reset, or on game finished
        $scope.gameState = "";
        $scope.gameBytes = [];
        $scope.gameDuration = "";
        $scope.lastGameDuration = "";
        $scope.playerOne = -1;
        $scope.guessOne = -1;
        $scope.playerTwo = -1;
        $scope.guessTwo = -1;
        
        $scope.stopPlayerTimer();
        $scope.stopGameTimer();
        
        $scope.gameCountDown = 0;
        $scope.playerCountDown = 10;
        
        $scope.$apply();
    }
    
    $scope.playerCountdown = function(){
        // called when one player is ready ... we wait 5 seconds   
        playerTimer = setInterval(function(){
            $scope.playerCountDown--;
            //console.log($scope.playerCountDown);
            $scope.$apply();
        }, 1000);
    }
    
    $scope.gameCountdown = function(){
        // called when we are playing the game ... how much time is left in the game  
        gameTimer = setInterval(function(){
            $scope.gameCountDown--;
            //console.log($scope.gameCountDown)
            $scope.$apply();
        }, 1000);
    }
    
    $scope.stopPlayerTimer = function(){
        clearInterval(playerTimer);
    }
    
    $scope.stopGameTimer = function(){
        clearInterval(gameTimer);
    }
    
    $scope.$watch( 'gameState',
        function(newValue, oldValue){
            //console.log('gameState Changed '+newValue);
            if(newValue=='started'){
                if($scope.gameBytes.length<1){
                    console.log("NO BYTES or GAME IN PROGRESS");                    
                }else{
                    // valid change to started state
                    $scope.stopPlayerTimer();
                    $scope.gameCountdown();
                    $scope.startGameMusic();
                    // console.log("Starting game music");
                }
            }else if(newValue=='offline' && oldValue=='started'){
                // this happens in a crash
                //$scope.resetGame();
                //Top the music if we crash
                $scope.titleMusic.stop();
                $scope.gameMusic.stop();
            }else{
                $scope.startTitleMusic();
                //console.log("Staring title music / Stopping Game Music");
            }
        }
    );
    
    $scope.$watch( 'playerOne',
        function(newValue, oldValue){
            //console.log('playerOne Changed to '+newValue);
            if($scope.playerTwo==-1 && $scope.playerOne==0){
                // player one joined first!
                $scope.playerCountdown();
            }
        }
    );
    
    $scope.$watch( 'playerTwo',
        function(newValue, oldValue){
            //console.log('playerTwo Changed to '+newValue);
            if($scope.playerOne==-1 && $scope.playerTwo==0){
                // player two joined first!
                $scope.playerCountdown();
            }
        }
    );
    
    $scope.mqttClient = new Paho.MQTT.Client($scope.mqttServer, $scope.mqttPort,$scope.clientId)
    //$scope.mqttClient = new Paho.MQTT.Client("108.45.141.42",Number(1883),"clientId")
    
    // set callback handlers
    // NOTE: we have to define these two functions
    $scope.mqttClient.onConnectionLost = function(response){
        console.log("Connection Lost");
        console.log(response);
        // connect the client
        $scope.mqttClient.connect({onSuccess:onSuccess,onFailure:onFailure});
    };
    
    $scope.mqttClient.onMessageArrived = function(message){
        //console.log("Message Recevied");
        // message is a js object and it should have a destination name
        console.log(message.destinationName+" = "+message.payloadString);
        
        // what are we going to do?
        var dName = message.destinationName;
        var data = message.payloadString;
        var n = dName.indexOf('/');
        var topic = dName.substring(n + 1);
        switch(topic){
            case "game/state":{
                $scope.gameState = data;
                $scope.$apply();
            }
            break;
            case "game/bytes":{
                // remove the leadaing '[' and the trailing ']'
                var d = data.substring(1, data.length-1);
                var bytes = d.split(',');
                $scope.gameBytes = bytes;
                $scope.lastGameBytesLength = $scope.gameBytes.length;
                $scope.$apply();
            }
            break;
            case "game/duration":{
                $scope.gameDuration = Number(data);
                $scope.gameCountDown = $scope.gameDuration;
                $scope.$apply();
            }
            break;
            case "game/number":{
                $scope.gameNumber = Number(data);
                $scope.$apply();
            }
            break;
            case "game/reset":{
                $scope.resetGame();
            }
            break;
            case "game/join/1":{
                // disallow joining if the game has already started
                if($scope.gameState != 'started')
                    $scope.playerOne = 0;
                    $scope.p1JoinGameEffect.play();
            }
            break;
            case "game/join/2":{
                // disallow joining if the game has already started
                if($scope.gameState != 'started')
                    $scope.playerTwo = 0;
                    $scope.p2JoinGameEffect.play();
            }
            break;
            case "game/join/Player1":{
                // disallow joining if the game has already started
                if($scope.gameState != 'started')
                    $scope.playerOne = 0;
            }
            break;
            case "game/join/Player2":{
                // disallow joining if the game has already started
                if($scope.gameState != 'started')
                    $scope.playerTwo = 0;
            }
            break;
            case "guess/Player1":{
                // check if the guess was right
                $scope.guessOne = data;
                if($scope.gameBytes[$scope.playerOne]==data){
                    $scope.p1Right.play();
                    $scope.playerOne++;
                }
                $scope.$apply();
            }
            break;
            case "guess/Player2":{
                $scope.guessTwo = data;
                // check if the guess was right
                if($scope.gameBytes[$scope.playerTwo]==data){
                    $scope.p2Right.play();
                    $scope.playerTwo++;
                }
                $scope.$apply();
            }
            break;
            case "guess/1":{
                $scope.guessOne = data;
                // check if the guess was right
                if($scope.gameBytes[$scope.playerOne]==data){
                    $scope.p1Right.play();
                    $scope.playerOne++;
                }
                $scope.$apply();
            }
            break;
            case "guess/2":{
                $scope.guessTwo = data;
                // check if the guess was right
                if($scope.gameBytes[$scope.playerTwo]==data){
                    $scope.p2Right.play();
                    $scope.playerTwo++;
                }
                $scope.$apply();
            }
            break;
            case "join":{
                // disallow joining if the game has already started
                if((data=="Player1" || data=="1") && ($scope.gameState != 'started'))
                    $scope.playerOne = 0;
                else if((data=="Player2" || data=="2")&& ($scope.gameState != 'started'))
                    $scope.playerTwo = 0;
                else
                    console.log("JOIN TOPIC submitted unknown data: "+data);
                
                $scope.$apply();
            }
            break;
            case "scoreboard":{
                // an array of objects {seconds,player_name,num_bytes,game_num}
                $scope.scoreboard = JSON.parse(data);
                /*for(i in $scope.scoreboard){
                    var score = $scope.scoreboard[i];
                    if(Number(score.game_num) == Number($scope.gameNumber)){
                        // previous game score
                        if(score.deck=="1"){
                            $scope.lastPlayerOne = score.num_bytes;
                            $scope.lastPlayerOneTime = score.seconds;
                        }else if(score.deck=="2"){
                            $scope.lastPlayerTwo = score.num_bytes;
                            $scope.lastPlayerTwoTime = score.seconds;
                        }
                    }
                }*/
                $scope.$apply();
            }
            break;
            case "fortegoscoreboard":{
                $scope.fortegoScoreboard = JSON.parse(data);
                
                $scope.$apply();
            }
            break;
            case "lastgame":{
                /*[{"seconds": 6.667975, "deck": "1", "player_name": "Eric", "num_bytes": 4, "game_num": 5}]*/
                jsonData = JSON.parse(data);
                //console.log(jsonData);
                for(i in jsonData){
                    var score = jsonData[i];
                    //console.log(score);
                    // previous game score
                    if(score.deck=="1"){
                        $scope.lastPlayerOne = score.num_bytes;
                        $scope.lastPlayerOneTime = score.seconds;
                    }else if(score.deck=="2"){
                        $scope.lastPlayerTwo = score.num_bytes;
                        $scope.lastPlayerTwoTime = score.seconds;
                    }
                }
                $scope.$apply();
            }
            break;
            default:{
                console.log("UNKNOWN TOPIC :: "+topic)
            }
        };
    }
    
    var onSuccess = function(response){
        console.log("CONNECTED...Subscribing to battlebits");
        $scope.mqttClient.subscribe("battlebits/#");
    }
    
    var onFailure = function(response){
        console.log("onFailure");
        console.log(response);
    }
    
    // connect the client
    $scope.mqttClient.connect({onSuccess:onSuccess,onFailure:onFailure});
    
});
