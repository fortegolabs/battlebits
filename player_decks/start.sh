#!/bin/bash

#echo "Staring HTTP Display Server"
#http-server /var/lib/cloud9/battlebits/display -p9090 &


echo "Starting Battlebits... Hold on..."
UV_THREADPOOL_SIZE=10 node /var/lib/cloud9/battlebits/player_decks/main.js
