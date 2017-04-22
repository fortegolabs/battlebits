import paho.mqtt.publish as publish
publish.single('battlebits/game/state', 'ready', hostname="test.mosquitto.org")
