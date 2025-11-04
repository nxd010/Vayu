"""
Test script to populate database with sample data
"""
import requests
import time
import random
from datetime import datetime

API_URL = "http://localhost:8000/api/sensor-data"

def generate_sensor_data():
    """Generate realistic sensor data"""
    base_temp = 25.0
    base_humidity = 60.0
    base_aq = 1.0
    
    return {
        "temperature": round(base_temp + random.uniform(-3, 3), 1),
        "humidity": round(base_humidity + random.uniform(-10, 10), 1),
        "airQualityVoltage": round(base_aq + random.uniform(-0.5, 1.5), 2),
        "airQualityLevel": random.choice(["Good", "Good", "Good", "Moderate", "Poor"])
    }

def test_api():
    print("🧪 Testing API with sample data...")
    print("=" * 60)
    
    # Test 1: Send 20 readings
    print("\n📊 Sending 20 sample readings...")
    for i in range(20):
        data = generate_sensor_data()
        try:
            response = requests.post(API_URL, json=data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Reading {i+1}: Temp={result['temperature']}°C, "
                      f"Humidity={result['humidity']}%, "
                      f"AQ={result['air_quality_level']}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("Make sure the server is running: uvicorn app.main:app --reload")
            return
        
        time.sleep(0.5)  # Small delay between requests
    
    # Test 2: Get latest reading
    print("\n📖 Fetching latest reading...")
    try:
        response = requests.get("http://localhost:8000/api/sensor-data/latest")
        if response.status_code == 200:
            latest = response.json()
            print(f"✅ Latest: {latest['temperature']}°C at {latest['timestamp']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get statistics
    print("\n📈 Fetching statistics (last 1 hour)...")
    try:
        response = requests.get("http://localhost:8000/api/statistics?hours=1")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Total readings: {stats['total_readings']}")
            print(f"   Temperature: {stats['temperature']}")
            print(f"   Humidity: {stats['humidity']}")
            print(f"   Air Quality: {stats['air_quality']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Health check
    print("\n🏥 Health check...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Status: {health['status']}")
            print(f"   Total readings: {health['total_readings']}")
            print(f"   Latest reading: {health['latest_reading_time']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API testing complete!")
    print("\n📚 View full API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    test_api()