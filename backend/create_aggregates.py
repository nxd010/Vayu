"""
Create historical aggregates from existing raw data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.crud import create_hourly_aggregate, create_daily_aggregate
from sqlalchemy import select
from app.models import SensorReading


async def create_all_aggregates():
    """Create all missing aggregates from raw data"""
    print("🔄 Creating Historical Aggregates")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Get oldest and newest readings
        oldest = await db.execute(
            select(SensorReading.timestamp)
            .order_by(SensorReading.timestamp.asc())
            .limit(1)
        )
        newest = await db.execute(
            select(SensorReading.timestamp)
            .order_by(SensorReading.timestamp.desc())
            .limit(1)
        )
        
        oldest_time = oldest.scalar()
        newest_time = newest.scalar()
        
        if not oldest_time or not newest_time:
            print("❌ No raw data found")
            return
        
        print(f"\n📅 Data Range:")
        print(f"   From: {oldest_time}")
        print(f"   To: {newest_time}")
        
        # Create hourly aggregates
        print(f"\n⏱️  Creating Hourly Aggregates...")
        
        # Start from the beginning of the hour
        current_hour = oldest_time.replace(minute=0, second=0, microsecond=0)
        end_hour = newest_time.replace(minute=0, second=0, microsecond=0)
        
        hourly_created = 0
        hourly_skipped = 0
        
        while current_hour <= end_hour:
            result = await create_hourly_aggregate(db, current_hour)
            if result:
                hourly_created += 1
                print(f"   ✅ Created hourly aggregate for {current_hour}")
            else:
                hourly_skipped += 1
                if hourly_skipped == 1:
                    print(f"   ⏭️  Skipping existing aggregates...")
            
            current_hour += timedelta(hours=1)
        
        print(f"\n   Created: {hourly_created} hourly aggregates")
        print(f"   Skipped: {hourly_skipped} (already existed)")
        
        # Create daily aggregates
        print(f"\n📆 Creating Daily Aggregates...")
        
        # Start from the beginning of the day
        current_day = oldest_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = newest_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_created = 0
        daily_skipped = 0
        
        while current_day <= end_day:
            result = await create_daily_aggregate(db, current_day)
            if result:
                daily_created += 1
                print(f"   ✅ Created daily aggregate for {current_day.date()}")
            else:
                daily_skipped += 1
            
            current_day += timedelta(days=1)
        
        print(f"\n   Created: {daily_created} daily aggregates")
        print(f"   Skipped: {daily_skipped} (already existed)")
        
        print("\n" + "=" * 60)
        print("✅ Aggregation Complete!")
        print("=" * 60)
        
        # Show summary
        print("\n📊 Summary:")
        print(f"   Hourly aggregates: {hourly_created}")
        print(f"   Daily aggregates: {daily_created}")
        print(f"   These will make historical queries much faster!")


if __name__ == "__main__":
    asyncio.run(create_all_aggregates())