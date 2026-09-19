# Viva Questions and Short Answers

## Why PostgreSQL?
It provides a reliable relational system of record for structured sensor, reading, prediction and alert data and supports SQL joins, aggregation, constraints and indexes.

## Why PostGIS?
Traffic objects have geographic coordinates and road geometry. PostGIS adds geometry types, spatial operators and GiST indexes to PostgreSQL.

## Why Neo4j?
Road connectivity is naturally represented as nodes and relationships. Graph traversal can be expressed directly in Cypher.

## Why not store everything in Neo4j?
The project intentionally demonstrates multiple database models. Transactional and analytical traffic records are relational, spatial data is handled through PostGIS, and graph connectivity is handled through Neo4j.

## What is the composite index?
`traffic_readings(sensor_id, recorded_at)` is designed for the common query pattern of retrieving one sensor's history in time order.

## What is a spatial index?
A GiST index on PostGIS geometry accelerates spatial predicates such as proximity searches.

## What is normalization?
The schema separates independent entities such as junctions, sensors and readings and references them with keys to reduce redundancy and update anomalies.

## What is a GNN?
A Graph Neural Network learns from node features while aggregating information from neighboring nodes connected by graph edges.

## What does the GCN use here?
Four lagged traffic-volume values are node features and the road network provides graph edges.

## Why compare a baseline?
A simple Linear Regression baseline gives a reference point so GNN performance is evaluated rather than assumed.

## What metrics are used?
MAE, RMSE and MAPE on a held-out temporal test split.

## Are the seeded traffic numbers real?
No. They are synthetic demonstration data and must be labelled as such in the academic presentation.
