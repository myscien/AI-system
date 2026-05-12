from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_sqlite_schema_compatibility():
    with engine.begin() as conn:
        existing_tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }

        if not existing_tables:
            return

        task_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
        } if "tasks" in existing_tables else set()
        if "tasks" in existing_tables and "description" not in task_columns:
            conn.execute(
                text(
                    "ALTER TABLE tasks ADD COLUMN description VARCHAR(500) NOT NULL DEFAULT ''"
                )
            )

        question_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(questions)")).fetchall()
        } if "questions" in existing_tables else set()
        if "questions" in existing_tables and "encouragement_json" not in question_columns:
            conn.execute(
                text(
                    "ALTER TABLE questions ADD COLUMN encouragement_json TEXT NOT NULL DEFAULT '{}'"
                )
            )

        if "students" in existing_tables:
            student_columns = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(students)")).fetchall()
            }
            if "status" not in student_columns:
                conn.execute(
                    text(
                        "ALTER TABLE students ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'active'"
                    )
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
