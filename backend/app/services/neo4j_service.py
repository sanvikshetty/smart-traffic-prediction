import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env')

URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
USER = os.getenv('NEO4J_USER', 'neo4j')
PASSWORD = os.getenv('NEO4J_PASSWORD', 'trafficpassword')

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    return _driver

def neighbors(junction_id: str):
    driver = get_driver()
    with driver.session() as session:
        result = session.run('''
            MATCH (j:Junction {junction_id:$junction_id})-[:CONNECTED_TO]->(n:Junction)
            RETURN n.junction_id AS junction_id, n.name AS name
            ORDER BY n.name
        ''', junction_id=junction_id)
        return [dict(r) for r in result]

def graph_summary():
    driver = get_driver()
    with driver.session() as session:
        nodes = session.run('MATCH (j:Junction) RETURN count(j) AS count').single()['count']
        edges = session.run('MATCH ()-[r:CONNECTED_TO]->() RETURN count(r) AS count').single()['count']
        return {'junctions': nodes, 'connections': edges}

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
