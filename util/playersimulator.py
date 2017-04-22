from __future__ import print_function
print = lambda x: sys.stdout.write("%s\n" % x)

import sys
import argparse
import random
import time
import threading
import json

import paho.mqtt.client as mqtt

def on_connect(client, userdata, rc):
    print('... connected with result code ' + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    topics = [('battlebits/game/state', 2),
              ('battlebits/game/bytes', 2),
              ('battlebits/result/#', 2)]

    print('... subscribing to %s' % topics)
    client.subscribe(topics)


def on_disconnect(client, userdata, rc):
    print('[!] disconnected, attempting to reconnect automatically')


def on_message_game_state(client, userdata, msg):
    print('... ' + repr(msg.payload))
    # available, busy
    if msg.payload == 'finished':
        EVENT_GAME_FINISHED.set()
        EVENT_GAME_READY.clear()
        EVENT_GAME_STARTED.clear()
    elif msg.payload == 'started':
        EVENT_GAME_STARTED.set()
        EVENT_GAME_READY.clear()
        EVENT_GAME_FINISHED.clear()
    elif msg.payload == 'ready':
        EVENT_GAME_READY.set()
        EVENT_GAME_FINISHED.clear()
        EVENT_GAME_STARTED.clear()
    elif msg.payload == 'online':
        pass
    elif msg.payload == 'offline':
        pass

def on_message_game_bytes(client, userdata, msg):
    global CURRENT_GAME_BYTES
    print('... ' + repr(msg.payload))
    CURRENT_GAME_BYTES = json.loads(msg.payload)
    print('... recvd set of bytes')
    print(CURRENT_GAME_BYTES)


def on_message_result(client, userdata, msg):
    global PLAYERS_CORRECT_IDX
    # battlebits/result/player_name
    player_name = msg.topic[18:]
    if EVENT_GAME_STARTED.isSet():
        if msg.payload == '1':
            if player_name in PLAYERS_CORRECT_IDX:
                PLAYERS_CORRECT_IDX[player_name] += 1


# get a random pause time
def get_random_pause_secs():
    return random.uniform(0, 1.5)


class PlayerThread(threading.Thread):

    def __init__(self, name):
        global PLAYERS_CORRECT_IDX
        threading.Thread.__init__(self)
        self.name = name
        self.topic = 'battlebits/guess/%s' % name
        PLAYERS_CORRECT_IDX[self.name] = 0

    def run(self):
        print('(%s) thread starting ' % self.name)
        self.play_game()
        print('(%s) thread exiting ' % self.name)

    def play_game(self):

        # let game know player is joined and ready
        MQTT_CLIENT.publish('battlebits/join', self.name, 1)

        # now wait for game to start
        print('(%s) waiting for game to start' % self.name)
        publish_simulator_message('(%s) waiting for game to start' % self.name)
        EVENT_GAME_STARTED.wait()

        time_to_wait = 0
        start_time = time.time()

        high = random.choice([2, 3])
        variances = range(0, high)
        random.shuffle(variances)

        # keep guessing until we are told the game is over
        while not EVENT_GAME_FINISHED.wait(0.75):
            elapsed_time = time.time() - start_time
            #print('%s %s %s %s' % (self.name, str(time_to_wait), str(elapsed_time), str(time_to_wait)))

            # make a guess if we have waited random amount of time
            if elapsed_time > time_to_wait:
                if len(variances) < 1:
                    high = random.choice([2, 3])
                    variances = range(0, high)
                    random.shuffle(variances)

                variance = variances.pop()
                #print(CURRENT_GAME_BYTES)
                guess = ((CURRENT_GAME_BYTES[PLAYERS_CORRECT_IDX[self.name]] + variance) & 0xff)

                MQTT_CLIENT.publish(self.topic, guess)
                print ('(%s) %s %02x (%d variance)' % (self.name, self.topic, guess, variance))

                # set a new random time to wait
                time_to_wait = get_random_pause_secs()
                start_time = time.time()

        # remove this player from the number of correct tracker
        del PLAYERS_CORRECT_IDX[self.name]

MQTT_CLIENT = mqtt.Client(client_id='joBBClient', clean_session=True)

EVENT_GAME_FINISHED = threading.Event()
EVENT_GAME_STARTED = threading.Event()
EVENT_GAME_READY = threading.Event()

CURRENT_GAME_BYTES = []
PLAYERS_CORRECT_IDX = {}


def publish_simulator_message(message):
    MQTT_CLIENT.publish('battlebits/simulator/message', message, qos=2, retain=False)


def main():
    print('(main thread) main()')

    mqtt_host = args.host
    mqtt_port = args.port

    print('(main thread) connecting to %s:%d' % (mqtt_host, mqtt_port))
    MQTT_CLIENT.on_connect = on_connect
    MQTT_CLIENT.on_disconnect = on_disconnect
    MQTT_CLIENT.message_callback_add('battlebits/game/state', on_message_game_state)
    MQTT_CLIENT.message_callback_add('battlebits/game/bytes', on_message_game_bytes)
    MQTT_CLIENT.message_callback_add('battlebits/result/#', on_message_result)
    MQTT_CLIENT.connect(mqtt_host, mqtt_port)
    MQTT_CLIENT.loop_start()

    time.sleep(2)

    # loop for as long as we are running this program
    while True:

        # dont enter players into game until game is ready
        print('(main thread) waiting for game to be ready')
        EVENT_GAME_READY.wait()

        print('(main thread) waiting for players to enter game')
        time.sleep(2)

        num_players = random.randrange(1, 2)
        print('(main thread) %d players are going to play' % num_players)
        threads = []

        # create a thread for each player
        for i in xrange(1, num_players+1):
            threads.append(PlayerThread('%d' % i))

        publish_simulator_message('starting player threads')
        # Start new Threads
        for thread in threads:
            thread.start()

        print('(main thread) waiting for player threads to finish')
        # any started threads will run until the event_game_over is signaled
        # we will block here until the threads finish running
        for thread in threads:
            thread.join()

        # secs to wait before joining next game's players
        print('waiting %d mins before joining next players' % args.delay)
        publish_simulator_message('waiting %d mins before joining next players' % args.delay)
        time.sleep(args.delay * 60.0)

    print('(main thread) exiting')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('delay', action='store', type=int, default='5', help='minutes to delay between players joining game')
    parser.add_argument('-H', '--host', action='store', default='test.mosquitto.org', help='hostname of broker to connect to')
    parser.add_argument('-p', '--port', action='store', type=int, default=1883, help='port to connect to')
    #parser.add_argument('-d', '--debug', action='store_true', default=False, help='send debugging messages to battlebits/debug topic')
    args = parser.parse_args()

    sys.exit(main())
