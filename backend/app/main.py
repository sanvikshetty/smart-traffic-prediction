from datetime import datetime, timezone
from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas import TrafficReadingIn
from app.services.gnn_service import run_gnn_prediction
from app.services.neo4j_service import neighbors, graph_summary

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')

app = FastAPI(title='Smart Traffic Prediction API', version='2.0.0')
origins = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
app.add_middleware(CORSMiddleware, allow_origins=[origins, 'http://localhost:3000'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])


def rows(db: Session, sql: str, params=None):
    return [dict(r) for r in db.execute(text(sql), params or {}).mappings().all()]


def tables(db: Session):
    return set(inspect(db.bind).get_table_names(schema='public'))


def is_new_project_schema(db: Session):
    return 'traffic_nodes' in tables(db) and 'traffic_data' in tables(db)


@app.get('/api/health')
def health(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'status': 'ok', 'database': 'postgresql', 'schema': 'traffic_nodes/traffic_data' if is_new_project_schema(db) else 'legacy'}


@app.get('/api/schema')
def schema_info(db: Session = Depends(get_db)):
    ts = sorted(tables(db))
    return {'database': 'connected', 'tables': ts, 'project_tables': [t for t in ['traffic_nodes','road_edges','traffic_data','traffic_predictions'] if t in ts]}


@app.get('/api/dashboard')
def dashboard(db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        return db.execute(text('''
            SELECT
              (SELECT COUNT(*) FROM traffic_nodes) AS nodes,
              (SELECT COUNT(*) FROM road_edges) AS roads,
              COALESCE((SELECT ROUND(AVG(vehicle_count),2) FROM traffic_data),0) AS avg_traffic,
              COALESCE((SELECT ROUND(AVG(average_speed),2) FROM traffic_data),0) AS avg_speed,
              COALESCE((SELECT ROUND(AVG(congestion_level),3) FROM traffic_data),0) AS avg_congestion,
              (SELECT COUNT(*) FROM traffic_data WHERE congestion_level >= 0.70) AS congested
        ''')).mappings().one()
    return db.execute(text('''
        SELECT (SELECT COUNT(*) FROM sensors) AS sensors,
               (SELECT COUNT(*) FROM junctions) AS junctions,
               COALESCE((SELECT ROUND(AVG(vehicle_count),2) FROM v_current_traffic),0) AS avg_traffic,
               COALESCE((SELECT ROUND(AVG(average_speed),2) FROM v_current_traffic),0) AS avg_speed,
               (SELECT COUNT(*) FROM v_current_traffic WHERE congestion_level IN ('HIGH','SEVERE')) AS congested
    ''')).mappings().one()


@app.get('/api/traffic/current')
def current_traffic(db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        return rows(db, '''SELECT td.traffic_id,td.node_id,n.node_name,n.latitude,n.longitude,n.road_type,
                                  td.recorded_at,td.vehicle_count,td.average_speed,td.congestion_level,td.weather
                           FROM traffic_data td JOIN traffic_nodes n USING(node_id)
                           WHERE td.recorded_at=(SELECT MAX(t2.recorded_at) FROM traffic_data t2 WHERE t2.node_id=td.node_id)
                           ORDER BY td.congestion_level DESC,td.vehicle_count DESC''')
    return rows(db, 'SELECT * FROM v_current_traffic ORDER BY vehicle_count DESC')


@app.get('/api/traffic/history')
def traffic_history(node_id: int | None = None, limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        if node_id is not None:
            return rows(db, '''SELECT recorded_at,node_id,vehicle_count,average_speed,congestion_level,weather
                               FROM traffic_data WHERE node_id=:node_id ORDER BY recorded_at DESC LIMIT :limit''', {'node_id':node_id,'limit':limit})
        return rows(db, '''SELECT date_trunc('hour',recorded_at) AS bucket,
                                  ROUND(AVG(vehicle_count),2) AS avg_volume,
                                  ROUND(AVG(average_speed),2) AS avg_speed,
                                  ROUND(AVG(congestion_level),3) AS avg_congestion
                           FROM traffic_data GROUP BY bucket ORDER BY bucket DESC LIMIT :limit''', {'limit':limit})
    return rows(db, '''SELECT date_trunc('hour',recorded_at) AS bucket,ROUND(AVG(vehicle_count),2) AS avg_volume,
                              ROUND(AVG(average_speed),2) AS avg_speed
                       FROM traffic_readings GROUP BY bucket ORDER BY bucket DESC LIMIT :limit''', {'limit':limit})


@app.get('/api/nodes')
def nodes(db: Session = Depends(get_db)):
    if not is_new_project_schema(db):
        return []
    return rows(db, 'SELECT * FROM traffic_nodes ORDER BY node_id')


@app.get('/api/edges')
def edges(db: Session = Depends(get_db)):
    if not is_new_project_schema(db):
        return []
    return rows(db, 'SELECT * FROM road_edges')


@app.get('/api/sensors')
def sensors(db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        return rows(db, '''SELECT node_id AS sensor_id,node_id::text AS sensor_code,node_id AS junction_id,
                                  node_name AS junction_name,road_type AS sensor_type,'active' AS status,
                                  latitude,longitude FROM traffic_nodes ORDER BY node_id''')
    return rows(db, '''SELECT s.sensor_id,s.sensor_code,s.junction_id,j.name AS junction_name,s.sensor_type,s.status,
                       ST_Y(s.location) AS latitude,ST_X(s.location) AS longitude
                       FROM sensors s JOIN junctions j USING(junction_id) ORDER BY s.sensor_id''')


@app.get('/api/junctions')
def junctions(db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        return rows(db, 'SELECT node_id AS junction_id,node_name AS name,road_type AS description,latitude,longitude FROM traffic_nodes ORDER BY node_id')
    return rows(db, 'SELECT junction_id,name,description,ST_Y(location) AS latitude,ST_X(location) AS longitude FROM junctions ORDER BY junction_id')


@app.get('/api/analytics')
def analytics(db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        return {
            'nodes': rows(db, '''SELECT n.node_name,ROUND(AVG(td.vehicle_count),2) AS avg_volume,
                                        ROUND(AVG(td.average_speed),2) AS avg_speed,
                                        ROUND(AVG(td.congestion_level),3) AS avg_congestion
                                 FROM traffic_nodes n JOIN traffic_data td USING(node_id)
                                 GROUP BY n.node_id,n.node_name ORDER BY avg_volume DESC'''),
            'hourly': rows(db, '''SELECT EXTRACT(HOUR FROM recorded_at)::int AS hour,
                                         ROUND(AVG(vehicle_count),2) AS avg_volume,
                                         ROUND(AVG(average_speed),2) AS avg_speed
                                  FROM traffic_data GROUP BY hour ORDER BY hour'''),
            'congestion': rows(db, '''SELECT CASE WHEN congestion_level>=0.80 THEN 'SEVERE' WHEN congestion_level>=0.60 THEN 'HIGH'
                                         WHEN congestion_level>=0.40 THEN 'MEDIUM' ELSE 'LOW' END AS level,COUNT(*) AS readings
                                  FROM traffic_data GROUP BY level ORDER BY readings DESC''')
        }
    return {
        'junctions': rows(db, 'SELECT * FROM v_junction_traffic ORDER BY avg_volume DESC'),
        'hourly': rows(db, '''SELECT EXTRACT(HOUR FROM recorded_at)::int AS hour,ROUND(AVG(vehicle_count),2) AS avg_volume,
                              ROUND(AVG(average_speed),2) AS avg_speed FROM traffic_readings GROUP BY hour ORDER BY hour'''),
        'congestion': rows(db, '''SELECT congestion_level,COUNT(*) AS readings FROM traffic_readings GROUP BY congestion_level ORDER BY readings DESC''')
    }


@app.post('/api/predict/gnn')
def gnn_predict(epochs: int = Query(300, ge=50, le=1000), db: Session = Depends(get_db)):
    if not is_new_project_schema(db):
        raise HTTPException(400, 'GNN endpoint requires traffic_nodes, road_edges and traffic_data tables')
    try:
        return run_gnn_prediction(db, epochs)
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))


@app.get('/api/predictions')
def predictions(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    if not is_new_project_schema(db) or 'traffic_predictions' not in tables(db):
        return []
    return rows(db, 'SELECT * FROM traffic_predictions ORDER BY prediction_time DESC LIMIT :limit', {'limit':limit})


@app.get('/api/prediction/{node_id}')
def prediction(node_id: int, db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        if 'traffic_predictions' in tables(db):
            stored = rows(db, 'SELECT * FROM traffic_predictions WHERE node_id=:id ORDER BY prediction_time DESC LIMIT 3', {'id':node_id})
            if stored:
                return {'source':'gnn_model','predictions':stored}
        latest = db.execute(text('''SELECT vehicle_count,average_speed,congestion_level FROM traffic_data
                                   WHERE node_id=:id ORDER BY recorded_at DESC LIMIT 1'''), {'id':node_id}).mappings().first()
        if not latest: raise HTTPException(404, 'Node not found')
        return {'source':'current_state','predictions':[dict(latest)]}
    raise HTTPException(400, 'Use the legacy sensor prediction endpoint with the legacy schema')


@app.get('/api/congestion')
def congestion(db: Session = Depends(get_db)):
    if is_new_project_schema(db):
        return rows(db, '''SELECT td.*,n.node_name FROM traffic_data td JOIN traffic_nodes n USING(node_id)
                           WHERE td.congestion_level>=0.70 ORDER BY td.recorded_at DESC LIMIT 100''')
    return rows(db, '''SELECT ca.*,s.sensor_code,j.name AS junction_name FROM congestion_alerts ca
                       JOIN sensors s ON s.sensor_id=ca.sensor_id JOIN junctions j ON j.junction_id=s.junction_id
                       WHERE ca.status='open' ORDER BY ca.created_at DESC''')


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
    if is_new_project_schema(db):
        raise HTTPException(400, 'For the current project schema, insert into traffic_data using the database SQL scripts.')
    try:
        db.execute(text('''INSERT INTO traffic_readings(sensor_id,recorded_at,vehicle_count,average_speed,occupancy,congestion_level)
                           VALUES (:sensor_id,NOW(),:vehicle_count,:average_speed,:occupancy,:congestion_level)'''), payload.model_dump())
        db.commit(); return {'message':'Reading stored'}
    except Exception as exc:
        db.rollback(); raise HTTPException(400, str(exc))
