// Create the road-network graph from the same demonstration network used by PostgreSQL.
MERGE (j1:Junction {junction_id:'J001', name:'Panvel Central'});
MERGE (j2:Junction {junction_id:'J002', name:'Khandeshwar'});
MERGE (j3:Junction {junction_id:'J003', name:'Kalamboli'});
MERGE (j4:Junction {junction_id:'J004', name:'Kamothe'});
MERGE (j5:Junction {junction_id:'J005', name:'New Panvel'});

MERGE (s1:Sensor {sensor_id:'S001', sensor_code:'PNVL-001'});
MERGE (s2:Sensor {sensor_id:'S002', sensor_code:'KND-002'});
MERGE (s3:Sensor {sensor_id:'S003', sensor_code:'KLM-003'});
MERGE (s4:Sensor {sensor_id:'S004', sensor_code:'KMT-004'});
MERGE (s5:Sensor {sensor_id:'S005', sensor_code:'NPV-005'});
