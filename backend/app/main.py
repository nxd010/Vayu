"""
FastAPI Main Application - Vayu Air Quality Monitor Backend
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import asyncio
import io
import csv

from app.database import init_db, get_db, close_db
from app.config import CORS_ORIGINS, API_PREFIX
from app.schemas import (
    SensorDataInput,
    SensorReadingResponse,
    AggregateResponse,
    StatisticsResponse,
    HealthResponse,
    MessageResponse
)
from app import crud

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task control
background_tasks_running = False


async def run_background_tasks():
    """Background tasks for data aggregation and cleanup"""
    global background_tasks_running
    background_tasks_running = True
    
    logger.info("Background tasks started")
    
    while background_tasks_running:
        try:
            # Wait 1 hour between runs
            await asyncio.sleep(3600)
            
            logger.info("Running scheduled tasks...")
            
            async with AsyncSession(bind=crud.engine) as db:
                # Create hourly aggregate for previous hour
                now = datetime.utcnow()
                prev_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
                await crud.create_hourly_aggregate(db, prev_hour)
                
                # Create daily aggregate for yesterday if it's a new day
                if now.hour == 0:
                    yesterday = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    await crud.create_daily_aggregate(db, yesterday)
                
                # Cleanup old data
                await crud.cleanup_old_data(db)
                
            logger.info("Scheduled tasks completed")
            
        except Exception as e:
            logger.error(f"Error in background tasks: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Vayu Air Monitor Backend...")
    await init_db()
    
    # Start background tasks
    task = asyncio.create_task(run_background_tasks())
    
    logger.info("Server ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    global background_tasks_running
    background_tasks_running = False
    task.cancel()
    await close_db()
    logger.info("Goodbye!")


# Create FastAPI app
app = FastAPI(
    title="Vayu Air Quality Monitor API",
    description="Backend API for ESP32-based air quality monitoring system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ===== Health Check Endpoint =====

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check API and database health"""
    try:
        total_readings = await crud.get_total_readings_count(db)
        latest = await crud.get_latest_reading(db)
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            database_connected=True,
            total_readings=total_readings,
            latest_reading_time=latest.timestamp if latest else None
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# ===== Sensor Data Endpoints =====

@app.post(f"{API_PREFIX}/sensor-data", response_model=SensorReadingResponse, tags=["Sensor Data"])
async def receive_sensor_data(
    data: SensorDataInput,
    db: AsyncSession = Depends(get_db)
):
    """Receive sensor data from ESP32"""
    try:
        reading = await crud.create_sensor_reading(db, data)
        logger.info(f"Received: Temp={reading.temperature}°C, Humidity={reading.humidity}%, AQ={reading.air_quality_level}")
        return reading
    except Exception as e:
        logger.error(f"Error saving sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/sensor-data/latest", response_model=SensorReadingResponse, tags=["Sensor Data"])
async def get_latest_sensor_data(db: AsyncSession = Depends(get_db)):
    """Get the most recent sensor reading"""
    reading = await crud.get_latest_reading(db)
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data available")
    return reading


@app.get(f"{API_PREFIX}/sensor-data/range", response_model=List[SensorReadingResponse], tags=["Sensor Data"])
async def get_sensor_data_range(
    hours: int = Query(1, ge=1, le=24, description="Number of hours to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """Get sensor readings for the last N hours"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    readings = await crud.get_readings_by_time_range(db, start_time, end_time)
    return readings


# ===== Aggregated Data Endpoints =====

@app.get(f"{API_PREFIX}/sensor-data/hourly", response_model=List[AggregateResponse], tags=["Aggregated Data"])
async def get_hourly_data(
    hours: int = Query(24, ge=1, le=168, description="Number of hours (max 7 days)"),
    db: AsyncSession = Depends(get_db)
):
    """Get hourly aggregated data"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    aggregates = await crud.get_hourly_aggregates(db, start_time, end_time)
    
    # Convert to response format
    return [
        AggregateResponse(
            timestamp=agg.hour_start,
            temp_avg=agg.temp_avg,
            temp_min=agg.temp_min,
            temp_max=agg.temp_max,
            humidity_avg=agg.humidity_avg,
            humidity_min=agg.humidity_min,
            humidity_max=agg.humidity_max,
            aq_voltage_avg=agg.aq_voltage_avg,
            aq_voltage_min=agg.aq_voltage_min,
            aq_voltage_max=agg.aq_voltage_max,
            reading_count=agg.reading_count
        )
        for agg in aggregates
    ]


@app.get(f"{API_PREFIX}/sensor-data/daily", response_model=List[AggregateResponse], tags=["Aggregated Data"])
async def get_daily_data(
    days: int = Query(7, ge=1, le=14, description="Number of days (max 14)"),
    db: AsyncSession = Depends(get_db)
):
    """Get daily aggregated data"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    aggregates = await crud.get_daily_aggregates(db, start_date, end_date)
    
    # Convert to response format
    return [
        AggregateResponse(
            timestamp=agg.date,
            temp_avg=agg.temp_avg,
            temp_min=agg.temp_min,
            temp_max=agg.temp_max,
            humidity_avg=agg.humidity_avg,
            humidity_min=agg.humidity_min,
            humidity_max=agg.humidity_max,
            aq_voltage_avg=agg.aq_voltage_avg,
            aq_voltage_min=agg.aq_voltage_min,
            aq_voltage_max=agg.aq_voltage_max,
            reading_count=agg.reading_count
        )
        for agg in aggregates
    ]


# ===== Statistics Endpoint =====

@app.get(f"{API_PREFIX}/statistics", response_model=StatisticsResponse, tags=["Statistics"])
async def get_statistics(
    hours: int = Query(24, ge=1, le=336, description="Time period in hours (max 14 days)"),
    db: AsyncSession = Depends(get_db)
):
    """Get statistical summary for a time period"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    stats = await crud.get_statistics(db, start_time, end_time)
    return StatisticsResponse(**stats)


# ===== Export Endpoint =====

@app.get(f"{API_PREFIX}/export/csv", tags=["Export"])
async def export_to_csv(
    hours: int = Query(24, ge=1, le=336, description="Number of hours to export"),
    db: AsyncSession = Depends(get_db)
):
    """Export sensor data to CSV"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    readings = await crud.get_readings_by_time_range(db, start_time, end_time, limit=10000)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'Temperature (°C)', 'Humidity (%)', 'Air Quality (V)', 'Air Quality Level'])
    
    # Write data
    for reading in reversed(readings):  # Oldest first
        writer.writerow([
            reading.timestamp.isoformat(),
            reading.temperature,
            reading.humidity,
            reading.air_quality_voltage,
            reading.air_quality_level
        ])
    
    # Prepare response
    output.seek(0)
    filename = f"vayu_data_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ===== Manual Aggregation Endpoint (for testing) =====

@app.post(f"{API_PREFIX}/aggregation/run", response_model=MessageResponse, tags=["Admin"])
async def run_manual_aggregation(db: AsyncSession = Depends(get_db)):
    """Manually trigger data aggregation (for testing)"""
    try:
        now = datetime.utcnow()
        
        # Create hourly aggregate for previous hour
        prev_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        hourly_result = await crud.create_hourly_aggregate(db, prev_hour)
        
        # Create daily aggregate for yesterday
        yesterday = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_result = await crud.create_daily_aggregate(db, yesterday)
        
        message = f"Aggregation completed. Hourly: {'created' if hourly_result else 'already exists'}, Daily: {'created' if daily_result else 'already exists'}"
        
        return MessageResponse(message=message)
    except Exception as e:
        logger.error(f"Manual aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Root Endpoint =====

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": "Vayu Air Quality Monitor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)