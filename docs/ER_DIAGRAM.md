# ER Diagram Description

## Core entities

```text
USERS
  |
  | administrative/system use
  |
  +-----------------------------+
                                |
JUNCTIONS 1 ----- N SENSORS 1 ----- N TRAFFIC_READINGS
    |                                  |
    |                                  |
    +---- ROADS -----------------------+
          source_junction
          target_junction

SENSORS 1 ----- N PREDICTIONS 1 ----- N CONGESTION_ALERTS
```

## Entities and key attributes

### users
- user_id (PK)
- name
- email (UNIQUE)
- role
- created_at

### junctions
- junction_id (PK)
- name
- location (PostGIS geometry)
- description
- created_at

### roads
- road_id (PK)
- road_name
- source_junction (FK -> junctions)
- target_junction (FK -> junctions)
- length_km
- road_type
- speed_limit
- geometry (PostGIS geometry)
- created_at

### sensors
- sensor_id (PK)
- sensor_code (UNIQUE)
- junction_id (FK -> junctions)
- location (PostGIS geometry)
- sensor_type
- status
- installed_at

### traffic_readings
- reading_id (PK)
- sensor_id (FK -> sensors)
- timestamp
- vehicle_count
- average_speed
- occupancy
- congestion_level

### predictions
- prediction_id (PK)
- sensor_id (FK -> sensors)
- generated_at
- target_time
- horizon_minutes
- predicted_volume
- predicted_speed
- predicted_congestion
- model_name

### congestion_alerts
- alert_id (PK)
- sensor_id (FK -> sensors)
- prediction_id (FK -> predictions)
- alert_level
- message
- threshold
- created_at
- resolved_at
- status

## Important relationships

- One junction can contain many sensors.
- One junction can be connected to many roads as either source or target.
- One sensor produces many traffic readings.
- One sensor can have many predictions.
- A prediction can generate congestion alerts.

## Normalization goal

The relational design separates entities and repeated facts so that sensor, junction, road and prediction attributes are not duplicated unnecessarily. Foreign keys maintain referential integrity.

The exact SQL data types, constraints and indexes will be implemented in Phase 2.
