import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    # Test connection
    with engine.connect() as conn:
        logger.info(f"Database connected successfully to {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    logger.warning(f"Could not connect to {db_url}: {e}. Falling back to SQLite for local session.")
    sqlite_url = "sqlite:///./sourcelearn.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
