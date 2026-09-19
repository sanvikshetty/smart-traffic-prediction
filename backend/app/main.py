from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas import TrafficReadingIn
from app.services.neo4j_service import neighbors, graph_summary

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')

app = FastAPI(title='Smart Traffic Prediction API', version='1.0.0')
origin = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])


def rows(db: Session, sql: str, params=None):
    return [dict(r) for r in db.execute(text(sql), params or {}).mappings().all()]

@app.get('/api/health')
def health(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'status':'ok','database':'postgresql'}

@app.get('/api/dashboard')
def dashboard(db: Session = Depends(get_db)):
    r = db.execute(text('''
        SELECT
          (SELECT COUNT(*) FROM sensors) AS sensors,
          (SELECT COUNT(*) FROM junctions) AS junctions,
          COALESCE((SELECT ROUND(AVG(vehicle_count),2) FROM v_current_traffic),0) AS avg_traffic,
          COALESCE((SELECT ROUND(AVG(average_speed),2) FROM v_current_traffic),0) AS avg_speed,
          (SELECT COUNT(*) FROM v_current_traffic WHERE congestion_level IN ('HIGH','SEVERE')) AS congested
    ''')).mappings().one()
    return dict(r)

@app.get('/api/traffic/current')
def current_traffic(db: Session = Depends(get_db)):
    return rows(db, 'SELECT * FROM v_current_traffic ORDER BY vehicle_count DESC')

@app.get('/api/traffic/history')
def traffic_history(sensor_id: str | None = None, limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_db)):
    if sensor_id:
        return rows(db, '''SELECT recorded_at,sensor_id,vehicle_count,average_speed,occupancy,congestion_level
                           FROM traffic_readings WHERE sensor_id=:sensor_id ORDER BY recorded_at DESC LIMIT :limit''', {'sensor_id':sensor_id,'limit':limit})
    return rows(db, '''SELECT date_trunc('hour', recorded_at) AS bucket,
                              ROUND(AVG(vehicle_count),2) AS avg_volume,
                              ROUND(AVG(average_speed),2) AS avg_speed
                       FROM traffic_readings GROUP BY bucket ORDER BY bucket DESC LIMIT :limit''', {'limit':limit})

@app.get('/api/traffic/{sensor_id}')
def sensor_traffic(sensor_id: str, db: Session = Depends(get_db)):
    data = rows(db, '''SELECT * FROM traffic_readings WHERE sensor_id=:sensor_id ORDER BY recorded_at DESC LIMIT 100''', {'sensor_id':sensor_id})
    if not data:
        raise HTTPException(404, 'Sensor not found or has no readings')
    return data

@app.get('/api/sensors')
def sensors(db: Session = Depends(get_db)):
    return rows(db, '''SELECT s.sensor_id,s.sensor_code,s.junction_id,j.name AS junction_name,s.sensor_type,s.status,
                       ST_Y(s.location) AS latitude,ST_X(s.location) AS longitude
                       FROM sensors s JOIN junctions j USING(junction_id) ORDER BY s.sensor_id''')

@app.get('/api/junctions')
def junctions(db: Session = Depends(get_db)):
    return rows(db, '''SELECT junction_id,name,description,ST_Y(location) AS latitude,ST_X(location) AS longitude
                       FROM junctions ORDER BY junction_id''')

@app.get('/api/analytics')
def analytics(db: Session = Depends(get_db)):
    return {
        'junctions': rows(db, 'SELECT * FROM v_junction_traffic ORDER BY avg_volume DESC'),
        'hourly': rows(db, '''SELECT EXTRACT(HOUR FROM recorded_at)::int AS hour,ROUND(AVG(vehicle_count),2) AS avg_volume,
                              ROUND(AVG(average_speed),2) AS avg_speed FROM traffic_readings GROUP BY hour ORDER BY hour'''),
        'congestion': rows(db, '''SELECT congestion_level,COUNT(*) AS readings FROM traffic_readings GROUP BY congestion_level ORDER BY readings DESC''')
    }

@app.get('/api/congestion')
def congestion(db: Session = Depends(get_db)):
    return rows(db, '''SELECT ca.*,s.sensor_code,j.name AS junction_name FROM congestion_alerts ca
                       JOIN sensors s ON s.sensor_id=ca.sensor_id JOIN junctions j ON j.junction_id=s.junction_id
                       WHERE ca.status='open' ORDER BY ca.created_at DESC''')

@app.get('/api/prediction/{sensor_id}')
def prediction(sensor_id: str, db: Session = Depends(get_db)):
    exists = db.execute(text('SELECT 1 FROM sensors WHERE sensor_id=:id'), {'id':sensor_id}).first()
    if not exists:
        raise HTTPException(404, 'Sensor not found')
    stored = rows(db, '''SELECT sensor_id,generated_at,target_time,horizon_minutes,predicted_volume,predicted_speed,predicted_congestion,model_name
                         FROM predictions WHERE sensor_id=:id ORDER BY generated_at DESC,target_time LIMIT 3''', {'id':sensor_id})
    if stored:
        return {'source':'trained_model','predictions':stored}
    latest = db.execute(text('''SELECT vehicle_count,average_speed FROM traffic_readings WHERE sensor_id=:id ORDER BY recorded_at DESC LIMIT 1'''), {'id':sensor_id}).mappings().first()
    if not latest:
        raise HTTPException(404, 'No traffic history for sensor')
    # Safe development fallback. The GCN training pipeline can replace these values in predictions.
    base = float(latest['vehicle_count']); speed = float(latest['average_speed']); now = datetime.now(timezone.utc)
    result=[]
    for h,factor in ((15,1.03),(30,1.06),(60,1.10)):
        volume=round(base*factor,2); level='SEVERE' if volume>=120 else 'HIGH' if volume>=90 else 'MEDIUM' if volume>=65 else 'LOW'
        result.append({'sensor_id':sensor_id,'generated_at':now,'target_time':now+timedelta(minutes=h),'horizon_minutes':h,
                       'predicted_volume':volume,'predicted_speed':round(max(10,speed*(1-(factor-1)*1.5)),2),
                       'predicted_congestion':level,'model_name':'Development baseline (train GCN to replace)'})
    return {'source':'development_fallback','predictions':result}

@app.get('/api/graph/neighbors/{junction_id}')
def graph_neighbors(junction_id: str):
    try:
        return {'junction_id':junction_id,'neighbors':neighbors(junction_id)}
    except Exception as exc:
        raise HTTPException(503, f'Neo4j unavailable: {exc}')

@app.get('/api/graph/summary')
def graph_info():
    try:
        return graph_summary()
    except Exception as exc:
        raise HTTPException(503, f'Neo4j unavailable: {exc}')

@app.post('/api/traffic/readings')
def add_reading(payload: TrafficReadingIn, db: Session = Depends(get_db)):
    try:
        db.execute(text('''INSERT INTO traffic_readings(sensor_id,recorded_at,vehicle_count,average_speed,occupancy,congestion_level)
                           VALUES (:sensor_id,NOW(),:vehicle_count,:average_speed,:occupancy,:congestion_level)'''), payload.model_dump())
        db.commit()
        return {'message':'Reading stored'}
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
