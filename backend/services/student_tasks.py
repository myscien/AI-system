def infer_grade_from_student_id(student_id: str) -> int | None:
    graduation_year = int(student_id[:4])

    mapping = {
        2029: 6,
        2028: 7,
        2027: 8,
    }

    return mapping.get(graduation_year)
