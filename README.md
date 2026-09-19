# Smart Traffic Prediction using Graph Neural Networks

A complete academic **Pre-Final Year Advanced Database** project. The database layer is the core: PostgreSQL + PostGIS + Neo4j manage relational, spatial and graph traffic information, while a PyTorch Geometric GCN provides traffic forecasting.

> The included traffic records are **synthetic demonstration data**. They are not presented as real-world traffic measurements.

## Architecture

```text
React + Plotly
      |
    FastAPI
      |
  +---+-------------+
  |         |       |
PostgreSQL PostGIS Neo4j
  |         |       |
  +---------+-------+
            |
      Python ML layer
            |
       PyTorch GCN
            |
     15/30/60 min forecast
            |
        PostgreSQL
```

## Features

- Relational schema with PK/FK/UNIQUE/CHECK/NOT NULL constraints
- PostgreSQL views, joins, aggregations and query-plan example
- Composite indexes and PostGIS GiST spatial indexes
- PostGIS point/line geometry, distance and proximity queries
- Neo4j road-network graph with Cypher traversal
- Traffic analytics and congestion classification
- React dashboard with Plotly charts and spatial map
- FastAPI REST endpoints with validation and error handling
- GCN traffic prediction with 15/30/60-minute horizons
- Linear Regression baseline and MAE/RMSE/MAPE evaluation
- Environment variables and Git-safe configuration

## Windows quick start

### 1. Prerequisites

Install:
- Docker Desktop
- Python 3.11 or newer
- Node.js 20 or newer
- Git

### 2. Clone and enter the repository

```powershell
git clone https://github.com/sanvikshetty/smart-traffic-prediction.git
cd smart-traffic-prediction
```

### 3. Create environment file

```powershell
Copy-Item .env.example .env
```

The Docker defaults already match `.env.example`: PostgreSQL password `postgres`, Neo4j password `trafficpassword`.

### 4. Start databases

```powershell
docker compose up -d
```

This creates PostgreSQL with PostGIS and loads the schema + clearly marked synthetic seed data. Neo4j starts separately.

### 5. Initialize Neo4j

Create Python environment:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r backend\\requirements.txt
```

Then:

```powershell
python scripts\\init_neo4j.py
```

### 6. Start FastAPI

From the repository root:

```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --reload --app-dir backend
```

API documentation is available at `http://localhost:8000/docs`.

### 7. Start React

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, normally `http://localhost:5173`.

## GNN training

The dashboard works immediately with a clearly labelled development fallback prediction. To train the actual GCN on the database data:

```powershell
python ml\\training\\train_gcn.py
```

This produces:
- `ml/models/gcn.pt`
- `ml/models/metrics.json`

Then generate database predictions:

```powershell
python ml\\training\\generate_predictions.py
```

Refresh the dashboard. The prediction cards will then show stored `GCN` predictions instead of the development fallback.

## API endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/traffic/current`
- `GET /api/traffic/history`
- `GET /api/traffic/{sensor_id}`
- `GET /api/sensors`
- `GET /api/junctions`
- `GET /api/analytics`
- `GET /api/congestion`
- `GET /api/prediction/{sensor_id}`
- `GET /api/graph/neighbors/{junction_id}`
- `GET /api/graph/summary`
- `POST /api/traffic/readings`

## Advanced Database viva points

1. PostgreSQL is the relational source of record.
2. PostGIS extends PostgreSQL for geographic data and spatial operators.
3. Neo4j represents junction connectivity naturally as a graph.
4. Composite index `(sensor_id, recorded_at)` supports sensor history queries.
5. GiST indexes support spatial search.
6. Views simplify repeated analytical queries.
7. Foreign keys preserve referential integrity.
8. CHECK constraints enforce domain rules at the database layer.
9. SQL handles aggregation and joins; Cypher handles graph traversal.
10. The GNN consumes traffic features plus road connectivity and stores predictions back into PostgreSQL.

## Dataset note

The repository is intentionally self-contained for college demonstration. The seeded dataset is synthetic and generated only for development. To use METR-LA or another public traffic forecasting dataset later, map its sensor/time-series fields into `traffic_readings` and construct its road graph in Neo4j. No real-world performance claim should be made until the real dataset is trained and evaluated.
