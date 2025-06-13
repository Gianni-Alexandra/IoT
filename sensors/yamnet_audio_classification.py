## === Import Libraries
import os
import time
import base64
import csv
import numpy as np
import librosa
import tensorflow_hub as hub

from influxdb import InfluxDBClient

## === Configuration
INFLUXDB_HOST = "localhost"
INFLUXDB_PORT = 8086
INFLUXDB_DB = "team14_db"
INFLUXDB_USER = "team14"
INFLUXDB_PASS = "team14$@#$"

AUDIO_DIR = "audio_clips"
os.makedirs(AUDIO_DIR, exist_ok=True)

MODEL_HANDLE = "https://tfhub.dev/google/yamnet/1"

## === The four display names we care about 
TARGET_LABELS = ["cough", "sneeze", "throat clearing", "wheeze"]

## === Load the YAMNet model & class map
print("Loading YAMNet model...")
yamnet = hub.load(MODEL_HANDLE)
print("Model Loaded!")

## === Get path to bundled class map.csv
class_map_path = yamnet.class_map_path().numpy().decode("utf-8")
print(f"Using class map at: {class_map_path}")

## === Parse class map for display names
mids, names = [], []
with open(class_map_path, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader, None)  # skip header
    for row in reader:
        if len(row) < 3:
            continue
        mid = row[1].strip()
        name = row[2].strip().lower()
        if mid.startswith("/m/"):
            mids.append(mid)
            names.append(name)

## === Build index map for our target labels
target_indices = {}
for lbl in TARGET_LABELS:
    if lbl not in names:
        raise RuntimeError(f"Target label '{lbl}' not found in YAMNet class map.")
    target_indices[lbl] = names.index(lbl)
print(f"Target class indices: {target_indices}")

## === InfluxDB client setup
influx = InfluxDBClient(
    host=INFLUXDB_HOST,
    port=INFLUXDB_PORT,
    username=INFLUXDB_USER,
    password=INFLUXDB_PASS,
    database=INFLUXDB_DB
)


### === Functions
"""Fetch points newer than last_ts from InfluxDB"""
def query_new_points(last_ts):
    
    query = (
        "SELECT air_temperature AS temp, humidity, audio_base64, filename "
        f"FROM room_sensors_raw WHERE time > '{last_ts}' ORDER BY time ASC"
    )
    result = influx.query(query)

    return list(result.get_points())

"""Decode base64 WAV and save locally"""
def decode_and_save(b64str, filename):
    data = base64.b64decode(b64str)
    path = os.path.join(AUDIO_DIR, filename)

    with open(path, 'wb') as f:
        f.write(data)
    #print(f"✅ Saved WAV: {path}")

    return path

"""Run YAMNet on WAV and return scores for target labels"""
def classify_clip(wavpath):
    wav,  = librosa.load(wavpath, sr=16000, mono=True)
    scores, , _ = yamnet(wav.astype(np.float32))
    max_scores = np.max(scores.numpy(), axis=0)

    # Extract scores for target labels
    return {lbl: float(max_scores[idx]) for lbl, idx in target_indices.items()}

"""Generate a simple rule-based health recommendation"""
def make_recommendation(label, conf, temp, hum):
    
    if conf < 0.6:
        return "Low confidence—please reposition the microphone."
    
    if label == "cough":
        return "Hot/humid + cough: open window." if (temp > 26 or hum > 70) else "Cough detected—rest & hydrate."
    
    if label == "sneeze":
        return "Dry + sneeze: use humidifier." if hum < 30 else "Sneeze detected—have tissues."
    
    if label == "throat clearing":
        return "Throat clearing—consider gargling."
    
    if label == "wheeze":
        return "Wheezing detected—monitor breathing."
    
    return "No issue detected."


## === Main processing loop
def main():
    last_ts = "1970-01-01T00:00:00Z"
    print("▶ Starting classification loop…")

    while True:
        points = query_new_points(last_ts)

        if not points:
            time.sleep(2)
            continue

        for rec in points:
            ts = rec['time']
            tmp = rec['temp']
            hum = rec['humidity']

            wav_path = decode_and_save(rec['audio_base64'], rec['filename'])
            scores = classify_clip(wav_path)
            label, conf = max(scores.items(), key=lambda x: x[1])
            rec_txt = make_recommendation(label, conf, tmp, hum)

            # Print results
            print(f"[{ts}] Temp={tmp:.1f}°C Hum={hum:.1f}% -> {label.title()} ({conf:.2f}) -> {rec_txt}")

            # Clean up WAV file
            os.remove(wav_path) 

            # Update last timestamp
            last_ts = ts 
        time.sleep(1)

if name == "main":
    main()