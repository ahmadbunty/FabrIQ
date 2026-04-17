# Database Integration Guide

## Current Status: Mock Data

All dashboard endpoints currently return **hardcoded mock data**. This is intentional for initial development and testing.

## Endpoints Using Mock Data

### 1. Dashboard Stats (`/api/dashboard/stats`)
**Current:** Returns fixed values
```python
{
    'totalInspections': 1250,
    'defectsDetected': 234,
    'qualityScore': 85,
    'avgProcessingTime': 245,
}
```

### 2. Recent Detections (`/api/dashboard/recent-detections`)
**Current:** Returns 2 sample detections
```python
[
    {'class': 'knit hole', 'timestamp': '2024-01-15T10:30:00Z', 'grade': 'B'},
    {'class': 'oil spot', 'timestamp': '2024-01-15T10:25:00Z', 'grade': 'A'},
]
```

### 3. Defect Distribution (`/api/analytics/defect-distribution`)
**Current:** Returns fixed percentages
```python
[
    {'name': 'Knit Hole', 'value': 35},
    {'name': 'Oil Spot', 'value': 25},
    ...
]
```

### 4. Defect Trends (`/api/analytics/defect-trends`)
**Current:** Returns sample date/count pairs

### 5. Quality Trends (`/api/analytics/quality-trends`)
**Current:** Returns sample grade distribution

## Real Data Endpoints

### Detection (`/api/detection/analyze`)
**Status:** ✅ Uses real YOLO model (when loaded)
- Processes actual uploaded images
- Returns real detection results
- Only works if model is loaded

## How to Connect Real Data

### Option 1: SQLite (Simple, File-based)
```python
import sqlite3

# Initialize database
conn = sqlite3.connect('fabriq.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        quality_grade TEXT,
        confidence REAL,
        defect_count INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS defects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id INTEGER,
        class_name TEXT,
        confidence REAL,
        bbox TEXT,
        FOREIGN KEY (inspection_id) REFERENCES inspections(id)
    )
''')
conn.commit()
```

### Option 2: PostgreSQL (Production-ready)
```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='fabriq',
    user='your_user',
    password='your_password'
)
```

### Option 3: MongoDB (NoSQL)
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.fabriq
inspections = db.inspections
defects = db.defects
```

## Implementation Steps

1. **Store detection results** when images are analyzed
2. **Query database** in dashboard endpoints
3. **Calculate statistics** from real data
4. **Update frontend** to display real-time data

## Quick Fix: Store Results in Memory (Temporary)

For testing without a database, you can store results in memory:

```python
# Add to backend/app.py
STORED_RESULTS = []

@app.route('/api/detection/analyze', methods=['POST'])
@token_required
def analyze_image():
    # ... existing detection code ...
    
    # Store result
    result = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'defects': defects,
        'qualityGrade': quality_grade,
        'confidence': confidence,
    }
    STORED_RESULTS.append(result)
    
    return jsonify({...}), 200

@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    # Use STORED_RESULTS instead of mock data
    total = len(STORED_RESULTS)
    defects_count = sum(len(r['defects']) for r in STORED_RESULTS)
    # ... calculate real stats ...
```

## Next Steps

1. Choose a database (SQLite for simple, PostgreSQL for production)
2. Create database schema
3. Update detection endpoint to save results
4. Update dashboard endpoints to query database
5. Add data aggregation queries

Would you like me to implement database integration?

