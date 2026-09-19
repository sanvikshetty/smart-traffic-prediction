# Smart Traffic Prediction using Graph Neural Networks

Academic **Pre-Final Advanced Database** project combining PostgreSQL, graph data, a GNN model and a React dashboard.

> The current traffic records shown in pgAdmin are synthetic demonstration data.

## Current project flow

```text
PostgreSQL (smart_traffic_db)
        |
        +--> traffic_nodes
        +--> road_edges
        +--> traffic_data
        +--> traffic_predictions
        |
        v
FastAPI backend
        |
        v
2-layer Graph Convolutional Network
        |
        v
15-minute traffic prediction
        |
        v
React + Plotly dashboard
```

## Database already prepared in pgAdmin

The current local setup uses:
- `traffic_nodes` — road/junction nodes and coordinates
- `road_edges` — graph connectivity
- `traffic_data` — vehicle count, speed and congestion observations
- `traffic_predictions` — model output

Indexes created in pgAdmin are retained for faster node/time queries.

## Windows + VS Code setup

### 1. Pull the latest project

```powershell
git pull origin main
```

### 2. Configure PostgreSQL

Copy `.env.example` to `.env` and set your actual PostgreSQL password.

Important defaults for the database you created manually:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smart_traffic_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PASSWORD
```

### 3. Create Python environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 4. Start FastAPI

From the repository root:

```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --reload --app-dir backend
```

API: `http://localhost:8000`
Swagger: `http://localhost:8000/docs`

### 5. Start the React dashboard

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

## GNN prediction

The backend now detects the four-table pgAdmin schema automatically.

Run the model through the API:

```text
POST http://localhost:8000/api/predict/gnn?epochs=300
```

Or use Swagger at `/docs`.

The endpoint:
1. Reads `traffic_nodes`.
2. Reads `road_edges` and constructs a normalized adjacency matrix.
3. Reads the latest `traffic_data` for every node.
4. Builds node features: vehicle count, average speed and congestion level.
5. Trains a two-layer GCN.
6. Generates the next-state development forecast.
7. Writes predictions to `traffic_predictions` when the table columns match.
8. Returns the prediction JSON to the dashboard.

### Important model limitation

The current pgAdmin data shown in the project has one timestamp per node. Therefore the model currently uses a documented short-horizon development target derived from the current state. For genuine supervised forecasting and MAE/RMSE evaluation, add multiple historical timestamps per node and train against the actual future observation.

## Useful API endpoints

- `GET /api/health` — PostgreSQL connectivity and schema detection
- `GET /api/schema` — database table inventory
- `GET /api/dashboard` — project KPIs
- `GET /api/nodes` — traffic nodes
- `GET /api/edges` — road graph edges
- `GET /api/traffic/current` — latest traffic per node
- `GET /api/traffic/history` — historical traffic / hourly aggregates
- `GET /api/analytics` — node, hourly and congestion analytics
- `POST /api/predict/gnn` — train and run the GNN
- `GET /api/predictions` — stored predictions
- `GET /api/prediction/{node_id}` — predictions for one node
- `GET /api/congestion` — high/severe congestion observations

## Advanced Database points for viva

1. PostgreSQL is the system of record.
2. `traffic_nodes` models entities in the road network.
3. `road_edges` represents graph relationships between nodes.
4. `traffic_data` stores time-dependent traffic features.
5. `traffic_predictions` stores derived ML results separately from raw observations.
6. Primary keys identify nodes and observations.
7. Foreign keys maintain node-to-traffic and edge-to-node integrity.
8. Indexes reduce lookup time for node and timestamp queries.
9. SQL performs filtering, joins and aggregation before the ML layer consumes data.
10. The GNN uses both node features and graph connectivity, unlike a plain tabular model.
11. Predictions are persisted back into PostgreSQL so the dashboard can query them.
12. The architecture keeps database, API, ML and presentation layers separate.

## Next data upgrade

For the final project, add 20–100+ timestamps per node. Then we can implement:
- train/validation/test split by time
- true next-step forecasting
- MAE, RMSE and MAPE
- baseline vs GNN comparison
- 15/30/60 minute horizons
- live dashboard refresh
