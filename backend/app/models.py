#Database Models

from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class SensorReading(Base):
    """Raw sensor readings from ESP32 (stored for 24 hours)"""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    air_quality_voltage = Column(Float, nullable=False)
    air_quality_level = Column(String(20), nullable=False)  # Good/Moderate/Poor
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Index for efficient time-based queries
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<SensorReading(id={self.id}, temp={self.temperature}, timestamp={self.timestamp})>"


class HourlyAggregate(Base):
    """Hourly aggregated sensor data (stored for 7 days)"""
    __tablename__ = "hourly_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    hour_start = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Temperature statistics
    temp_avg = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    
    # Humidity statistics
    humidity_avg = Column(Float, nullable=False)
    humidity_min = Column(Float, nullable=False)
    humidity_max = Column(Float, nullable=False)
    
    # Air quality statistics
    aq_voltage_avg = Column(Float, nullable=False)
    aq_voltage_min = Column(Float, nullable=False)
    aq_voltage_max = Column(Float, nullable=False)
    
    # Count of readings in this hour
    reading_count = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_hour_start', 'hour_start'),
    )

    def __repr__(self):
        return f"<HourlyAggregate(hour={self.hour_start}, temp_avg={self.temp_avg})>"


class DailyAggregate(Base):
    """Daily aggregated sensor data (stored for 14 days)"""
    __tablename__ = "daily_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Temperature statistics
    temp_avg = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    
    # Humidity statistics
    humidity_avg = Column(Float, nullable=False)
    humidity_min = Column(Float, nullable=False)
    humidity_max = Column(Float, nullable=False)
    
    # Air quality statistics
    aq_voltage_avg = Column(Float, nullable=False)
    aq_voltage_min = Column(Float, nullable=False)
    aq_voltage_max = Column(Float, nullable=False)
    
    # Count of readings in this day
    reading_count = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_date', 'date'),
    )

    def __repr__(self):
        return f"<DailyAggregate(date={self.date}, temp_avg={self.temp_avg})>"