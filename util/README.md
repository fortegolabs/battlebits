# util
utilities to help in development of battlebits

## playersimulator.py 
- simulates players playing the game by publishing messages to battlebits topics
- publishes messages to battlebits topics on <host>:<port>
- publishes player guesses (the byte that they are submitting to the game controller)
- loops indefinitely
 - waits for battlebits/game_status = 'ready'
 - randomly picks 1 or 2 players
 - each player waits for battlebits/game_status = 'start'
 - loops until battlebits/game_status = 'end'
  - randomly sleeps between 3-8 seconds between submitting player guesses

## game_ready.py 
- sends a "ready" on battlebits/game_status topic

## game_start.py 
- sends a "start" on battlebits/game_status topic

##game_end.py 
- sends an "end" on battlebits/game_status topic

## print_mqtt_topic.py 
- subscribes to and prints all messages received, for a given topic
```shell
python print_mqtt_topic.py
usage: print_mqtt_topic.py [-h] [-p PORT] hostname topic
```

## generate_random_bytes.py
```shell
python generate_random_bytes.py
usage: generate_random_bytes.py [-h] number
```
