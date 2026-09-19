# Database Architecture

## 1. Multi-database design

The system intentionally uses three complementary database capabilities:

| Technology | Role | Main data |
|---|---|---|
| PostgreSQL | Relational system of record | sensors, junctions, roads, readings, predictions, alerts |
| PostGIS | Spatial extension of PostgreSQL | coordinates, road geometry, spatial relationships |
| Neo4j | Graph representation | junction connectivity and road-network traversal |

## 2. PostgreSQL relational model

```text
users

junctions
   |
   +----< sensors
   |          |
   |          +----< traffic_readings
   |          |
   |          +----< predictions
   |                         |
   |                         +----< congestion_alerts
   |
   +----< roads >---- junctions
```

## 3. Integrity rules

The schema will use:
- Primary keys on all entity tables
- Foreign keys for relationships
- NOT NULL on required attributes
- UNIQUE constraints for identifiers such as sensor_code and email
- CHECK constraints for non-negative traffic/speed and valid occupancy
- Timestamp fields for temporal traceability

## 4. Indexing plan

Initial indexes planned for Phase 2:

- sensors(junction_id)
- traffic_readings(sensor_id, timestamp)
- predictions(sensor_id, target_time)
- congestion_alerts(status, created_at)
- GiST spatial indexes on PostGIS geometry columns

Indexes will be justified according to query patterns rather than added indiscriminately.

## 5. Advanced query areas

Phase 2 will include SQL demonstrating:
- Multi-table joins
- GROUP BY and aggregation
- Peak-hour analysis
- Average traffic and speed
- Congestion analysis
- Historical time-window filtering
- Spatial proximity using PostGIS
- Distance calculations
- Query plans/performance comparison where useful

## 6. Graph model

Neo4j will represent road-network connectivity separately from the relational model:

```text
(:Junction)-[:CONNECTED_TO]->(:Junction)
```

Road and connectivity properties will be retained so that Cypher can demonstrate graph-specific traversal and connectivity queries.

## 7. Database-to-ML flow

```text
PostgreSQL traffic history
          |
          +------> feature preparation
          |
          v
Neo4j road connectivity
          |
          +------> graph edges
          |
          v
PyTorch Geometric
          |
          v
GCN predictions
          |
          v
PostgreSQL predictions
```
