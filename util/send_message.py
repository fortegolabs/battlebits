import argparse
import sys
import paho.mqtt.publish as publish


def main():
    return publish.single(args.topic,
                          payload=args.message,
                          qos=args.qos,
                          retain=args.retain,
                          hostname=args.host,
                          port=args.port)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='prints any messages published to a topic on test.mosquitto.org:1883')
    parser.add_argument('topic', help='name of topic to monitor')
    parser.add_argument('message', help='message to send')
    parser.add_argument('qos', type=int, choices=range(0, 3), default=1, help='qos (0, 1, 2); default: 1')
    parser.add_argument('retain', type=bool, choices=[True, False], default=False, help='retain message (True, False); default:False')
    parser.add_argument('-H', '--host', action='store', default='test.mosquitto.org', help='hostname of broker to connect to')
    parser.add_argument('-p', '--port', action='store', type=int, default=1883, help='port to connect to')
    args = parser.parse_args()
    sys.exit(main())