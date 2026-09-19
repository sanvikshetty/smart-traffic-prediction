from pathlib import Path
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
uri=os.getenv('NEO4J_URI','bolt://localhost:7687')
user=os.getenv('NEO4J_USER','neo4j')
password=os.getenv('NEO4J_PASSWORD','trafficpassword')

def run_file(tx, path):
    statements=[s.strip() for s in path.read_text().split(';') if s.strip()]
    for statement in statements: tx.run(statement)

with GraphDatabase.driver(uri,auth=(user,password)) as driver:
    driver.verify_connectivity()
    with driver.session() as session:
        session.execute_write(run_file, ROOT/'neo4j'/'nodes.cypher')
        session.execute_write(run_file, ROOT/'neo4j'/'relationships.cypher')
print('Neo4j graph initialized.')
