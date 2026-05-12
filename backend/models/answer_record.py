from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AnswerRecord(Base):
    __tablename__ = "answer_records"
    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "question_pk",
            "student_no",
            "session_id",
            name="uq_answer_record_first_submit",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True)
    question_pk: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    student_no: Mapped[str] = mapped_column(String(50), index=True)
    student_name: Mapped[str] = mapped_column(String(100), default="")
    session_id: Mapped[str] = mapped_column(String(100), index=True)

    student_answer_json: Mapped[str] = mapped_column(Text)
    correct_answer_json: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[int] = mapped_column(Integer)
    score_awarded: Mapped[int] = mapped_column(Integer, default=0)

    selected_option_explanation: Mapped[str] = mapped_column(Text, default="")
    student_explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
