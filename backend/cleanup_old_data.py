"""
Cleanup old raw data (keep only last 24 hours)
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.crud import cleanup_old_data
from sqlalchemy import select, func, delete
from app.models import SensorReading


async def manual_cleanup():
    """Manually cleanup old data"""
    print("🗑️  Data Cleanup Utility")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Count total records
        total_result = await db.execute(select(func.count(SensorReading.id)))
        total_before = total_result.scalar()
        
        # Get oldest and newest
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
        
        print(f"\n📊 Current Status:")
        print(f"   Total raw readings: {total_before:,}")
        print(f"   Oldest: {oldest_time}")
        print(f"   Newest: {newest_time}")
        
        if oldest_time and newest_time:
            age_hours = (newest_time - oldest_time).total_seconds() / 3600
            print(f"   Data span: {age_hours:.1f} hours ({age_hours/24:.1f} days)")
        
        # Calculate cutoff (24 hours ago)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        # Count records to delete
        count_result = await db.execute(
            select(func.count(SensorReading.id))
            .where(SensorReading.timestamp < cutoff)
        )
        to_delete = count_result.scalar()
        
        print(f"\n🗑️  Cleanup Plan:")
        print(f"   Cutoff time: {cutoff}")
        print(f"   Records to delete: {to_delete:,}")
        print(f"   Records to keep: {total_before - to_delete:,}")
        
        if to_delete == 0:
            print("\n✅ No cleanup needed - all data is within 24 hours")
            return
        
        # Confirm deletion
        print(f"\n⚠️  This will delete {to_delete:,} records")
        confirm = input("Continue? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        print("\n🔄 Deleting old records...")
        
        # Delete old records
        result = await db.execute(
            delete(SensorReading)
            .where(SensorReading.timestamp < cutoff)
        )
        await db.commit()
        
        deleted_count = result.rowcount
        
        # Count remaining
        total_result = await db.execute(select(func.count(SensorReading.id)))
        total_after = total_result.scalar()
        
        print(f"\n✅ Cleanup Complete!")
        print(f"   Deleted: {deleted_count:,} records")
        print(f"   Remaining: {total_after:,} records")
        print(f"   Freed: ~{(deleted_count * 200 / 1024 / 1024):.2f} MB")
        
        print("\n💡 Tip: Run VACUUM to reclaim disk space:")
        print("   sqlite3 vayu_data.db 'VACUUM;'")


if __name__ == "__main__":
    asyncio.run(manual_cleanup())