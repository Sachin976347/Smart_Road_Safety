import requests
import json
import time
import random
import uuid 
from datetime import datetime

# ======================= CONFIGURATION =======================
API_URL = "http://localhost:5000/api/iot/data" 
DEVICE_ID = str(uuid.uuid4()) # Unique ID for this simulation client
LOCATION_CENTER = (18.5204, 73.8567) # Pune, India (for realistic coordinates)
INTERVAL_SECONDS = 3 # Send data every 3 seconds for better real-time feel

# Simulated traffic states (Value: 3+ alerts Flask backend)
TRAFFIC_STATES = {
    'none': 0, 'light': 1, 'medium': 2, 'heavy': 3, 'gridlock': 4
}
# Simulated weather conditions (Value: 3+ alerts Flask backend)
WEATHER_CONDITIONS = {
    'clear': 0, 'rainy': 1, 'foggy': 2, 'hazardous_storm': 3
}

# ======================= SIMULATION LOGIC =======================

def generate_sensor_data(lat, lon):
    """Generates simulated data for speed, vibration, traffic, and weather."""
    
    # 1. Speed/Speedometer Data (0-80 normal, 100-120 alert)
    speed = random.choice([
        random.uniform(60.0, 80.0),  
        random.uniform(40.0, 70.0),
        random.uniform(105.0, 115.0) # Alert Trigger (>100)
    ])
    
    # 2. Vibration/Impact Data (4.0-7.0 normal, 8.5-12.0 impact)
    vibration = random.choice([
        random.uniform(4.0, 7.0),
        random.uniform(8.5, 12.0)   # Alert Trigger (>8.0)
    ])
    
    # 3. Traffic Detection
    traffic = random.choice(list(TRAFFIC_STATES.keys()))
    
    # 4. Weather Detection
    weather = random.choice(list(WEATHER_CONDITIONS.keys()))

    # Select one key metric (speed, vibration, traffic, weather) to send as primary payload
    primary_metric = random.choice(['speed', 'vibration', 'traffic', 'weather'])
    
    if primary_metric == 'speed':
        value = speed
    elif primary_metric == 'vibration':
        value = vibration
    elif primary_metric == 'traffic':
        value = TRAFFIC_STATES[traffic]
    else: # weather
        value = WEATHER_CONDITIONS[weather]
        
    sensor_type = primary_metric

    # Simulate slight movement
    lat_offset = random.uniform(-0.01, 0.01)
    lon_offset = random.uniform(-0.01, 0.01)
    
    payload = {
        "device_id": DEVICE_ID,
        "latitude": lat + lat_offset,
        "longitude": lon + lon_offset,
        "sensor_type": sensor_type,
        "value": value,
        # Attach auxiliary data (crucial for accurate speed display on dashboard)
        "auxiliary_data": {
            "speed": speed, 
            "traffic_level": traffic,
            "weather_condition": weather
        }
    }
    return payload

def send_data(data):
    """Sends the data payload to the Flask API."""
    try:
        response = requests.post(
            API_URL, 
            json=data, 
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result = response.json()
            status_msg = "🚨 ALERT" if result.get('alert') else "✅ Normal"
            
            # Display detailed message including auxiliary info
            aux = data.get('auxiliary_data', {})
            detail_msg = f"Type: {data['sensor_type'].capitalize()} | Val: {data['value']:.1f}"
            
            # Conditionally add auxiliary data to console log
            if aux:
                detail_msg += f" | Current Speed: {aux['speed']:.0f} | Traffic: {aux['traffic_level'].capitalize()}"

            print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_msg} - Device {data['device_id'][:8]} | {detail_msg}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ API Error: {response.status_code}, {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Connection Refused. Is 'app.py' running on port 5000?")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ General Error: {e}")


def run_client():
    """Main loop for the IoT client simulation."""
    print("=====================================================")
    print(f"       🚀 Starting IoT Client Simulation 🚀")
    print(f"       Device ID: {DEVICE_ID[:12]}...")
    print(f"       Sending data every {INTERVAL_SECONDS} seconds to {API_URL}")
    print("=====================================================")
    
    while True:
        try:
            data = generate_sensor_data(LOCATION_CENTER[0], LOCATION_CENTER[1])
            send_data(data)
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nShutting down IoT Client.")
            break

if __name__ == "__main__":
    import uuid
    run_client()