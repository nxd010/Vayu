"""
Test script to verify database setup
"""
import asyncio
from app.database import init_db, AsyncSessionLocal
from app.crud import create_sensor_reading, get_latest_reading, get_total_readings_count
from app.schemas import SensorDataInput
from datetime import datetime


async def test_database():
    print("🧪 Testing database setup...")
    
    # Initialize database
    print("\n1️⃣ Initializing database...")
    await init_db()
    print("✅ Database initialized")
    
    # Test creating a sensor reading
    print("\n2️⃣ Creating test sensor reading...")
    async with AsyncSessionLocal() as db:
        test_data = SensorDataInput(
            temperature=25.5,
            humidity=60.0,
            airQualityVoltage=1.2,
            airQualityLevel="Good"
        )
        
        reading = await create_sensor_reading(db, test_data)
        print(f"✅ Created reading: ID={reading.id}, Temp={reading.temperature}°C")
    
    # Test retrieving latest reading
    print("\n3️⃣ Retrieving latest reading...")
    async with AsyncSessionLocal() as db:
        latest = await get_latest_reading(db)
        if latest:
            print(f"✅ Latest reading: {latest.temperature}°C, {latest.humidity}%, {latest.air_quality_level}")
        else:
            print("❌ No readings found")
    
    # Test getting total count
    print("\n4️⃣ Getting total readings count...")
    async with AsyncSessionLocal() as db:
        count = await get_total_readings_count(db)
        print(f"✅ Total readings in database: {count}")
    
    print("\n🎉 All database tests passed!")
    print(f"📁 Database file created at: backend/vayu_data.db")


if __name__ == "__main__":
    asyncio.run(test_database())