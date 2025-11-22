# Project description

This project implements an RGB keypad that connects to an MQTT server to send key events and displays key colors based on the received events.
This project is designed to run on a microcontroller with MicroPython support (tested with Raspberry Pi Pico) with an keypad associated (tested with Pimoroni Pico RGB Keypad).

# Configuration file

The configuration file `config.py` should contain the following settings (you can use `config.py.default` as a template):
- WIFI_SSID: The SSID of your WiFi network
- WIFI_PASSWORD: The password of your WiFi network
- MQTT_SERVER: The IP address or hostname of your MQTT server
- MQTT_CLIENT_ID: A unique client ID for the MQTT connection
- MQTT_TOPIC: The base topic for the keypad events

# MQTT messages

The MQTT messages sent are:
- `$MQTT_TOPIC/keypressed`: Sent when a key is pressed, where the content of the message is a string with the list of numbers (from 0 to 15) of the keys pressed separated by a comma (in case of multiple keys are pressed at the same time).
- `$MQTT_TOPIC/ping`: A ping message to check that the connection is alive. The content of the message is the current time.

The MQTT messages received are:
- `$MQTT_TOPIC/<key_number>/on`: Turn on the key with the given number. The content of the message should contains the color to display, in hexadecimal format (e.g., `FF0000` for red).
- `$MQTT_TOPIC/<key_number>/blink`: Make the key with the given number blink. The content of the message should contains the color to display, in hexadecimal format (e.g., `FF0000` for red).
- `$MQTT_TOPIC/<key_number>/off`: Turn off the key with the given number.
- `$MQTT_TOPIC/pong`: The answer to the ping message to indicate that the connection is alive. The content of the message shoule be the one received in the ping message.

# Versions

22/11/2025 
This commit adds the initial project files for the Keypad project and implements the RGBKeypad functionality with MQTT support. The main changes include importing the MQTTClient from the umqtt.simple module, setting up MQTT connectivity, and handling MQTT messages to monitor the machine status. The code now pings the MQTT server periodically and checks for incoming messages to ensure the system remains responsive. If no ping is received within a specified timeframe, the machine will reboot to recover from potential connectivity issues.

