from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app.models import models  # noqa
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        for col, col_type in [("notes", "TEXT"), ("contractor_notes", "TEXT"), ("accepted_by_user_id", "INTEGER")]:
            try:
                conn.execute(text(f"ALTER TABLE labour_requests ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass
