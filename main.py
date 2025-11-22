import asyncio
import machine
import network
import time

from keypad.keypad import RGBKeypad
from umqtt.simple import MQTTClient
import config

mqtt_client = None
machine_status = 'starting'
last_ping = time.time()

async def manage_connection():
    global mqtt_client
    global machine_status
    global last_ping
    
    print('Waiting for Wi-Fi connection...')
    await asyncio.sleep(1)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Turn off power-saving mode
    wlan.config(pm = 0xa11140)

    # Connect to the network
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    # Wait for Wi-Fi connection
    while True:
        if wlan.status() >= 3:
            break
        print('Waiting for Wi-Fi connection...')
        await asyncio.sleep(1)

    print('... Wi-Fi connected')
    await asyncio.sleep(1)

    # Wait for MQTT connection
    while True:
        try:
            mqtt_client = MQTTClient(client_id=config.MQTT_CLIENT_ID,
                                server=config.MQTT_SERVER)
            mqtt_client.connect()
            break
        except Exception as e:
            print('Error connecting to MQTT:', e)

    mqtt_client.set_callback(manage_message)
    mqtt_client.subscribe(config.MQTT_TOPIC + '/#')

    print('... MQTT connected')
    machine_status = 'running'

    # Send pings or try to reconnect to keep connection alive
    while True:
        await asyncio.sleep(25)
        if machine_status == 'running':
            try:
                mqtt_client.publish(config.MQTT_TOPIC + '/ping', str(time.time()))
                await asyncio.sleep(5)

                if machine_status == 'running' and last_ping + 90 < time.time():
                    machine_status = 'down'            
                    print('No ping received in the last minute, MQTT down !')
                if machine_status == 'down' and last_ping + 60 > time.time():
                    machine_status = 'running'
                    print('Ping received, MQTT up again !')
                if machine_status == 'down' and last_ping + 300 < time.time():
                    print('No ping received in the last 5 minutes, rebooting !')
                    machine.reset()

            except Exception as e:
                print('Error pinging MQTT:', e)
                machine_status = 'down'            
                print('MQTT down !')

        if machine_status == 'down':
            print('MQTT trying to reconnect ...')
            try:
                mqtt_client.connect()
                mqtt_client.set_callback(manage_message)
                mqtt_client.subscribe(config.MQTT_TOPIC + '/#')
                print('MQTT up again !')
                machine_status = 'running'
            except Exception as e:
                print('Error reconnecting to MQTT:', e)

keypad = RGBKeypad()

async def show_status():
    global machine_status
    previous_status = ''

    brightnesses = [0, 0.2, 0.4, 0.6, 0.8, 1, 0.8, 0.6, 0.4, 0.2] 
    current_brightness = 0

    while True:
        if machine_status != previous_status:
            if machine_status == 'starting':
                keypad.set_color(0, 255, 0)
                keypad.light()
            elif machine_status == 'down':
                keypad.set_color(255, 0, 0)
                keypad.light()
            elif machine_status == 'running':
                keypad.set_brightness(0.5)
                keypad.clear()

            current_brightness = 0
            previous_status = machine_status    
        else:
            if machine_status == 'starting' or machine_status == 'down':
                if current_brightness == len(brightnesses)-1:
                    current_brightness = 0
                else:
                    current_brightness += 1
                keypad.set_brightness(brightnesses[current_brightness])
                keypad.light()

        for key in keypad.get_keys():
            key.update_blink()

        await asyncio.sleep_ms(100)

async def manage_buttons():
    global machine_status
    global mqtt_client

    while True:
        keys = keypad.get_keys_pressed()
        if len(keys) > 0:
            if len(keys) == 2 and ((keys[0].get_index() == 12 and keys[1].get_index() == 15) or (keys[0].get_index() == 15 and keys[1].get_index() == 12)):
                machine.reset()
            key_string = ""
            for key in keys:
                key_string += str(key.get_index()) + ","
            key_string = key_string[:len(key_string)-1]

            if machine_status == 'running':
                try:
                    mqtt_client.publish(config.MQTT_TOPIC + '/keypressed', key_string)
                except Exception as e:
                    print('Error publishing message on MQTT:', e)
                    machine_status = 'down'            
                    print('MQTT down !')
            print('Sent ', key_string, ' on topic ', config.MQTT_TOPIC + '/keypressed')
      
        if machine_status == 'running':
            try:
                mqtt_client.check_msg()
            except Exception as e:
                print('Error checking messages on MQTT:', e)
                machine_status = 'down'            
                print('MQTT down !')
        
        await asyncio.sleep_ms(100)

def manage_message(topic, message):
    global last_ping

    print('Received ', message, ' on topic ', topic)

    if topic.decode('utf-8') == config.MQTT_TOPIC + '/ping':
        return

    if topic.decode('utf-8') == config.MQTT_TOPIC + '/pong':
        last_ping = int(message.decode('utf-8'))
        return

    topics = topic[len(config.MQTT_TOPIC)+1:].decode('utf-8').split('/')
    if topics[0].isdigit() and int(topics[0]) >=0 and int(topics[0]) < 16:
        if topics[1] == "on":
            key = keypad.get_key(int(topics[0]))
            colors = message.decode('utf-8').replace(" ", "").split(',')
            if len(colors) == 3 and colors[0].isdigit() and colors[1].isdigit() and colors[2].isdigit():
                key.set_color(int(colors[0]), int(colors[1]), int(colors[2]))
            key.on()
        elif topics[1] == "blink":
            key = keypad.get_key(int(topics[0]))
            colors = message.decode('utf-8').replace(" ", "").split(',')
            if len(colors) == 3 and colors[0].isdigit() and colors[1].isdigit() and colors[2].isdigit():
                key.set_color(int(colors[0]), int(colors[1]), int(colors[2]))
            key.blink()
        elif topics[1] == "off":
            keypad.get_key(int(topics[0])).off()

loop = asyncio.get_event_loop()  
loop.create_task(show_status())
loop.create_task(manage_connection())
loop.create_task(manage_buttons())
loop.run_forever()