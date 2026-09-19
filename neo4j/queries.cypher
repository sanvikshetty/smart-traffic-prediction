// Connected junctions
MATCH (j:Junction {junction_id:$junction_id})-[:CONNECTED_TO]->(n:Junction)
RETURN n.junction_id AS junction_id,n.name AS name;

// Two-hop traversal
MATCH p=(j:Junction {junction_id:$junction_id})-[:CONNECTED_TO*1..2]->(n:Junction)
RETURN p;

// Most connected junctions
MATCH (j:Junction)
OPTIONAL MATCH (j)-[r:CONNECTED_TO]->()
RETURN j.junction_id AS junction_id,j.name AS name,count(r) AS outgoing_connections
ORDER BY outgoing_connections DESC;

// All road relationships
MATCH (a:Junction)-[r:CONNECTED_TO]->(b:Junction)
RETURN a.name AS from_junction,r.road_id AS road_id,b.name AS to_junction,r.length_km AS length_km;
