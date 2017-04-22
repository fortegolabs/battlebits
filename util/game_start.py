import paho.mqtt.publish as publish
publish.single('battlebits/game/state', 'start', hostname="test.mosquitto.org")
