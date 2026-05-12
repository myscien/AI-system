from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    grade: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(500), default="")
    _legacy_class_name: Mapped[str] = mapped_column("class_name", String(50), default="")
    _legacy_question_count: Mapped[int] = mapped_column("question_count", Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        primaryjoin="Task.id == Question.task_id",
        viewonly=True,
    )

    @property
    def question_count(self) -> int:
        return len(self.questions)
