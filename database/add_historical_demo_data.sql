-- Optional: generate 7 days of synthetic hourly traffic history.
-- Run only if you want a proper time-series dataset for GNN training.
-- This does NOT delete your current rows.

INSERT INTO traffic_data
    (node_id, vehicle_count, average_speed, congestion_level, weather, recorded_at)
SELECT
    n.node_id,
    GREATEST(50, ROUND((350 + n.node_id * 55
      + 180 * (0.5 + 0.5 * sin(EXTRACT(EPOCH FROM ts) / 43200.0))
      + 45 * sin(EXTRACT(EPOCH FROM ts) / 21600.0)
      + random() * 80)::numeric))::integer,
    ROUND(GREATEST(12, 42 - n.node_id * 0.7
      - 0.018 * (350 + n.node_id * 55)
      - random() * 8)::numeric, 2),
    ROUND(LEAST(1.0, GREATEST(0.05,
      0.18 + 0.0009 * (350 + n.node_id * 55)
      + 0.18 * (0.5 + 0.5 * sin(EXTRACT(EPOCH FROM ts) / 43200.0))
      + random() * 0.12))::numeric, 3),
    CASE WHEN random() < 0.10 THEN 'Rain' ELSE 'Clear' END,
    ts
FROM traffic_nodes n
CROSS JOIN generate_series(
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '1 hour',
    INTERVAL '1 hour'
) AS ts;

-- Verify the resulting time-series size.
SELECT node_id, COUNT(*) AS readings, MIN(recorded_at) AS first_reading,
       MAX(recorded_at) AS last_reading
FROM traffic_data
GROUP BY node_id
ORDER BY node_id;
