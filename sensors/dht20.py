# === Library imports ===
import time          # For short wait between requests
import smbus2        # For I²C communication (used by DHT20)   
#import psutil
import subprocess

# === Constants ===
DHT20_ADDR = 0x38               # Default I2C address for the DHT20 sensor
i2cbus = smbus2.SMBus(1)        # default use I2C bus
time.sleep(1)                 # Short delay to allow sensor to power up and initialize

# === Sensor reset ===
def reset():
    try:
        i2cbus.write_byte(DHT20_ADDR, 0xBA)
        time.sleep(1)
    except Exception as e:
        print("Reset failed", e)



# === Function that reads sensor data ===
def read_dht20():
    try:

        ## Step 1: Check sensor status register (0x71). DHT20 datasheet
        # Bit[3] = 1 means ready
        status = i2cbus.read_i2c_block_data(DHT20_ADDR, 0x71, 1)

        # Bit 4 = calibrated, Bit 3 = idle → both must be 1. DHT20 datasheet
        if (status[0] & 0x18) != 0x18:
            print("Initialization Error!")
            
            return None, None
        
        ## Step 2: Start a new measurement (send 0xAC 0x33 0x00). DHT20 datasheet
        i2cbus.write_i2c_block_data(DHT20_ADDR, 0xac, [0x33,0x00])
        time.sleep(0.2)             # wait 100ms for data to be ready

        ## Step 3: Read 7 bytes of measurement data. DHT20 datasheet
        data = i2cbus.read_i2c_block_data(DHT20_ADDR, 0x00, 7)
        print("Raw data", data)

        ## Step 4: Convert raw temperature data (20-bit)
        temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        temperature = 200*float(temp_raw)/2**20-50                  #Formula from DHT20 manual

        ## Step 5: Convert raw humidity data (20-bit)
        humid_raw = (data[1] << 12) | (data[2] << 4) | ((data[3] & 0xF0) >> 4)
        humidity = 100*float(humid_raw)/2**20                       #Formula from DHT20 manual
        #humid_raw = ((data[3] & 0xf0) >> 4) + (data[1] << 12) + (data[2] << 4)
        #humidity = 100*float(humid_raw)/2**20
        
        return round(temperature, 2), round(humidity, 2)
    
    except Exception as e:
        print("DHT20 read error:",e)

        return None,None
    

# Optional: test it directly
if __name__ == "__main__":

    max_attempts = 3
    for attempt in range(max_attempts):
        temp, hum = read_dht20()
        if temp is not None and hum != 0.0:
            break
        print(f"⚠️ Attempt {attempt + 1} failed. Retrying...")
        time.sleep(1)
    
    #temp, hum = read_dht20()
    if temp is not None:
        print(f"🌡️ Temperature: {temp} °C, 💧 Humidity: {hum} %")
    else:
        print("⚠️ Failed to read DHT20 sensor.")


    
