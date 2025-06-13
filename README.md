# Smart IoT System for Audio-Based Health Monitoring
This project detects **coughing**, **sneezing**, **throat clearing** and **wheeze**  using a **microphone**. In parallel, it monitors **room temperature and humidity**, and suggests simple health-related recommendations based on real-time data.

## Project Objectives
- Classify audio events (cough, sneeze, throat clearing, wheeze)
- Monitor real-time environmental conditions (temperature & humidity)
- Upload all data to the *cloud* for centralized storage and processing
- Run a machine learning model in the cloud to classify audio
- Combine audio & sensor data to provide real-time health suggestions

## Components

### Hardware (Inputs/sensors)
- USB Microphone 
- DHT20 (temperature and humidity)

### Software 
- MQTT: Data transmittion
- Cloud database (Google Cloud services)
- Python: Sensor reading, cloud uploading, model inference
- Tensorflow / Keras: audio classification model 
For audio classification we used the **pretrained YAMNet** model. It is an audio event classifier trained on the *AudioSet* database.

## Project Pipeline

1. **Sensor Acquisition (Raspberry Pi)**  
   - **DHT20** (`dht20.py`): reads temperature & humidity  
   - **Microphone** (`mic_sensor.py` ): records 4 s audio clips at 16 kHz, mono  
   
2. **MQTT Transport (Raspberry Pi)**  
   - **publisher.py** samples sensors & audio, encodes clip as Base64, packs JSON:  
     ```json
     {
       "timestamp": "2025-06-12T15:00:00Z",
       "temperature": 24.8,
       "humidity": 45.2,
       "filename": "clip_2025-06-12T15:00:00.wav",
       "audio_base64": "UklGRlIAAABXQVZFZm10IBAAAAABAAEA..."
     }
     ```  
   - Publishes on topic `iot/team14/sensor`

3. **Time-Series Ingestion (Raspberry Pi → InfluxDB)**  
   - **subscriber.py** (Pi) subscribes to `iot/team14/sensor`, decodes JSON  
   - Writes a single point into measurement `room_sensors_raw` with fields:
     - `air_temperature`  
     - `humidity`  
     - `filename`  
     - `audio_base64`

4. **Cloud Classification (Google Cloud VM)**  
   - **yamnet_audio_classification.py** runs on VM with InfluxDB v1.x installed  
   - Polls `room_sensors_raw` via the Python client every 1–2 s  
   - Decodes Base64 → saves local WAV → loads via `librosa` at 16 kHz, mono  
   - Feeds waveform into **YAMNet** (TF-Hub)  
     - Internally segments into 0.975 s patches  
     - Averages (or takes max) patch scores for your four targets:  
       `cough`, `sneeze`, `throat clearing`, `wheeze`  
   - Applies simple rule-based logic to print real-time recommendations:
     - E.g. “Cough detected—rest & hydrate.” or “Dry + sneeze: use humidifier.”

5. **Result Display & Logging**  
   - Classification script prints each event with:
     ```
     [2025-06-12T15:00:00Z] Temp=24.8°C Hum=45.2% → Cough (0.82) → Cough detected—rest & hydrate.
     ```




