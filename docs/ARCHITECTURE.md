# System Architecture

## 1. Purpose

Smart Traffic Prediction using Graph Neural Networks is an Advanced Database project. The database layer is the primary engineering focus; the GNN is an integrated analytical feature.

## 2. High-Level Architecture

```text
React.js + Plotly Dashboard
            |
            | REST/JSON
            v
         FastAPI
            |
     +------+-------+----------------+
     |              |                |
     v              v                v
 PostgreSQL       PostGIS          Neo4j
 relational       spatial          graph
 traffic data    road geometry    road network
     |              |                |
     +--------------+----------------+
                    |
                    v
             Python Data Layer
                    |
                    v
          PyTorch Geometric / GCN
                    |
                    v
             Traffic Predictions
                    |
                    v
               PostgreSQL
                    |
                    v
              React Dashboard
```

## 3. Database Responsibilities

### PostgreSQL
- Sensors
- Junctions
- Roads
- Traffic readings
- Predictions
- Congestion alerts
- Users
- Constraints, indexes, joins, aggregations and views

### PostGIS
- Sensor locations
- Junction locations
- Road geometry
- Distance calculations
- Nearby-object queries
- Spatial indexing

### Neo4j
- Junction nodes
- Road/network relationships
- Graph traversal
- Neighbor discovery
- Connectivity analysis

## 4. GNN Integration

Traffic readings from PostgreSQL and road connectivity represented in the graph layer are transformed into a graph dataset for PyTorch Geometric. A simple GCN will initially predict traffic at 15-, 30- and 60-minute horizons. A baseline model will be evaluated alongside the GCN.

## 5. Design Principle

The project follows:

`Database -> Analytics/Graph -> ML -> Stored Predictions -> Web Application`

rather than treating the project as an ML-only application.
