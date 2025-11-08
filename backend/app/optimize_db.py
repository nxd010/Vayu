"""
Database Optimization Script
Analyzes and optimizes the Vayu database for better performance
"""
import asyncio
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, engine
from app.models import SensorReading, HourlyAggregate, DailyAggregate
from sqlalchemy import text, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def analyze_database():
    """Analyze current database status"""
    print("📊 Database Analysis")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Count records in each table
        raw_count = await db.execute(select(func.count(SensorReading.id)))
        hourly_count = await db.execute(select(func.count(HourlyAggregate.id)))
        daily_count = await db.execute(select(func.count(DailyAggregate.id)))
        
        raw = raw_count.scalar()
        hourly = hourly_count.scalar()
        daily = daily_count.scalar()
        
        print(f"\n📈 Record Counts:")
        print(f"   Raw readings: {raw:,}")
        print(f"   Hourly aggregates: {hourly:,}")
        print(f"   Daily aggregates: {daily:,}")
        print(f"   Total records: {raw + hourly + daily:,}")
        
        # Calculate data age
        if raw > 0:
            oldest = await db.execute(
                select(SensorReading.timestamp).order_by(SensorReading.timestamp.asc()).limit(1)
            )
            newest = await db.execute(
                select(SensorReading.timestamp).order_by(SensorReading.timestamp.desc()).limit(1)
            )
            
            oldest_time = oldest.scalar()
            newest_time = newest.scalar()
            
            if oldest_time and newest_time:
                age = (newest_time - oldest_time).total_seconds() / 3600
                print(f"\n⏱️  Data Age:")
                print(f"   Oldest reading: {oldest_time}")
                print(f"   Newest reading: {newest_time}")
                print(f"   Time span: {age:.1f} hours ({age/24:.1f} days)")
                
                # Estimate readings per hour
                readings_per_hour = raw / age if age > 0 else 0
                print(f"   Readings/hour: {readings_per_hour:.0f}")
    
    # Get database file size
    db_path = Path("vayu_data.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"\n💾 Database Size: {size_mb:.2f} MB")
        
        # Estimate growth rate
        if raw > 0:
            bytes_per_reading = db_path.stat().st_size / (raw + hourly + daily)
            daily_growth = bytes_per_reading * 43200  # 2-second intervals
            print(f"   Est. daily growth: {daily_growth / (1024 * 1024):.2f} MB")
            print(f"   Est. 14-day size: {daily_growth * 14 / (1024 * 1024):.2f} MB")


async def optimize_indexes():
    """Optimize database indexes"""
    print("\n🔧 Optimizing Indexes")
    print("=" * 60)
    
    # Connect directly to SQLite for ANALYZE and VACUUM
    conn = sqlite3.connect('vayu_data.db')
    cursor = conn.cursor()
    
    try:
        # Analyze tables to update statistics
        print("\n   Running ANALYZE...")
        cursor.execute("ANALYZE")
        
        # Check if indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = cursor.fetchall()
        print(f"   Found {len(indexes)} custom indexes")
        for idx in indexes:
            print(f"      - {idx[0]}")
        
        # Create additional indexes if needed
        print("\n   Creating/verifying indexes...")
        
        # Index on timestamp for range queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
            ON sensor_readings(timestamp DESC)
        """)
        
        # Composite index for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_timestamp_aqlevel 
            ON sensor_readings(timestamp, air_quality_level)
        """)
        
        conn.commit()
        print("   ✅ Indexes optimized")
        
    finally:
        conn.close()


async def vacuum_database():
    """Vacuum database to reclaim space"""
    print("\n🧹 Vacuuming Database")
    print("=" * 60)
    
    db_path = Path("vayu_data.db")
    size_before = db_path.stat().st_size / (1024 * 1024)
    
    conn = sqlite3.connect('vayu_data.db')
    cursor = conn.cursor()
    
    try:
        print("   Running VACUUM (this may take a moment)...")
        cursor.execute("VACUUM")
        conn.commit()
        print("   ✅ Vacuum complete")
        
        size_after = db_path.stat().st_size / (1024 * 1024)
        savings = size_before - size_after
        
        print(f"\n   Size before: {size_before:.2f} MB")
        print(f"   Size after: {size_after:.2f} MB")
        print(f"   Space reclaimed: {savings:.2f} MB ({savings/size_before*100:.1f}%)")
        
    finally:
        conn.close()


async def test_query_performance():
    """Test query performance"""
    print("\n⚡ Query Performance Tests")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        tests = [
            ("Latest reading", select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(1)),
            ("Last hour readings", select(SensorReading).where(
                SensorReading.timestamp >= datetime.utcnow() - timedelta(hours=1)
            )),
            ("Count all readings", select(func.count(SensorReading.id))),
        ]
        
        for test_name, query in tests:
            start = datetime.utcnow()
            await db.execute(query)
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            
            status = "✅" if duration < 100 else "⚠️" if duration < 500 else "❌"
            print(f"   {status} {test_name}: {duration:.2f}ms")


async def suggest_optimizations():
    """Suggest further optimizations"""
    print("\n💡 Optimization Recommendations")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        raw_count = await db.execute(select(func.count(SensorReading.id)))
        raw = raw_count.scalar()
        
        hourly_count = await db.execute(select(func.count(HourlyAggregate.id)))
        hourly = hourly_count.scalar()
        
        recommendations = []
        
        if raw > 50000:
            recommendations.append("⚠️  High raw reading count. Consider shorter retention period.")
        
        if hourly == 0 and raw > 1000:
            recommendations.append("⚠️  No hourly aggregates found. Run aggregation to improve performance.")
        
        if raw > 100000:
            recommendations.append("🔴 Database growing large. Consider PostgreSQL for production.")
        
        if not recommendations:
            recommendations.append("✅ Database is well-optimized for current load!")
        
        for rec in recommendations:
            print(f"\n   {rec}")
        
        print("\n📋 Best Practices:")
        print("   • Keep raw data for 24 hours only")
        print("   • Run hourly aggregation every hour")
        print("   • Run daily aggregation once per day")
        print("   • Vacuum database weekly")
        print("   • Monitor database size regularly")


async def main():
    """Run all optimization tasks"""
    print("\n🚀 Vayu Database Optimization Tool")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    await analyze_database()
    await optimize_indexes()
    await test_query_performance()
    await vacuum_database()
    await suggest_optimizations()
    
    print("\n" + "=" * 60)
    print("✅ Optimization Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())