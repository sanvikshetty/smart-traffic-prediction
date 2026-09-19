INSERT INTO users(name,email,role) VALUES
('System Admin','admin@smarttraffic.local','admin'),
('Traffic Analyst','analyst@smarttraffic.local','analyst')
ON CONFLICT (email) DO NOTHING;

INSERT INTO junctions(junction_id,name,location,description) VALUES
('J001','Panvel Central','SRID=4326;POINT(73.1175 18.9894)','Central demonstration junction'),
('J002','Khandeshwar','SRID=4326;POINT(73.1030 19.0070)','Demonstration junction'),
('J003','Kalamboli','SRID=4326;POINT(73.1058 19.0178)','Demonstration junction'),
('J004','Kamothe','SRID=4326;POINT(73.0960 19.0165)','Demonstration junction'),
('J005','New Panvel','SRID=4326;POINT(73.1120 19.0015)','Demonstration junction')
ON CONFLICT (junction_id) DO NOTHING;

INSERT INTO roads(road_id,road_name,source_junction,target_junction,length_km,road_type,speed_limit,geometry) VALUES
('R001','Central-Khandeshwar','J001','J002',2.45,'arterial',50,'SRID=4326;LINESTRING(73.1175 18.9894,73.1030 19.0070)'),
('R002','Khandeshwar-Kalamboli','J002','J003',1.65,'arterial',50,'SRID=4326;LINESTRING(73.1030 19.0070,73.1058 19.0178)'),
('R003','Khandeshwar-Kamothe','J002','J004',1.90,'collector',40,'SRID=4326;LINESTRING(73.1030 19.0070,73.0960 19.0165)'),
('R004','Kalamboli-New Panvel','J003','J005',2.20,'arterial',50,'SRID=4326;LINESTRING(73.1058 19.0178,73.1120 19.0015)'),
('R005','Kamothe-New Panvel','J004','J005',1.80,'collector',40,'SRID=4326;LINESTRING(73.0960 19.0165,73.1120 19.0015)'),
('R006','New Panvel-Central','J005','J001',1.55,'urban',40,'SRID=4326;LINESTRING(73.1120 19.0015,73.1175 18.9894)')
ON CONFLICT (road_id) DO NOTHING;

INSERT INTO sensors(sensor_id,sensor_code,junction_id,location,sensor_type,status,installed_at) VALUES
('S001','PNVL-001','J001','SRID=4326;POINT(73.1175 18.9894)','camera','active','2025-06-01'),
('S002','KND-002','J002','SRID=4326;POINT(73.1030 19.0070)','loop','active','2025-06-01'),
('S003','KLM-003','J003','SRID=4326;POINT(73.1058 19.0178)','camera','active','2025-06-01'),
('S004','KMT-004','J004','SRID=4326;POINT(73.0960 19.0165)','radar','active','2025-06-01'),
('S005','NPV-005','J005','SRID=4326;POINT(73.1120 19.0015)','camera','active','2025-06-01')
ON CONFLICT (sensor_id) DO NOTHING;

-- Small clearly synthetic demonstration dataset. It is not real-world traffic data.
INSERT INTO traffic_readings(sensor_id,recorded_at,vehicle_count,average_speed,occupancy,congestion_level)
SELECT s.sensor_id,
       NOW() - (x.n * INTERVAL '15 minutes'),
       GREATEST(20, ROUND((55 + s.idx*13 + 35*sin(x.n/5.0) + (CASE WHEN EXTRACT(HOUR FROM NOW() - x.n*INTERVAL '15 minutes') BETWEEN 8 AND 10 THEN 35 ELSE 0 END) + (random()*18))::numeric)::int),
       GREATEST(12, ROUND((52 - s.idx*2 - 12*sin(x.n/5.0) - random()*8)::numeric,2)),
       LEAST(0.98, GREATEST(0.05, ROUND((0.20 + s.idx*0.06 + 0.18*sin(x.n/5.0) + random()*0.10)::numeric,4))),
       CASE
         WHEN (55 + s.idx*13 + 35*sin(x.n/5.0)) > 115 THEN 'SEVERE'
         WHEN (55 + s.idx*13 + 35*sin(x.n/5.0)) > 90 THEN 'HIGH'
         WHEN (55 + s.idx*13 + 35*sin(x.n/5.0)) > 65 THEN 'MEDIUM'
         ELSE 'LOW'
       END
FROM (VALUES ('S001',1),('S002',2),('S003',3),('S004',4),('S005',5)) s(sensor_id,idx)
CROSS JOIN generate_series(0,95) x(n);
