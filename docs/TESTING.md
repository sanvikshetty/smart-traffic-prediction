# Testing Checklist

## Infrastructure

- [ ] Docker Desktop running
- [ ] PostgreSQL container healthy
- [ ] Neo4j container healthy
- [ ] PostGIS extension enabled

## Database

- [ ] `SELECT PostGIS_Version();` returns a version
- [ ] `SELECT COUNT(*) FROM traffic_readings;` returns seeded rows
- [ ] spatial proximity query in `database/queries.sql` succeeds
- [ ] `EXPLAIN ANALYZE` shows the expected query plan for indexed history lookup

## Neo4j

- [ ] `python scripts/init_neo4j.py` completes
- [ ] Junction node count is 5 for the included demo graph
- [ ] Connected-junction query returns relationships

## API

- [ ] `/api/health`
- [ ] `/api/dashboard`
- [ ] `/api/traffic/current`
- [ ] `/api/analytics`
- [ ] `/api/graph/summary`
- [ ] `/docs` Swagger UI opens
- [ ] invalid reading values are rejected by Pydantic validation

## Frontend

- [ ] Dashboard cards load
- [ ] Traffic Map renders spatial points
- [ ] Traffic Analytics charts render
- [ ] Prediction page returns 15/30/60-minute values
- [ ] Road Network neighbor query works
- [ ] Alerts table loads
- [ ] Database Insights page loads

## ML

- [ ] GCN training completes
- [ ] `metrics.json` is generated
- [ ] MAE/RMSE/MAPE are computed on a held-out test split
- [ ] Linear Regression baseline is evaluated on the same split
- [ ] GCN predictions can be stored in PostgreSQL

No model accuracy should be reported in academic documentation until the model has actually been trained and the metrics file has been generated.
