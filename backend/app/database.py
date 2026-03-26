# database.py - This file handles the connection to our PostgreSQL database

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load variables from our .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the database engine
# This is like opening a phone line to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal is a "factory" that creates database sessions
# A session = one conversation with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our models (tables) will inherit from
Base = declarative_base()

# -----------------------------------------------
# Dependency function used in API routes
# This opens a DB session, gives it to the route,
# then closes it automatically when done
# -----------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db          # Give the session to whoever needs it
    finally:
        db.close()        # Always close, even if an error occurs