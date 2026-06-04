"""SQLAlchemy engine and session."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def init_db():
    """Create tables and seed default settings. Called once on startup."""
    import app.models  # noqa: F401 — register models with Base

    Base.metadata.create_all(bind=engine)

    # Seed default settings if not present
    from app.models import Setting
    db = SessionLocal()
    try:
        defaults = {
            "sync_interval_minutes": "60",
            "data_retention_days": "90",
        }
        for key, value in defaults.items():
            if not db.query(Setting).filter(Setting.key == key).first():
                db.add(Setting(key=key, value=value))
        db.commit()
    finally:
        db.close()


def get_db():
    """Yield a DB session. FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
