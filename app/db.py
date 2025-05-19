from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/fhir")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Detect dropped DB connections and auto-reconnect
    pool_recycle=1800,  # Recycle connections every 30 minutes
    connect_args={"sslmode": "require", "connect_timeout": 15},  # if using SSL (Render usually requires it)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
