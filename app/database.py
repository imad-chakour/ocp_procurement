import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the local database URL
DATABASE_URL = "postgresql://postgres:postgre2024@localhost/OCPproject"

# Replace 'username', 'password', and 'dbname' with your local PostgreSQL credentials and database name
# Example: "postgresql://postgres:password@localhost/mydatabase"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_conn():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
