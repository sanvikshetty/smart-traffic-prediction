import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env')

# Supports both Docker variables and the local pgAdmin setup.
DB_USER = os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres'))
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'postgres'))
DB_HOST = os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost'))
DB_PORT = os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'smart_traffic_db'))

DATABASE_URL = f'postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
