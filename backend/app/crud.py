#CRUD operations for database

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app.models import SensorReading, HourlyAggregate, DailyAggregate
from app.schemas import SensorDataInput
from app.config import (
    RAW_DATA_RETENTION_DAYS,
    HOURLY_DATA_RETENTION_DAYS,
    DAILY_DATA_RETENTION_DAYS
)

logger = logging.getLogger(__name__)


# ===== Sensor Readings CRUD =====

async def create_sensor_reading(db: AsyncSession, data: SensorDataInput) -> SensorReading:
    """Create a new sensor reading"""
    reading = SensorReading(
        temperature=data.temperature,
        humidity=data.humidity,
        air_quality_voltage=data.airQualityVoltage,
        air_quality_level=data.airQualityLevel,
        timestamp=datetime.utcnow()
    )
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


async def get_latest_reading(db: AsyncSession) -> Optional[SensorReading]:
    """Get the most recent sensor reading"""
    result = await db.execute(
        select(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_readings_by_time_range(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    limit: int = 1000
) -> List[SensorReading]:
    """Get sensor readings within a time range"""
    result = await db.execute(
        select(SensorReading)
        .where(
            and_(
                SensorReading.timestamp >= start_time,
                SensorReading.timestamp <= end_time
            )
        )
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_total_readings_count(db: AsyncSession) -> int:
    """Get total count of sensor readings"""
    result = await db.execute(select(func.count(SensorReading.id)))
    return result.scalar() or 0


# ===== Hourly Aggregates CRUD =====

async def get_hourly_aggregates(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime
) -> List[HourlyAggregate]:
    """Get hourly aggregates within time range"""
    result = await db.execute(
        select(HourlyAggregate)
        .where(
            and_(
                HourlyAggregate.hour_start >= start_time,
                HourlyAggregate.hour_start <= end_time
            )
        )
        .order_by(HourlyAggregate.hour_start.asc())
    )
    return result.scalars().all()


async def create_hourly_aggregate(
    db: AsyncSession,
    hour_start: datetime
) -> Optional[HourlyAggregate]:
    """Create hourly aggregate from raw readings"""
    hour_end = hour_start + timedelta(hours=1)
    
    # Calculate aggregates using SQL
    result = await db.execute(
        select(
            func.avg(SensorReading.temperature).label('temp_avg'),
            func.min(SensorReading.temperature).label('temp_min'),
            func.max(SensorReading.temperature).label('temp_max'),
            func.avg(SensorReading.humidity).label('humidity_avg'),
            func.min(SensorReading.humidity).label('humidity_min'),
            func.max(SensorReading.humidity).label('humidity_max'),
            func.avg(SensorReading.air_quality_voltage).label('aq_avg'),
            func.min(SensorReading.air_quality_voltage).label('aq_min'),
            func.max(SensorReading.air_quality_voltage).label('aq_max'),
            func.count(SensorReading.id).label('count')
        )
        .where(
            and_(
                SensorReading.timestamp >= hour_start,
                SensorReading.timestamp < hour_end
            )
        )
    )
    
    stats = result.first()
    
    if stats and stats.count > 0:
        # Check if aggregate already exists
        existing = await db.execute(
            select(HourlyAggregate).where(HourlyAggregate.hour_start == hour_start)
        )
        if existing.scalar_one_or_none():
            logger.info(f"Hourly aggregate for {hour_start} already exists")
            return None
        
        aggregate = HourlyAggregate(
            hour_start=hour_start,
            temp_avg=float(stats.temp_avg),
            temp_min=float(stats.temp_min),
            temp_max=float(stats.temp_max),
            humidity_avg=float(stats.humidity_avg),
            humidity_min=float(stats.humidity_min),
            humidity_max=float(stats.humidity_max),
            aq_voltage_avg=float(stats.aq_avg),
            aq_voltage_min=float(stats.aq_min),
            aq_voltage_max=float(stats.aq_max),
            reading_count=stats.count,
            created_at=datetime.utcnow()
        )
        
        db.add(aggregate)
        await db.commit()
        await db.refresh(aggregate)
        logger.info(f"Created hourly aggregate for {hour_start}")
        return aggregate
    
    return None


# ===== Daily Aggregates CRUD =====

async def get_daily_aggregates(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> List[DailyAggregate]:
    """Get daily aggregates within date range"""
    result = await db.execute(
        select(DailyAggregate)
        .where(
            and_(
                DailyAggregate.date >= start_date,
                DailyAggregate.date <= end_date
            )
        )
        .order_by(DailyAggregate.date.asc())
    )
    return result.scalars().all()


async def create_daily_aggregate(
    db: AsyncSession,
    date: datetime
) -> Optional[DailyAggregate]:
    """Create daily aggregate from raw readings"""
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    # Calculate aggregates
    result = await db.execute(
        select(
            func.avg(SensorReading.temperature).label('temp_avg'),
            func.min(SensorReading.temperature).label('temp_min'),
            func.max(SensorReading.temperature).label('temp_max'),
            func.avg(SensorReading.humidity).label('humidity_avg'),
            func.min(SensorReading.humidity).label('humidity_min'),
            func.max(SensorReading.humidity).label('humidity_max'),
            func.avg(SensorReading.air_quality_voltage).label('aq_avg'),
            func.min(SensorReading.air_quality_voltage).label('aq_min'),
            func.max(SensorReading.air_quality_voltage).label('aq_max'),
            func.count(SensorReading.id).label('count')
        )
        .where(
            and_(
                SensorReading.timestamp >= day_start,
                SensorReading.timestamp < day_end
            )
        )
    )
    
    stats = result.first()
    
    if stats and stats.count > 0:
        # Check if aggregate already exists
        existing = await db.execute(
            select(DailyAggregate).where(DailyAggregate.date == day_start)
        )
        if existing.scalar_one_or_none():
            logger.info(f"Daily aggregate for {day_start.date()} already exists")
            return None
        
        aggregate = DailyAggregate(
            date=day_start,
            temp_avg=float(stats.temp_avg),
            temp_min=float(stats.temp_min),
            temp_max=float(stats.temp_max),
            humidity_avg=float(stats.humidity_avg),
            humidity_min=float(stats.humidity_min),
            humidity_max=float(stats.humidity_max),
            aq_voltage_avg=float(stats.aq_avg),
            aq_voltage_min=float(stats.aq_min),
            aq_voltage_max=float(stats.aq_max),
            reading_count=stats.count,
            created_at=datetime.utcnow()
        )
        
        db.add(aggregate)
        await db.commit()
        await db.refresh(aggregate)
        logger.info(f"Created daily aggregate for {day_start.date()}")
        return aggregate
    
    return None


# ===== Data Cleanup Operations =====

async def cleanup_old_data(db: AsyncSession):
    """Remove data older than retention periods"""
    now = datetime.utcnow()
    
    # Delete old raw readings
    raw_cutoff = now - timedelta(days=RAW_DATA_RETENTION_DAYS)
    result_raw = await db.execute(
        delete(SensorReading).where(SensorReading.timestamp < raw_cutoff)
    )
    await db.commit()
    logger.info(f"Deleted {result_raw.rowcount} old raw readings")
    
    # Delete old hourly aggregates
    hourly_cutoff = now - timedelta(days=HOURLY_DATA_RETENTION_DAYS)
    result_hourly = await db.execute(
        delete(HourlyAggregate).where(HourlyAggregate.hour_start < hourly_cutoff)
    )
    await db.commit()
    logger.info(f"Deleted {result_hourly.rowcount} old hourly aggregates")
    
    # Delete old daily aggregates
    daily_cutoff = now - timedelta(days=DAILY_DATA_RETENTION_DAYS)
    result_daily = await db.execute(
        delete(DailyAggregate).where(DailyAggregate.date < daily_cutoff)
    )
    await db.commit()
    logger.info(f"Deleted {result_daily.rowcount} old daily aggregates")


# ===== Statistics Operations =====

async def get_statistics(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime
) -> dict:
    """Get statistics for a time period"""
    result = await db.execute(
        select(
            func.count(SensorReading.id).label('total'),
            func.avg(SensorReading.temperature).label('temp_avg'),
            func.min(SensorReading.temperature).label('temp_min'),
            func.max(SensorReading.temperature).label('temp_max'),
            func.avg(SensorReading.humidity).label('humidity_avg'),
            func.min(SensorReading.humidity).label('humidity_min'),
            func.max(SensorReading.humidity).label('humidity_max'),
            func.avg(SensorReading.air_quality_voltage).label('aq_avg'),
            func.min(SensorReading.air_quality_voltage).label('aq_min'),
            func.max(SensorReading.air_quality_voltage).label('aq_max'),
        )
        .where(
            and_(
                SensorReading.timestamp >= start_time,
                SensorReading.timestamp <= end_time
            )
        )
    )
    
    stats = result.first()
    
    if stats and stats.total > 0:
        return {
            'period_start': start_time,
            'period_end': end_time,
            'total_readings': stats.total,
            'temperature': {
                'avg': round(float(stats.temp_avg), 2),
                'min': round(float(stats.temp_min), 2),
                'max': round(float(stats.temp_max), 2),
            },
            'humidity': {
                'avg': round(float(stats.humidity_avg), 2),
                'min': round(float(stats.humidity_min), 2),
                'max': round(float(stats.humidity_max), 2),
            },
            'air_quality': {
                'avg': round(float(stats.aq_avg), 3),
                'min': round(float(stats.aq_min), 3),
                'max': round(float(stats.aq_max), 3),
            }
        }
    
    return {
        'period_start': start_time,
        'period_end': end_time,
        'total_readings': 0,
        'temperature': {'avg': 0, 'min': 0, 'max': 0},
        'humidity': {'avg': 0, 'min': 0, 'max': 0},
        'air_quality': {'avg': 0, 'min': 0, 'max': 0},
    }