MATCH (a:Junction {junction_id:'J001'}),(b:Junction {junction_id:'J002'}) MERGE (a)-[:CONNECTED_TO {road_id:'R001',length_km:2.45}]->(b);
MATCH (a:Junction {junction_id:'J002'}),(b:Junction {junction_id:'J003'}) MERGE (a)-[:CONNECTED_TO {road_id:'R002',length_km:1.65}]->(b);
MATCH (a:Junction {junction_id:'J002'}),(b:Junction {junction_id:'J004'}) MERGE (a)-[:CONNECTED_TO {road_id:'R003',length_km:1.90}]->(b);
MATCH (a:Junction {junction_id:'J003'}),(b:Junction {junction_id:'J005'}) MERGE (a)-[:CONNECTED_TO {road_id:'R004',length_km:2.20}]->(b);
MATCH (a:Junction {junction_id:'J004'}),(b:Junction {junction_id:'J005'}) MERGE (a)-[:CONNECTED_TO {road_id:'R005',length_km:1.80}]->(b);
MATCH (a:Junction {junction_id:'J005'}),(b:Junction {junction_id:'J001'}) MERGE (a)-[:CONNECTED_TO {road_id:'R006',length_km:1.55}]->(b);

MATCH (j:Junction {junction_id:'J001'}),(s:Sensor {sensor_id:'S001'}) MERGE (s)-[:MONITORS]->(j);
MATCH (j:Junction {junction_id:'J002'}),(s:Sensor {sensor_id:'S002'}) MERGE (s)-[:MONITORS]->(j);
MATCH (j:Junction {junction_id:'J003'}),(s:Sensor {sensor_id:'S003'}) MERGE (s)-[:MONITORS]->(j);
MATCH (j:Junction {junction_id:'J004'}),(s:Sensor {sensor_id:'S004'}) MERGE (s)-[:MONITORS]->(j);
MATCH (j:Junction {junction_id:'J005'}),(s:Sensor {sensor_id:'S005'}) MERGE (s)-[:MONITORS]->(j);
