#!/usr/bin/env python
from __future__ import print_function
print = lambda x: sys.stdout.write("%s\n" % x)

import sys
import argparse
import datetime
import threading
import collections
import random
import time
import json
import traceback

import paho.mqtt.client as mqtt

import scoreboard

ALL_BYTES = {0: [17,33,65,129,18,34,66,130,20,36,68,132,24,40,72,136],
             1: [49,81,97,113,145,241,50,82,98,114,146,242,52,84,100,116,148,244,56,88,104,120,152,248],
             2: [19,35,67,131,21,37,69,133,22,38,70,134,23,39,71,135,25,41,73,137,31,47,79,143],
             3: [51,83,99,115,147,243,53,85,101,117,149,245,54,86,102,118,150,246,55,87,103,119,151,247,57,89,105,121,153,249,63,95,111,127,159,255],
             4: [161,177,193,209,225,162,178,194,210,226,164,180,196,212,228,168,184,200,216,232],
             5: [26,42,74,138,27,43,75,139,28,44,76,140,29,45,77,141,30,46,78,142],
             6: [163,179,195,211,227,165,181,197,213,229,166,182,198,214,230,167,183,199,215,231,169,185,201,217,233,175,191,207,223,239],
             7: [58,90,106,122,154,250,59,91,107,123,155,251,60,92,108,124,156,252,61,93,109,125,157,253,62,94,110,126,158,254],
             8: [170,186,202,218,234,171,187,203,219,235,172,188,204,220,236,173,189,205,221,237,174,190,206,222,238]}

def get_random_game_bytes(num):
    result = []
    for i in xrange(0, num):
        result.append(random.choice(ALL_BYTES[i % len(ALL_BYTES)]))
    return result

def get_random_game_bytes_by_difficulty(num, max_difficulty):
    if max_difficulty > max(ALL_BYTES.keys()):
        max_difficulty = max(ALL_BYTES.keys())

    result = []
    for i in xrange(0, num):
        a = {k:v for k,v in ALL_BYTES.iteritems() if k <= max_difficulty}
        result.append(random.choice(a[i % len(a)]))
    return result

def get_printable_bytes(a):
    return str(', '.join(['%02X' % x for x in a]))


def subscribe_multiple_topics(client, list_subscribe_topics):
    # create list of tuples (topic, qos) to pass to subscribe function
    to_subscribe = []
    for item in list_subscribe_topics:
        to_subscribe.append((item.topic, item.qos))
        print('(subscribe_multiple_topics) subscribing to %s qos=%d' % (item.topic, item.qos))
    client.subscribe(to_subscribe)


def on_connect(client, userdata, rc):
    print('(cb on_connect) connected with result code ' + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    # subscribe to all the topics we need
    subscribe_multiple_topics(client, INITIAL_SUBSCRIBE_TOPICS)

    #print('... publish battlebits/controller/status = online')
    #client.publish('battlebits/controller/status', payload='online', qos=2, retain=True)

    print('... publish battlebits/game/state = online')
    client.publish('battlebits/game/state', payload='online', qos=2, retain=True)
    publish_controller_message('battlebits controller online at %s' % str(datetime.datetime.now()))

    # should this be here? or down in the main loop?
    client.publish('battlebits/game/reset', payload='1', qos=2, retain=False)

    # signal that we are connected
    EVENT_CONNECTED.set()


def on_disconnect(client, userdata, rc):
    print('(cb on_disconnect) disconnected gracefully')
    #client.publish('battlebits/controller/status', payload='offline', qos=2, retain=True)
    client.publish('battlebits/game/state', payload='offline', qos=2, retain=True)
    EVENT_CONNECTED.clear()


def on_log(client, obj, level, string):
    print('(cb on_log) %s:%s' % (level, string))


def on_subscribe(mosq, userdata, mid, granted_qos):
    print('(cb on_subscribe) subscribed: mid=%s, qos=%s' % (str(mid), str(granted_qos)))


def on_message(client, userdata, message):
    print('(cb on_message) topic: ' + message.topic + ', message: ' + message.payload)


def on_message_fortegomode(client, userdata, message):
    print('(cb on_message_fortegomode) topic: ' + message.topic + ', message: ' + message.payload)

    global FORTEGO_PLAYER_IDS
    topic_base = 'battlebits/fortegomode/'     # 23 chars
    player_name = message.topic[len(topic_base):]
    fortego_player_id = message.payload

    # only process joins if the game is not active
    if EVENT_GAME_READY.isSet():
        if player_name not in FORTEGO_PLAYER_IDS:
            FORTEGO_PLAYER_IDS[player_name] = fortego_player_id
            publish_debug_message('player_deck %s entered game in fortego mode as %s' % (player_name, FORTEGO_PLAYER_IDS[player_name]))
        else:
            publish_debug_message('player_deck %s already entered fortego mode as %s' % (player_name, FORTEGO_PLAYER_IDS[player_name]))
    else:
        publish_debug_message('player %s can not enter fortegomode: game not in ready state' % player_name)

def on_message_join(client, userdata, message):
    print('(cb on_message_join) topic: ' + message.topic + ', message: ' + message.payload)
    player_name = message.payload

    # only process joins if the game is not active
    if EVENT_GAME_READY.isSet():
        if player_name not in PLAYER_NAMES:
            PLAYER_NAMES.append(player_name)
            EVENT_PLAYER_JOINED.set()
            client.publish('battlebits/game/join/%s' % player_name, payload='1', qos=2)
            publish_controller_message('player %s joined the game' % player_name)
        else:
            publish_debug_message('player %s already joined the game' % player_name)
    else:
        publish_debug_message('player %s can not join: game not in ready state' % player_name)


def on_message_guess(client, userdata, message):
    global PLAYER_COUNT_DONE
    #print('(cb on_message_guess) topic: ' + message.topic + ', message: ' + message.payload)

    topic_base = 'battlebits/guess/'     # 17 chars
    player_name = message.topic[len(topic_base):]
    result_topic = 'battlebits/result/%s' % player_name
    guess = int(message.payload)

    # only process guesses if the game is currently active
    if EVENT_GAME_ACTIVE.isSet():

        # make sure our dicts have the indexes we are using
        if player_name in PLAYERS_CORRECT_IDX and PLAYERS_CORRECT_IDX[player_name] < len(CURRENT_GAME_BYTES):
            if guess == CURRENT_GAME_BYTES[PLAYERS_CORRECT_IDX[player_name]]:
                print('%s guess %02X CORRECT' % (player_name, guess))
                if PLAYERS_CORRECT_IDX[player_name]+1 < len(CURRENT_GAME_BYTES):
                    publish_controller_message('%s guess %02X CORRECT' % (player_name, guess))
                    publish_controller_message('CURRENT_BYTE: %02X' % CURRENT_GAME_BYTES[PLAYERS_CORRECT_IDX[player_name] + 1])
                client.publish(result_topic, payload='1', qos=2)
                PLAYERS_CORRECT_IDX[player_name] += 1
            else:
                #print('%s guess %02X incorrect' % (player_name, guess))
                publish_controller_message('%s guess %02X incorrect' % (player_name, guess))
                publish_controller_message('CURRENT_BYTE: %02X' % CURRENT_GAME_BYTES[PLAYERS_CORRECT_IDX[player_name]])
                client.publish(result_topic, payload='0', qos=2)

            # check to see if player completed all bytes
            if PLAYERS_CORRECT_IDX[player_name] == len(CURRENT_GAME_BYTES):
                PLAYER_END_TIMES[player_name] = datetime.datetime.now()
                PLAYER_COUNT_DONE += 1
                print('player %s COMPLETED!!!!!!!!' % repr(player_name))
                publish_controller_message('%s COMPLETED!!!!!!!!' % player_name)

                # check to see if ALL players are done, set event
                if PLAYER_COUNT_DONE == len(PLAYER_NAMES):
                    EVENT_ALL_PLAYERS_DONE.set()

    else:
        print('... no active game, ignoring byte %02X' % guess)
        publish_controller_message('no active game, ignoring byte %02X' % guess)


# the global mqtt client
MQTT_CLIENT = mqtt.Client(client_id='bbcontroller', clean_session=True)

# global sync events
EVENT_CONNECTED = threading.Event()
EVENT_GAME_ACTIVE = threading.Event()
EVENT_GAME_READY = threading.Event()
EVENT_PLAYER_JOINED = threading.Event()
EVENT_FORTEGO_MODE = threading.Event()

# global topics to subscribe to
SubscribeTopic = collections.namedtuple('SubscribeTopic', ['topic', 'qos', 'callback_func'])
INITIAL_SUBSCRIBE_TOPICS = [SubscribeTopic('battlebits/join', 2, on_message_join),
                            SubscribeTopic('battlebits/fortegomode/#', 2, on_message_fortegomode),
                            SubscribeTopic('battlebits/guess/#', 2, on_message_guess)]

# global configuration items
SECS_WAIT_PLAYERS_JOIN = 10
GAME_DURATION_SECS = 120
NUM_BYTES = 5
MAX_DIFFICULTY = 3       # 0-8 difficulty levels
CURRENT_GAME_NUM = 0

CURRENT_GAME_BYTES = []
PLAYER_NAMES = []
PLAYER_END_TIMES = {}
PLAYERS_CORRECT_IDX = {}
PLAYER_COUNT_DONE = 0
#EVENTS_PLAYERS_WON = {}
EVENT_ALL_PLAYERS_DONE = threading.Event()
FORTEGO_PLAYER_IDS = {}


def publish_controller_message(message):
    MQTT_CLIENT.publish('battlebits/controller/message', str(message), qos=2, retain=False)


def publish_debug_message(message):
    # TODO
    # convert this to logging module
    print('%s' % message)
    MQTT_CLIENT.publish('battlebits/debug/controller', str(message), qos=2, retain=False)


def main():
    global PLAYER_NAMES
    global CURRENT_GAME_BYTES
    global PLAYERS_CORRECT_IDX
    global PLAYER_END_TIMES
    global PLAYER_COUNT_DONE
    global EVENT_GAME_ACTIVE
    global EVENT_GAME_READY
    global CURRENT_GAME_NUM
    global FORTEGO_PLAYER_IDS

    print('... main()')

    mqtt_host = args.host
    mqtt_port = args.port
    db_filepath = 'game_%d_%d_%s' % (NUM_BYTES, GAME_DURATION_SECS, args.database)

    MQTT_CLIENT.on_connect = on_connect
    MQTT_CLIENT.on_disconnect = on_disconnect
    MQTT_CLIENT.on_subscribe = on_subscribe
    MQTT_CLIENT.on_message = on_message
    #MQTT_CLIENT.on_log = on_log

    # set callback handlers for each topic here
    #   can't set these in callback functions
    #   bug that causes deadlock
    #   https://bugs.eclipse.org/bugs/show_bug.cgi?id=459012
    print('... setting callback handlers')
    # set callback handlers for individual topics
    for item in INITIAL_SUBSCRIBE_TOPICS:
        if item.callback_func:
            MQTT_CLIENT.message_callback_add(item.topic, item.callback_func)

    # connect to the mqtt broker
    print('... connecting to %s:%d' % (mqtt_host, mqtt_port))
    MQTT_CLIENT.will_set('battlebits/game/state', payload='offline', qos=2, retain=True)
    MQTT_CLIENT.connect(mqtt_host, mqtt_port)
    MQTT_CLIENT.loop_start()

    # wait until we are connected
    EVENT_CONNECTED.wait()

    print('... watch battlebits/debug/controller for debugging messages')
    publish_debug_message('[+] connected to %s:%d' % (mqtt_host, mqtt_port))

    sb = scoreboard.Scoreboard(db_filepath)
    try:
        rows = sb.get_top_rows(3)
        for row in rows:
            publish_controller_message('SCOREBOARD top 3: game:%s player:%s seconds:%s bytes:%s' % (row[0],
                                                                                                    row[1],
                                                                                                    row[2],
                                                                                                    row[3]))

        rows = sb.get_top_rows(25)
        sb_json = json.dumps([{'game_num': row[0], 'player_name': row[1], 'seconds': row[2], 'num_bytes': row[3]} for row in rows])
        MQTT_CLIENT.publish('battlebits/scoreboard', payload=sb_json, qos=2, retain=False)

        CURRENT_GAME_NUM = sb.get_last_game_num() + 1

    finally:
        sb.close()

    MQTT_CLIENT.publish('battlebits/game/reset', payload='1', qos=2, retain=False)

    #
    # game loop
    #
    while True:

        #
        # wait for players to join
        #

        # tell everyone the game is ready
        MQTT_CLIENT.publish('battlebits/game/state', payload='ready', qos=2, retain=True)
        EVENT_GAME_READY.set()

        # wait for first player
        publish_controller_message('waiting for first player to join')
        EVENT_PLAYER_JOINED.wait()

        # first player joined
        EVENT_PLAYER_JOINED.clear()
        publish_controller_message('first player has joined, waiting %d seconds for more players to join' % SECS_WAIT_PLAYERS_JOIN)

        # wait for others to join
        time.sleep(SECS_WAIT_PLAYERS_JOIN)

        # tell everyone we are no longer accepting players
        EVENT_PLAYER_JOINED.clear()
        EVENT_GAME_READY.clear()

        publish_controller_message('%d players entered for game # %d' % (len(PLAYER_NAMES), CURRENT_GAME_NUM))

        for player_name in PLAYER_NAMES:
            PLAYERS_CORRECT_IDX[player_name] = 0
            PLAYER_END_TIMES[player_name] = 0
            #EVENTS_PLAYERS_WON[player_name] = threading.Event()

        #
        # now that we have players, choose and publish game parameters
        #

        # choose the list of bytes for this game
        publish_controller_message('generating randomized game bytes')
        CURRENT_GAME_BYTES = get_random_game_bytes_by_difficulty(NUM_BYTES, MAX_DIFFICULTY)

        # publish list of bytes
        j = json.dumps(CURRENT_GAME_BYTES, separators=(',', ':'))
        print(j)
        MQTT_CLIENT.publish('battlebits/game/bytes', j, qos=2, retain=False)

        printable_bytes = get_printable_bytes(CURRENT_GAME_BYTES)
        publish_debug_message('set of bytes: %s' % printable_bytes)

        # publish the duration of the game
        MQTT_CLIENT.publish('battlebits/game/duration', str(GAME_DURATION_SECS), qos=2, retain=False)
        MQTT_CLIENT.publish('battlebits/game/number', str(CURRENT_GAME_NUM), qos=2, retain=False)


        #
        # start game
        #

        # publish start time
        # if we need to sync start times, we could send a start time
        # but that would require the clocks on each device to be synchronized
        # for now we will just publish a game start signal
        # since player_decks and display will get signal at about the same delay

        publish_debug_message('... starting game # %d at %s; duration: %d secs; players: %s' % (CURRENT_GAME_NUM,
                                                                                                str(datetime.datetime.now()),
                                                                                                GAME_DURATION_SECS,
                                                                                                ','.join(PLAYER_NAMES)))

        MQTT_CLIENT.publish('battlebits/game/state', payload='started', qos=2, retain=True)

        # publish message starting game at <time>
        publish_controller_message('CURRENT_BYTE: %02X' % CURRENT_GAME_BYTES[0])

        game_start_time = datetime.datetime.now()
        for player_name in PLAYER_NAMES:
            PLAYER_END_TIMES[player_name] = game_start_time

        # wait for all players to be done, or the game duration expires
        EVENT_GAME_ACTIVE.set()
        EVENT_ALL_PLAYERS_DONE.wait(GAME_DURATION_SECS)
        EVENT_GAME_ACTIVE.clear()
        EVENT_ALL_PLAYERS_DONE.clear()

        # game is over
        print('... publishing battlebits/game/state = finished')
        MQTT_CLIENT.publish('battlebits/game/state', payload='finished', qos=2, retain=True)

        game_end_time = datetime.datetime.now()
        game_time_elapsed = game_end_time - game_start_time

        publish_controller_message('finished game at %s' % (str(game_end_time)))
        publish_controller_message('game lasted for %s' % str(game_time_elapsed))

        sb = scoreboard.Scoreboard(db_filepath)
        try:
            for player_name in PLAYER_NAMES:
                num_correct = PLAYERS_CORRECT_IDX[player_name]
                player_game_time = min(game_time_elapsed.total_seconds(), GAME_DURATION_SECS)

                if PLAYER_END_TIMES[player_name] > game_start_time:
                    player_game_time = (PLAYER_END_TIMES[player_name] - game_start_time).total_seconds()

                if num_correct > 0:
                    secs_per_byte = player_game_time / num_correct
                    bytes_per_min = num_correct * (60/player_game_time)
                else:
                    secs_per_byte = 0
                    bytes_per_min = 0

                publish_controller_message('player \'%s\' completed %d bytes in %s seconds, '
                                           '%d secs per byte, '
                                           '%d bytes per minute ' % (player_name, num_correct,
                                                                     player_game_time,
                                                                     secs_per_byte,
                                                                     bytes_per_min))

                print(FORTEGO_PLAYER_IDS)
                #if player_name is in FORTEGO_PLAYER_IDS, it was a fortego player
                if player_name in FORTEGO_PLAYER_IDS and FORTEGO_PLAYER_IDS[player_name]:
                    # insert into fortego DB
                    fortego_player_name = scoreboard.FortegoNamesMap.get(FORTEGO_PLAYER_IDS[player_name], 'guest')
                    # get existing row for player
                    row = sb.get_fortego_row(fortego_player_name)
                    print('fortego_row for player %s' % str(row))
                    if row:
                        if num_correct > row[4] or player_game_time < float(row[3]):
                            publish_debug_message('updating row: game:%d, player:%s, seconds:%s, bytes:%s' % (CURRENT_GAME_NUM, fortego_player_name, player_game_time, num_correct))
                            sb.update_row_fortego(CURRENT_GAME_NUM, player_name, fortego_player_name, player_game_time, num_correct)
                        else:
                            publish_debug_message('not updating because not a high score old:%s/%s; new %s/%s' % (row[4], row[3], num_correct, player_game_time))
                    else:
                        publish_debug_message('inserting row: game:%d, deck:%s, player:%s, seconds:%s, bytes:%s' % (CURRENT_GAME_NUM, player_name, fortego_player_name, player_game_time, num_correct))
                        sb.insert_row_fortego(CURRENT_GAME_NUM, player_name, fortego_player_name, player_game_time, num_correct)
                else:
                    publish_debug_message('inserting row: game:%d, deck:%s, player:%s, seconds:%s, bytes:%s' % (CURRENT_GAME_NUM, player_name, player_name, player_game_time, num_correct))
                    sb.insert_row_anonymous(CURRENT_GAME_NUM, player_name, player_name, player_game_time, num_correct)

            #rows = sb.get_top_rows(3)
            #for row in rows:
            #    publish_controller_message('SCOREBOARD top 3: game:%s player:%s seconds:%s bytes:%s' % (row[0], row[1], row[2], row[3]))
            #    print('SCOREBOARD top 3: game:%s player:%s seconds:%s bytes:%s' % (row[0], row[1], row[2], row[3]))

            rows = sb.get_top_rows(25)
            for a in sb.get_game_rows(CURRENT_GAME_NUM):
                if a not in rows:
                    rows.append(a)
                    print('added')
            print('rows %s' % str(rows))
            sb_json = json.dumps([{'game_num': row[0], 'deck': row[1], 'player_name': row[2], 'seconds': row[3], 'num_bytes': row[4]} for row in rows])
            MQTT_CLIENT.publish('battlebits/scoreboard', payload=sb_json, qos=2, retain=False)

            # send out the battlebits/fortegoscoreboard
            fortego_rows = sb.get_all_rows_fortego()
            print('fortego_rows %s' % str(fortego_rows))
            fortego_json = json.dumps([{'game_num': row[0], 'deck': row[1], 'player_name': row[2], 'seconds': row[3], 'num_bytes': row[4]} for row in fortego_rows])
            MQTT_CLIENT.publish('battlebits/fortegoscoreboard', payload=fortego_json, qos=2, retain=False)

            # get the last game played rows
            last_game = []
            last_game.extend(sb.get_game_rows(CURRENT_GAME_NUM))
            last_game.extend(sb.get_game_rows_fortego(CURRENT_GAME_NUM))
            print('last_game %s' % str(last_game))
            last_game_json = json.dumps([{'game_num': row[0], 'deck': row[1], 'player_name': row[2], 'seconds': row[3], 'num_bytes': row[4]} for row in last_game])
            MQTT_CLIENT.publish('battlebits/lastgame', payload=last_game_json, qos=2, retain=False)

            CURRENT_GAME_NUM = sb.get_last_game_num() + 1

            MQTT_CLIENT.publish('battlebits/game/reset', payload='1', qos=2, retain=False)

        except Exception, e:
            print(traceback.format_exc())
            raise e
        finally:
            sb.close()

        # reset for next game
        PLAYER_NAMES = []
        CURRENT_GAME_BYTES = []
        PLAYERS_CORRECT_IDX.clear()
        PLAYER_END_TIMES = {}
        PLAYER_COUNT_DONE = 0
        EVENT_ALL_PLAYERS_DONE.clear()
        EVENT_PLAYER_JOINED.clear()
        EVENT_FORTEGO_MODE.clear()
        FORTEGO_PLAYER_IDS = {}

    MQTT_CLIENT.loop_stop()
    MQTT_CLIENT.disconnect()

    print('... exiting')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', action='store', default='test.mosquitto.org', help='hostname of broker to connect to')
    parser.add_argument('-p', '--port', action='store', type=int, default=1883, help='port to connect to')
    parser.add_argument('database', action='store', help='filepath of database to store leaderboard')
    #parser.add_argument('-d', '--debug', action='store_true', default=False, help='send debugging messages to battlebits/debug topic')
    args = parser.parse_args()

    print(args)

    sys.exit(main())
