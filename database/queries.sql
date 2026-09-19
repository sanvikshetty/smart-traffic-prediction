-- Advanced Database demonstration queries

-- 1. Current traffic from indexed history using the view.
SELECT * FROM v_current_traffic ORDER BY vehicle_count DESC;

-- 2. Average, maximum traffic and speed by junction.
SELECT * FROM v_junction_traffic ORDER BY avg_volume DESC;

-- 3. Peak traffic hour.
SELECT EXTRACT(HOUR FROM recorded_at) AS hour,
       ROUND(AVG(vehicle_count),2) AS avg_volume,
       MAX(vehicle_count) AS max_volume
FROM traffic_readings
GROUP BY EXTRACT(HOUR FROM recorded_at)
ORDER BY avg_volume DESC;

-- 4. Most congested junctions.
SELECT j.junction_id, j.name,
       ROUND(AVG(tr.vehicle_count),2) AS avg_volume,
       ROUND(AVG(tr.average_speed),2) AS avg_speed,
       COUNT(*) FILTER (WHERE tr.congestion_level IN ('HIGH','SEVERE')) AS high_congestion_readings
FROM junctions j
JOIN sensors s ON s.junction_id=j.junction_id
JOIN traffic_readings tr ON tr.sensor_id=s.sensor_id
GROUP BY j.junction_id,j.name
ORDER BY high_congestion_readings DESC;

-- 5. Traffic history for a sensor.
SELECT recorded_at, vehicle_count, average_speed, occupancy, congestion_level
FROM traffic_readings
WHERE sensor_id='S001'
ORDER BY recorded_at DESC
LIMIT 50;

-- 6. Spatial: sensors within 2 km of J001.
SELECT s.sensor_id, s.sensor_code,
       ROUND(ST_Distance(s.location::geography,j.location::geography)) AS distance_m
FROM sensors s
CROSS JOIN junctions j
WHERE j.junction_id='J001'
  AND ST_DWithin(s.location::geography,j.location::geography,2000)
ORDER BY distance_m;

-- 7. Road length and geometry summary.
SELECT road_id, road_name,
       ROUND(ST_Length(geometry::geography)) AS geometry_length_m,
       length_km
FROM roads;

-- 8. Join roads with their endpoint names.
SELECT r.road_id,r.road_name,
       a.name AS source_name,b.name AS target_name,
       r.length_km,r.speed_limit
FROM roads r
JOIN junctions a ON a.junction_id=r.source_junction
JOIN junctions b ON b.junction_id=r.target_junction
ORDER BY r.length_km;

-- 9. Query plan for sensor history. Run in PostgreSQL with EXPLAIN ANALYZE.
EXPLAIN ANALYZE
SELECT recorded_at,vehicle_count,average_speed
FROM traffic_readings
WHERE sensor_id='S001'
ORDER BY recorded_at DESC
LIMIT 20;
