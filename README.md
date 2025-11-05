# Vayu: Air Monitor System

An ESP32 based Air Monitor System that sends the collected sensor data to a backend server via API requests. The backend stores this data in a database for historical analysis and retrieval. It also provides REST API endpoints for a React-based frontend application, where data visualization is implemented using Recharts to display real-time and historical air quality trends.




## Run Locally

To run this project locally follow the given instruction

Clone the project
```bash
  git clone https://github.com/nxd010/Vayu.git
```
Change Directory to backend
```bash
  cd backend
```
Then Start Server
```bash
  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal change to frontend

```bash
  cd frontend
```
Install dependencies
```bash
    npm install
```
Then Start Server
```bash
  npm run dev 
```
