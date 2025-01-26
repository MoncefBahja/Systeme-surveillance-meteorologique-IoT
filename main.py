from machine import Pin
from umqtt.simple import MQTTClient
import ujson
import network
import utime as time
import dht
# Device Setup
DEVICE_ID = "wokwi001"
# WiFi Setup
WIFI_SSID       = "Wokwi-GUEST"
WIFI_PASSWORD   = ""

# MQTT Setup
MQTT_BROKER             = "bbdef1a73ac84dfeb1c3eea17092ce44.s1.eu.hivemq.cloud"
MQTT_CLIENT             = DEVICE_ID
MQTT_TELEMETRY_TOPIC    = 'iot/device/{0}/telemetry'.format(DEVICE_ID)
MQTT_CONTROL_TOPIC      = 'iot/device/{0}/control'.format(DEVICE_ID)

# DHT Sensor Setup
DHT_PIN = Pin(15)

# LED/LAMP Setup
RED_LED     = Pin(12, Pin.OUT)
BLUE_LED    = Pin(13, Pin.OUT)
FLASH_LED   = Pin(2, Pin.OUT)
RED_LED.on()
BLUE_LED.on()

# Methods
def did_recieve_callback(topic, message):
  print('\n\nData Recieved! \ntopic = {0}, message = {1}'.format(topic, message))

  if topic == MQTT_CONTROL_TOPIC.encode(): 
    #Get the command message from json command.
    command_message = ujson.loads(message.decode())["command"]
    if command_message == "lamp/red/on":
      RED_LED.on()
    elif command_message == "lamp/red/off":
      RED_LED.off()
    elif command_message == "lamp/blue/on":
      BLUE_LED.on()
    elif command_message == "lamp/blue/off":
      BLUE_LED.off()
    elif command_message == "lamp/on":
      RED_LED.on()
      BLUE_LED.on()
    elif command_message == "lamp/off":
      RED_LED.off()
      BLUE_LED.off()
    elif command_message == "status":
      global telemetry_data_old
      mqtt_client_publish(MQTT_TELEMETRY_TOPIC, telemetry_data_old)
    else:
      return
    
    send_led_status()

def mqtt_connect():
    print("Connecting to MQTT broker ...", end="")
    mqtt_client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, user="moncef", password="Moncef1999@", ssl=True, ssl_params={'server_hostname':MQTT_BROKER})
    mqtt_client.set_callback(did_recieve_callback)
    mqtt_client.connect()
    print("Connected.")
    mqtt_client.subscribe(MQTT_CONTROL_TOPIC)
    return mqtt_client

def create_control_json_data(command, command_id):
  #import ujson
  data = ujson.dumps({
    "device_id": DEVICE_ID,
    "command_id": command_id,
    "command": command
  })
  return data

def create_json_data(temperature, humidity):
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "temp": temperature,
        "humidity": humidity,
        "type": "sensor"
    })
    return data

def mqtt_client_publish(topic, data):
    print("\nUpdating MQTT Broker...")
    mqtt_client.publish(topic, data)
    print(data)

def send_led_status():
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "red_led": "ON" if RED_LED.value() == 1 else "OFF",
        "blue_led": "ON" if BLUE_LED.value() == 1 else "OFF",
        "type": "lamp"
    })
    mqtt_client_publish(MQTT_TELEMETRY_TOPIC, data)


# Application Logic

# Connect to WiFi
wifi_client = network.WLAN(network.STA_IF)
wifi_client.active(True)
print("Connecting device to WiFi")
wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

# Wait until WiFi is Connected
while not wifi_client.isconnected():
    print("Connecting")
    time.sleep(0.1)
print("WiFi Connected!")
print(wifi_client.ifconfig())

# Connect to MQTT
mqtt_client = mqtt_connect()
# RED_LED.off()
# BLUE_LED.off()
mqtt_client_publish(MQTT_CONTROL_TOPIC, create_control_json_data('lamp/off', 'DEVICE-RESET-00'))
dht_sensor = dht.DHT22(DHT_PIN)
telemetry_data_old = ""

while True:
    mqtt_client.check_msg()
    print(". ", end="")

    FLASH_LED.on()
    try:
      dht_sensor.measure()
    except:
      pass
    
    time.sleep(0.2)
    FLASH_LED.off()

    telemetry_data_new = create_json_data(dht_sensor.temperature(), dht_sensor.humidity())

    if telemetry_data_new != telemetry_data_old:
        mqtt_client_publish(MQTT_TELEMETRY_TOPIC, telemetry_data_new)
        telemetry_data_old = telemetry_data_new

    time.sleep(0.1)






