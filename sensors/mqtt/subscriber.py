#!/usr/bin/env python3
"""
Subscribes to MQTT topic `iot/team14/sensor`, decodes incoming sensor + audio payloads,
writes a single point per message into InfluxDB measurement `room_sensors_raw`,
and optionally plays the audio locally.
"""

import os
import time
import json
import base64
import logging
import pygame
import paho.mqtt.client as mqtt
from datetime import datetime
from os import getenv
from dotenv import load_dotenv
from influxdb import InfluxDBClient

# === Logging Settings ===
LOGGING = "console"  # or "file"
LOG_FILE = "subscriber.log"

def config_logging():
    if LOGGING == "file":
        logging.basicConfig(
            filename=LOG_FILE,
            filemode='a',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

# === Load environment vars ===
load_dotenv()
TEAM = "team14"
PASSWORD = getenv("MQTT_PASSWORD", "")

# === MQTT ===
TOPIC = f"iot/{TEAM}/sensor"
broker_address = "10.64.44.156"
broker_port = 1883

# === InfluxDB ===
INFLUX_HOST = "34.78.74.123"
INFLUX_PORT = 8086
INFLUX_DB   = f"{TEAM}_db"
INFLUX_USER = TEAM
INFLUX_PASS = PASSWORD
# Initialize client
influx = InfluxDBClient(
    host=INFLUX_HOST,
    port=INFLUX_PORT,
    username=INFLUX_USER,
    password=INFLUX_PASS,
    database=INFLUX_DB
)

# === Local folder for received WAVs ===
RECEIVE_FOLDER = "received"
os.makedirs(RECEIVE_FOLDER, exist_ok=True)

# === MQTT on_message ===
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        timestamp    = payload.get("timestamp")
        temperature  = float(payload.get("temperature", 0.0))
        humidity     = float(payload.get("humidity", 0.0))
        filename     = payload.get("filename")
        audio_b64    = payload.get("audio_base64")

        if not (timestamp and filename and audio_b64):
            print("⚠️ Missing required fields; skipping message.")
            return

        # Decode and save WAV locally
        wav_path = os.path.join(RECEIVE_FOLDER, filename)
        with open(wav_path, 'wb') as f:
            f.write(base64.b64decode(audio_b64))
        print(f"✅ Saved WAV: {wav_path}")

        # Optional playback
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"❌ Playback error: {e}")

        # Prepare InfluxDB point
        point = {
            "measurement": "room_sensors_raw",
            "time": timestamp,
            "fields": {
                "air_temperature": temperature,
                "humidity": humidity,
                "filename": filename,
                "audio_base64": audio_b64
            }
        }
        influx.write_points([point], time_precision='s')
        print(f"Wrote to InfluxDB: {timestamp}")

        # Optional console/file logging
        log_msg = f"{timestamp} | Temp: {temperature}°C | Hum: {humidity}% | File: {filename}"
        if LOGGING == "console":
            print(log_msg)
        else:
            logging.info(log_msg)

        # Clean up
        os.remove(wav_path)

    except Exception as e:
        print(f"❌ Error processing message: {e}")

# === Main ===
def main():
    config_logging()
    client = mqtt.Client(client_id=f"subscriber_{int(time.time())}")
    client.username_pw_set(TEAM, PASSWORD)
    client.on_message = on_message

    client.connect(broker_address, broker_port)
    client.subscribe(TOPIC, qos=1)
    client.loop_start()

    print(f"Subscribed to {TOPIC}; waiting for messages…")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()
