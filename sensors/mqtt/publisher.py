# 📂 File: mqtt/publisher.py
### === Publisher script
#- Reads temperature and humidity data
#- Records audio
#- Encodes the audio as Base64 string
#- Sends an MQTT payload containing the timestamp, sensor data, and encoded audio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import random
import logging
import base64
import json
from os import getenv
from dotenv import load_dotenv
from datetime import datetime

import paho.mqtt.client as mqtt

# Import from sensors folder
from mic_sensor import get_filename, record_audio
from dht20 import read_dht20, reset as reset_dht

# === Logging Settings & Configuration ===
LOGGING: str = "console"        # Use "console" or "file"
LOG_FILE: str = "stats.log"

def config_logging() -> None:
    if LOGGING == "file":
        logging.basicConfig(
            filename=LOG_FILE,
            filemode='w',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

# === Load environment variables
load_dotenv()

# === User Configuration
TEAM = "team14"
PASSWORD = getenv("MQTT_PASSWORD")
PUBLISH_INTERVAL = 20

# === Broker Configuration
broker_address = "10.64.44.156"
broker_port = 1883
client_id = f"client_{random.randint(0, 1000)}"
TOPIC = f"iot/{TEAM}/sensor"

#TOPIC = f"iot/{TEAM}"
#TOPIC = f"iot/{TEAM}/audio"

# === MQTT Client setup ===
#- Connect to the MQTT broker and start the loop for handling background tasks
def get_mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
    client.username_pw_set(TEAM, PASSWORD)
    client.connect(broker_address, broker_port)
    client.loop_start()

    return client

# === Encode audio to Base64 ===
#- Function to encode audio file as base64 string ==
def encode_audio(filename):
    with open(filename, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded


# === Main Publishing Loop
def main():
    config_logging()
    reset_dht()         #Initialize sensor
    client = get_mqtt_client()

    if LOGGING == "console":
        print("Publishing has started. Press Ctrl+C to stop!")

    try:
        while True:
            # Read temperature and humidity data from sensors/dht20.py
            temp, hum = read_dht20()
            if temp is None or hum is None:
                message = "Sensor read failed. Skipping this cycle."
                print(message) if LOGGING == "console" else logging.warning(message)
                time.sleep(PUBLISH_INTERVAL)
                continue

            # Record audio
            audio_file = get_filename()
            record_audio(audio_file)
            encoded_audio = encode_audio(audio_file)

            # Build payLoad
            # with the [-1] you get the latest
            payload = {
                "timestamp": datetime.now().isoformat(),
                "temperature": temp,
                "humidity": hum,
                "audio_base64": encoded_audio,
                "filename": audio_file.split("/")[-1]
            }

            # Publish Via MQTT
            client.publish(TOPIC, json.dumps(payload), qos=1)

            print("Air_temp", temp)
            message = f"✅ Published data to `{TOPIC}`"
            print(message) if LOGGING == "console" else logging.info(message)

            time.sleep(PUBLISH_INTERVAL)


    except KeyboardInterrupt:
        message = "Publisher stopped by user!"
        print(message) if LOGGING == "console" else logging.warning(message)

    except Exception as e:
        message = f"Enexpected error: {e}"
        print(message) if LOGGING == "console" else logging.warning(message)
    
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()



