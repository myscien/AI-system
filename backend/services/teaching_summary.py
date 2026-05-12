from collections import defaultdict

from schemas.analysis import (
    QuestionAnalysisItem,
    StudentProgressItem,
    TaskAnalysisResponse,
)
from schemas.teaching_summary import (
    TeachingSummaryKnowledgePoint,
    TeachingSummaryOption,
    TeachingSummaryOverview,
    TeachingSummaryResponse,
    TeachingSummaryStudent,
    TeachingSummaryStudentGroups,
    TeachingSummaryTask,
    TeachingSummaryWeakQuestion,
    TeachingSummaryWrongOption,
)

WEAK_ACCURACY_THRESHOLD = 0.6
HIGH_ACCURACY_THRESHOLD = 0.85
MAX_FALLBACK_WEAK_QUESTIONS = 3
MAX_COPY_WEAK_QUESTIONS = 5


def _format_percent(value: float) -> str:
    return f"{round(value * 100, 1)}%"


def _mask_student_name(name: str) -> str:
    stripped_name = name.strip()
    if not stripped_name:
        return "\u672a\u77e5\u5b66\u751f"
    return f"{stripped_name[0]}**"


def _to_summary_student(student: StudentProgressItem) -> TeachingSummaryStudent:
    return TeachingSummaryStudent(
        student_no=student.student_no,
        student_name=student.student_name,
        grade=student.grade,
        class_name=student.class_name,
        answered_count=student.answered_count,
        correct_count=student.correct_count,
        accuracy=student.accuracy,
        progress=student.progress,
        status=student.status,
    )


def _build_options(question: QuestionAnalysisItem) -> list[TeachingSummaryOption]:
    stat_by_option_id = {
        stat.option_id: stat
        for stat in question.option_stats
    }
    correct_answer_set = set(question.correct_answer)

    options: list[TeachingSummaryOption] = []
    for option in question.options:
        option_stat = stat_by_option_id.get(option.id)
        options.append(
            TeachingSummaryOption(
                id=option.id,
                text=option.text,
                is_correct=option.id in correct_answer_set,
                selected_count=option_stat.count if option_stat else 0,
            )
        )
    return options


def _build_top_wrong_options(question: QuestionAnalysisItem) -> list[TeachingSummaryWrongOption]:
    return [
        TeachingSummaryWrongOption(
            option_id=stat.option_id,
            option_text=stat.option_text,
            count=stat.count,
        )
        for stat in sorted(
            question.option_stats,
            key=lambda item: (-item.count, item.option_id),
        )
        if not stat.is_correct and stat.count > 0
    ]


def _to_weak_question(question: QuestionAnalysisItem) -> TeachingSummaryWeakQuestion:
    return TeachingSummaryWeakQuestion(
        question_id=question.question_id,
        question_pk=question.question_pk,
        knowledge_point=question.knowledge_point,
        question_type=question.question_type,
        difficulty=question.difficulty,
        stem=question.stem,
        options=_build_options(question),
        correct_answer=question.correct_answer,
        total_answers=question.total_answers,
        correct_count=question.correct_count,
        wrong_count=question.wrong_count,
        accuracy=question.accuracy,
        top_wrong_options=_build_top_wrong_options(question),
    )


def _select_weak_questions(analysis: TaskAnalysisResponse) -> list[TeachingSummaryWeakQuestion]:
    weak_questions = [
        question
        for question in analysis.question_stats
        if question.total_answers > 0 and question.accuracy < WEAK_ACCURACY_THRESHOLD
    ]
    if not weak_questions:
        weak_questions = [
            question
            for question in sorted(
                analysis.question_stats,
                key=lambda item: (item.accuracy, item.question_pk),
            )[:MAX_FALLBACK_WEAK_QUESTIONS]
            if question.total_answers > 0
        ]

    return [
        _to_weak_question(question)
        for question in sorted(weak_questions, key=lambda item: (item.accuracy, item.question_pk))
    ]


def _build_knowledge_points(
    analysis: TaskAnalysisResponse,
) -> list[TeachingSummaryKnowledgePoint]:
    buckets: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {
            "question_count": 0,
            "accuracy_sum": 0.0,
            "weak_question_count": 0,
        }
    )
    for question in analysis.question_stats:
        bucket = buckets[question.knowledge_point]
        bucket["question_count"] += 1
        bucket["accuracy_sum"] += question.accuracy
        if question.total_answers > 0 and question.accuracy < WEAK_ACCURACY_THRESHOLD:
            bucket["weak_question_count"] += 1

    return [
        TeachingSummaryKnowledgePoint(
            knowledge_point=knowledge_point,
            question_count=int(bucket["question_count"]),
            average_accuracy=round(
                float(bucket["accuracy_sum"]) / int(bucket["question_count"]),
                4,
            ) if bucket["question_count"] else 0.0,
            weak_question_count=int(bucket["weak_question_count"]),
        )
        for knowledge_point, bucket in sorted(
            buckets.items(),
            key=lambda item: (
                -int(item[1]["weak_question_count"]),
                float(item[1]["accuracy_sum"]) / int(item[1]["question_count"])
                if item[1]["question_count"]
                else 0.0,
                item[0],
            ),
        )
    ]


def _build_student_groups(analysis: TaskAnalysisResponse) -> TeachingSummaryStudentGroups:
    not_started = [
        _to_summary_student(student)
        for student in analysis.student_progress
        if student.status == "not_started"
    ]
    in_progress = [
        _to_summary_student(student)
        for student in analysis.student_progress
        if student.status == "in_progress"
    ]
    low_accuracy = [
        _to_summary_student(student)
        for student in analysis.student_progress
        if student.answered_count > 0 and student.accuracy < WEAK_ACCURACY_THRESHOLD
    ]
    high_accuracy = [
        _to_summary_student(student)
        for student in analysis.student_progress
        if student.answered_count > 0 and student.accuracy >= HIGH_ACCURACY_THRESHOLD
    ]

    return TeachingSummaryStudentGroups(
        not_started=not_started,
        in_progress=in_progress,
        low_accuracy=sorted(low_accuracy, key=lambda item: (item.accuracy, item.student_no)),
        high_accuracy=sorted(high_accuracy, key=lambda item: (-item.accuracy, item.student_no)),
    )


def _build_copy_text(
    task: TeachingSummaryTask,
    overview: TeachingSummaryOverview,
    weak_questions: list[TeachingSummaryWeakQuestion],
    knowledge_points: list[TeachingSummaryKnowledgePoint],
    student_groups: TeachingSummaryStudentGroups,
) -> str:
    scope = f"{task.grade}年级"
    if task.class_name:
        scope += task.class_name

    lines = [
        f"任务：{task.task_title}",
        f"范围：{scope}",
        "",
        "一、整体情况",
        (
            f"应参与 {overview.assigned_students} 人，已提交 {overview.submitted_students} 人，"
            f"未开始 {overview.not_started_students} 人，已完成 {overview.completed_students} 人。"
        ),
        (
            f"完成率 {_format_percent(overview.completion_rate)}，"
            f"平均正确率 {_format_percent(overview.average_accuracy)}，"
            f"低正确率学生 {overview.low_accuracy_student_count} 人。"
        ),
        "",
        "二、薄弱知识点",
    ]

    if knowledge_points:
        for item in knowledge_points:
            if item.weak_question_count == 0:
                continue
            lines.append(
                (
                    f"- {item.knowledge_point}：共 {item.question_count} 题，"
                    f"平均正确率 {_format_percent(item.average_accuracy)}，"
                    f"薄弱题 {item.weak_question_count} 题。"
                )
            )
        if lines[-1] == "二、薄弱知识点":
            lines.append("- 暂无明显薄弱知识点。")
    else:
        lines.append("- 暂无知识点数据。")

    lines.extend(["", "三、薄弱题目"])
    if not weak_questions:
        lines.append("暂无薄弱题目。")
    for index, question in enumerate(weak_questions[:MAX_COPY_WEAK_QUESTIONS], start=1):
        lines.extend(
            [
                f"{index}. 题目ID：{question.question_id}",
                f"知识点：{question.knowledge_point}",
                f"题型：{question.question_type}",
                f"难度：{question.difficulty}",
                (
                    f"正确率：{_format_percent(question.accuracy)}，"
                    f"作答人数：{question.total_answers}，错误人数：{question.wrong_count}"
                ),
                "题干：",
                question.stem,
                "选项：",
            ]
        )
        for option in question.options:
            correctness = "正确" if option.is_correct else "错误"
            lines.append(
                f"{option.id}. {option.text}（{correctness}，{option.selected_count}人选择）"
            )
        lines.append(f"正确答案：{', '.join(question.correct_answer)}")
        if question.top_wrong_options:
            wrong_options = "；".join(
                f"{item.option_id} {item.option_text}，{item.count}人选择"
                for item in question.top_wrong_options
            )
            lines.append(f"主要错误选项：{wrong_options}")
        else:
            lines.append("主要错误选项：暂无。")
        lines.append("")

    lines.extend(
        [
            "四、学生分层",
            f"未开始学生：{len(student_groups.not_started)} 人",
            f"进行中学生：{len(student_groups.in_progress)} 人",
            f"低正确率学生：{len(student_groups.low_accuracy)} 人",
            f"高正确率学生：{len(student_groups.high_accuracy)} 人",
        ]
    )

    if student_groups.low_accuracy:
        names = "\n".join(
            (
                f"- 姓名：{_mask_student_name(student.student_name)} "
                f"学号：{student.student_no} 正确率：{_format_percent(student.accuracy)}"
            )
            for student in student_groups.low_accuracy[:10]
        )
        lines.append("低正确率学生名单示例：")
        lines.append(names)

    return "\n".join(lines).strip()


def build_teaching_summary(
    analysis: TaskAnalysisResponse,
    grade: str | None = None,
    class_name: str | None = None,
) -> TeachingSummaryResponse:
    task = TeachingSummaryTask(
        task_id=analysis.task_id,
        task_title=analysis.task_title,
        grade=grade or "",
        class_name=class_name,
    )
    overview = TeachingSummaryOverview(
        assigned_students=analysis.assigned_students,
        submitted_students=analysis.submitted_students,
        not_started_students=max(analysis.assigned_students - analysis.submitted_students, 0),
        completed_students=analysis.completed_students,
        completion_rate=analysis.completion_rate,
        average_accuracy=analysis.average_accuracy,
        low_accuracy_student_count=analysis.low_accuracy_student_count,
    )
    weak_questions = _select_weak_questions(analysis)
    knowledge_points = _build_knowledge_points(analysis)
    student_groups = _build_student_groups(analysis)

    return TeachingSummaryResponse(
        task=task,
        overview=overview,
        weak_questions=weak_questions,
        knowledge_points=knowledge_points,
        student_groups=student_groups,
        copy_text=_build_copy_text(
            task=task,
            overview=overview,
            weak_questions=weak_questions,
            knowledge_points=knowledge_points,
            student_groups=student_groups,
        ),
    )
