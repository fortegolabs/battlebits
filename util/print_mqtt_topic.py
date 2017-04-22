import sys
import argparse

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc, topic):
    print 'Connected with result code ' + str(rc)
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    print '... subscribing to %s' % args.topic
    client.subscribe(args.topic, 0)

def on_disconnect(client, userdata, rc):
    print '[!] disconnected... attempting reconnect automatically'    

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print msg.topic + ' ' + str(msg.payload)

def main():

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect(args.host, args.port, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='prints any messages published to a topic on test.mosquitto.org:1883')
    parser.add_argument('topic', help='name of topic to monitor')
    parser.add_argument('-H', '--host', action='store', default='test.mosquitto.org', help='hostname of broker to connect to')
    parser.add_argument('-p', '--port', action='store', type=int, default=1883, help='port to connect to')
    args = parser.parse_args()

    sys.exit(main())
