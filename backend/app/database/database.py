import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

if "channel_binding=" in db_url:
    db_url = db_url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")

connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
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

def ensure_schema_compatibility(engine_instance):
    """Adds missing columns dynamically to existing SQLite/PostgreSQL tables if needed."""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine_instance)
        table_names = inspector.get_table_names()

        if "quiz_questions" in table_names:
            cols = [col["name"] for col in inspector.get_columns("quiz_questions")]
            with engine_instance.begin() as conn:
                if "concept_area" not in cols:
                    conn.execute(text("ALTER TABLE quiz_questions ADD COLUMN concept_area VARCHAR(100) DEFAULT 'Core Concepts'"))
                if "question_type" not in cols:
                    conn.execute(text("ALTER TABLE quiz_questions ADD COLUMN question_type VARCHAR(50) DEFAULT 'concept_understanding'"))
                if "difficulty" not in cols:
                    conn.execute(text("ALTER TABLE quiz_questions ADD COLUMN difficulty VARCHAR(20) DEFAULT 'medium'"))

        if "quiz_attempts" in table_names:
            cols = [col["name"] for col in inspector.get_columns("quiz_attempts")]
            with engine_instance.begin() as conn:
                if "concept_breakdown" not in cols:
                    conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN concept_breakdown JSON"))

        if "subjects" in table_names:
            cols = [col["name"] for col in inspector.get_columns("subjects")]
            with engine_instance.begin() as conn:
                if "syllabus_text" not in cols:
                    conn.execute(text("ALTER TABLE subjects ADD COLUMN syllabus_text TEXT"))
                if "pyq_data" not in cols:
                    conn.execute(text("ALTER TABLE subjects ADD COLUMN pyq_data JSON"))

        if "units" in table_names:
            cols = [col["name"] for col in inspector.get_columns("units")]
            with engine_instance.begin() as conn:
                if "syllabus_text" not in cols:
                    conn.execute(text("ALTER TABLE units ADD COLUMN syllabus_text TEXT"))

        if "topics" in table_names:
            cols = [col["name"] for col in inspector.get_columns("topics")]
            with engine_instance.begin() as conn:
                if "learning_data" not in cols:
                    conn.execute(text("ALTER TABLE topics ADD COLUMN learning_data JSON"))
                if "pyq_frequency" not in cols:
                    conn.execute(text("ALTER TABLE topics ADD COLUMN pyq_frequency INTEGER DEFAULT 0"))
                if "pyq_notes" not in cols:
                    conn.execute(text("ALTER TABLE topics ADD COLUMN pyq_notes TEXT"))

        if "documents" in table_names:
            cols = [col["name"] for col in inspector.get_columns("documents")]
            with engine_instance.begin() as conn:
                if "resource_type" not in cols:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN resource_type VARCHAR(50) DEFAULT 'STUDY_RESOURCE'"))
    except Exception as e:
        logger.warning(f"Schema compatibility check warning: {e}")

try:
    ensure_schema_compatibility(engine)
except Exception:
    pass

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

