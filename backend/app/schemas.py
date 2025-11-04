from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal


# ===== Input Schemas (from ESP32) =====

class SensorDataInput(BaseModel):
    """Schema for incoming sensor data from ESP32"""
    temperature: float = Field(..., ge=-50, le=100, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    airQualityVoltage: float = Field(..., ge=0, le=5, description="Air quality sensor voltage")
    airQualityLevel: Literal["Good", "Moderate", "Poor"] = Field(..., description="Air quality classification")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if v < -50 or v > 100:
            raise ValueError("Temperature out of realistic range")
        return v

    @field_validator("humidity")
    @classmethod
    def validate_humidity(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Humidity must be between 0 and 100")
        return v


# ===== Output Schemas (to Frontend) =====

class SensorReadingResponse(BaseModel):
    """Schema for sensor reading response"""
    id: int
    temperature: float
    humidity: float
    air_quality_voltage: float
    air_quality_level: str
    timestamp: datetime

    class Config:
        from_attributes = True


class AggregateResponse(BaseModel):
    """Schema for aggregated data response"""
    timestamp: datetime
    temp_avg: float
    temp_min: float
    temp_max: float
    humidity_avg: float
    humidity_min: float
    humidity_max: float
    aq_voltage_avg: float
    aq_voltage_min: float
    aq_voltage_max: float
    reading_count: int

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    """Schema for statistics response"""
    period_start: datetime
    period_end: datetime
    total_readings: int
    
    temperature: dict
    humidity: dict
    air_quality: dict

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    database_connected: bool
    total_readings: int
    latest_reading_time: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)