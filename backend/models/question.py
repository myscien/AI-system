from __future__ import annotations

from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)

    knowledge_point: Mapped[str] = mapped_column(String(200))
    question_type: Mapped[str] = mapped_column(String(30))
    difficulty: Mapped[str] = mapped_column(String(20))
    stem: Mapped[str] = mapped_column(Text)

    # 先用 JSON 字符串存，最适合当前 SQLite 原型
    options_json: Mapped[str] = mapped_column(Text)
    correct_answer_json: Mapped[str] = mapped_column(Text)
    accepted_answers_json: Mapped[str] = mapped_column(Text)
    encouragement_json: Mapped[str] = mapped_column(Text, default="{}")

    student_explanation: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    task: Mapped["Task"] = relationship("Task", primaryjoin="Question.task_id == Task.id", viewonly=True)
