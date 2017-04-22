# Battlebits

Riley's creation for Shmoocon 2015. 

## folder structure
- battlebits - the main game_controller code
- display - code that drives the game display, scoreboard, etc
- player_decks - code that operate the player_decks (buttons)
- util - all sorts of handy utilities to help with development, debugging, etc

See the project wiki for more info
https://git.fortegodev.com/eric/battlebits/wikis/home

To restart:
mosquitto -c /etc/mosquitto/mosquitto.conf

then look in the history for python to start the server for the game controller

## how to startup game

1. plug in linksys e2500 router heroichawk
2. connect laptop to heroichawk
    make sure battlebits project is up-to-date: git pull
    cd ~/dev/battlebits/util
    python print_mqtt_topic.py -H 192.168.4.10 -p 1883 battlebits/#
3. connect and poweron bbcontroller (raspberrypi)
    mqtt server starts automatically on boot
    need to login and start game_controller.py
        ssh pi@bbcontroller
        cd battlebits/battlebits/
        if you want to change the game parameters, you have to edit game_controller.py
        python game_controller.py -H 127.0.0.1 -p 1883 testathome &
4. connect and poweron bb1/bb2
    player_decks start on boot
5. start in browser, ~/dev/battlebits/display/index.html


bbcontroller.bb.lan
192.168.4.10
B8:27:EB:16:AD:95
pi:fortegollc


bb1.bb.lan
192.168.4.21
1C:BA:8C:98:BB:B4
root:fortegollc


bb2.bb.lan
192.168.4.22
7C:66:9D:53:6C:72
root:fortegollc


IDEAS to improve things
- admin interface web page which would allow to start game with configuration settings, like game duration, num bytes (ideas: run webserver on bbcontroller and connect to webpage there? might make it harder to display on TV?)
- make game parameters available on cmdline when starting game_controller.py


