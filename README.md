# IoT
This repository includes my project on the course of "Internet of Things"

# Smart IoT System for Audio-Based Health Monitoring
This project detects **coughing**, **sneezing**, and other sound events using a **microphone**, monitors **room temperature and humidity**, and suggests simple health-related recommendations based on real-time data.

## Project Objectives
- Classify audio events (cough, sneeze, speech, silence)
- Monitor real-time environmental conditions (temperature & humidity)
- Upload all data to the *cloud* for centralized storage and processing
- Run a machine learning model in the cloud to classify audio
- Combine audio & sensor data to provide real-time health suggestions
- Visualize recent data and alerts in a web-based dashboard

### Components

## Hardware (Inputs/sensors)
- Microphone
- DHT20 (temperature and humidity)

## Software 
-MQTT: Data transmittion
-Cloud database
-Python: Sensor reading, cloud uploading, model inference
-Tensorflow / Keras: audio classification model
-Flask: Dashboard Visualization
  



