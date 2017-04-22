import paho.mqtt.publish as publish
publish.single('battlebits/game/state', 'end', hostname="test.mosquitto.org")
