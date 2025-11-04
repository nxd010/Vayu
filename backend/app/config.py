from pathlib import Path

# Database Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "vayu_data.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# Data Retention Settings (in days)
RAW_DATA_RETENTION_DAYS = 1  # Keep raw data for 1 day
HOURLY_DATA_RETENTION_DAYS = 7  # Keep hourly data for 7 days
DAILY_DATA_RETENTION_DAYS = 14  # Keep daily data for 14 days

# API Configuration
API_PREFIX = "/api"
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative React dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Background Task Intervals (in seconds)
CLEANUP_INTERVAL = 3600  # Run cleanup every 1 hour
AGGREGATION_INTERVAL = 3600  # Run aggregation every 1 hour

# Sensor Configuration
SENSOR_READ_INTERVAL = 2  # ESP32 sends data every 2 seconds