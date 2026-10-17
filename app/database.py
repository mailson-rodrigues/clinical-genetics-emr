import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# In local development, with no extra configuration, we use SQLite
# (file "heredograma.db"). In production, set DATABASE_URL in .env
# pointing to a Postgres, in the format:
#   postgresql://user:password@host:port/database_name
# and run `alembic upgrade head` to create the tables there - the rest of the
# code (models, routes, Alembic) needs no changes.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./heredograma.db")

# "check_same_thread" only exists/makes sense for SQLite; passing it to
# the Postgres driver (psycopg2) would cause a connection error.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# "engine" is the connection to the database
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# "SessionLocal" is used to open conversations (sessions) with the database on each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# "Base" is the class that all our models (tables) will inherit from
Base = declarative_base()


def get_db():
    """
    Provides a database session for each API request
    and guarantees it is closed properly afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()