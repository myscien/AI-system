import json
from models.question import Question


def normalize_answer(answer: list[str]) -> list[str]:
    return sorted([item.strip() for item in answer])


def score_question(question: Question, student_answer: list[str]) -> dict:
    correct_answer = json.loads(question.correct_answer_json)
    accepted_answers = json.loads(question.accepted_answers_json)
    options = json.loads(question.options_json)

    student_answer = [item.strip() for item in student_answer]
    question_type = question.question_type

    is_correct = False
    selected_option_explanation = ""

    if question_type in ["judgment", "single_choice"]:
        is_correct = student_answer == correct_answer

        if student_answer:
            selected_id = student_answer[0]
            for opt in options:
                if opt["id"] == selected_id:
                    selected_option_explanation = opt["explanation"]
                    break

    elif question_type == "multiple_choice":
        is_correct = normalize_answer(student_answer) == normalize_answer(correct_answer)

        if student_answer:
            explanations = []
            selected_ids = set(student_answer)
            for opt in options:
                if opt["id"] in selected_ids:
                    explanations.append(f'{opt["id"]}: {opt["explanation"]}')
            selected_option_explanation = " ".join(explanations)

    elif question_type == "blank":
        student_texts = [item.strip() for item in student_answer]
        accepted_set = set([item.strip() for item in accepted_answers])
        is_correct = any(ans in accepted_set for ans in student_texts)
        selected_option_explanation = ""

    score_awarded = question.score if is_correct else 0

    return {
        "question_pk": question.id,
        "student_answer": student_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "score_awarded": score_awarded,
        "selected_option_explanation": selected_option_explanation,
        "student_explanation": question.student_explanation,
    }
