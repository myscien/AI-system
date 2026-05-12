from sqlalchemy import Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class SubmissionDetail(Base):
    __tablename__ = "submission_details"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    question_pk: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)

    student_answer_json: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[int] = mapped_column(Integer)  # 1 = correct, 0 = wrong
    score_awarded: Mapped[int] = mapped_column(Integer, default=0)

    selected_option_explanation: Mapped[str] = mapped_column(Text, default="")
    student_explanation: Mapped[str] = mapped_column(Text, default="")
