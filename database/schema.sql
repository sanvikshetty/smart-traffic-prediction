CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS congestion_alerts CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS traffic_readings CASCADE;
DROP TABLE IF EXISTS sensors CASCADE;
DROP TABLE IF EXISTS roads CASCADE;
DROP TABLE IF EXISTS junctions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin','analyst','viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE junctions (
    junction_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE roads (
    road_id VARCHAR(20) PRIMARY KEY,
    road_name VARCHAR(160) NOT NULL,
    source_junction VARCHAR(20) NOT NULL REFERENCES junctions(junction_id),
    target_junction VARCHAR(20) NOT NULL REFERENCES junctions(junction_id),
    length_km NUMERIC(8,3) NOT NULL CHECK (length_km > 0),
    road_type VARCHAR(40) NOT NULL DEFAULT 'urban',
    speed_limit NUMERIC(6,2) NOT NULL CHECK (speed_limit > 0),
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (source_junction <> target_junction)
);

CREATE TABLE sensors (
    sensor_id VARCHAR(20) PRIMARY KEY,
    sensor_code VARCHAR(40) NOT NULL UNIQUE,
    junction_id VARCHAR(20) NOT NULL REFERENCES junctions(junction_id),
    location GEOMETRY(Point, 4326) NOT NULL,
    sensor_type VARCHAR(40) NOT NULL DEFAULT 'traffic_counter',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','maintenance')),
    installed_at DATE
);

CREATE TABLE traffic_readings (
    reading_id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(20) NOT NULL REFERENCES sensors(sensor_id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ NOT NULL,
    vehicle_count INTEGER NOT NULL CHECK (vehicle_count >= 0),
    average_speed NUMERIC(7,2) NOT NULL CHECK (average_speed >= 0),
    occupancy NUMERIC(5,4) NOT NULL CHECK (occupancy BETWEEN 0 AND 1),
    congestion_level VARCHAR(20) NOT NULL CHECK (congestion_level IN ('LOW','MEDIUM','HIGH','SEVERE'))
);

CREATE TABLE predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(20) NOT NULL REFERENCES sensors(sensor_id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    target_time TIMESTAMPTZ NOT NULL,
    horizon_minutes INTEGER NOT NULL CHECK (horizon_minutes IN (15,30,60)),
    predicted_volume NUMERIC(10,2) NOT NULL CHECK (predicted_volume >= 0),
    predicted_speed NUMERIC(7,2) CHECK (predicted_speed >= 0),
    predicted_congestion VARCHAR(20) NOT NULL CHECK (predicted_congestion IN ('LOW','MEDIUM','HIGH','SEVERE')),
    model_name VARCHAR(80) NOT NULL
);

CREATE TABLE congestion_alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(20) NOT NULL REFERENCES sensors(sensor_id) ON DELETE CASCADE,
    prediction_id BIGINT REFERENCES predictions(prediction_id) ON DELETE SET NULL,
    alert_level VARCHAR(20) NOT NULL CHECK (alert_level IN ('MEDIUM','HIGH','SEVERE')),
    message TEXT NOT NULL,
    threshold NUMERIC(10,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved'))
);

CREATE INDEX idx_junctions_location ON junctions USING GIST (location);
CREATE INDEX idx_roads_geometry ON roads USING GIST (geometry);
CREATE INDEX idx_sensors_location ON sensors USING GIST (location);
CREATE INDEX idx_sensors_junction ON sensors(junction_id);
CREATE INDEX idx_roads_source_target ON roads(source_junction, target_junction);
CREATE INDEX idx_readings_sensor_time ON traffic_readings(sensor_id, recorded_at DESC);
CREATE INDEX idx_readings_time ON traffic_readings(recorded_at DESC);
CREATE INDEX idx_predictions_sensor_target ON predictions(sensor_id, target_time DESC);
CREATE INDEX idx_alerts_status_time ON congestion_alerts(status, created_at DESC);

CREATE OR REPLACE VIEW v_current_traffic AS
SELECT DISTINCT ON (s.sensor_id)
    s.sensor_id, s.sensor_code, s.junction_id, j.name AS junction_name,
    tr.recorded_at, tr.vehicle_count, tr.average_speed, tr.occupancy, tr.congestion_level,
    ST_Y(s.location) AS latitude, ST_X(s.location) AS longitude
FROM sensors s
JOIN junctions j ON j.junction_id = s.junction_id
JOIN traffic_readings tr ON tr.sensor_id = s.sensor_id
ORDER BY s.sensor_id, tr.recorded_at DESC;

CREATE OR REPLACE VIEW v_junction_traffic AS
SELECT j.junction_id, j.name,
       ROUND(AVG(tr.vehicle_count),2) AS avg_volume,
       ROUND(MAX(tr.vehicle_count),2) AS max_volume,
       ROUND(AVG(tr.average_speed),2) AS avg_speed,
       COUNT(*) AS readings
FROM junctions j
JOIN sensors s ON s.junction_id = j.junction_id
JOIN traffic_readings tr ON tr.sensor_id = s.sensor_id
GROUP BY j.junction_id, j.name;
