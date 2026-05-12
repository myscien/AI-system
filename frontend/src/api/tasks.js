const STUDENT_TASKS_URL = "/api/student/tasks";
const TASKS_URL = "/api/tasks";
const TEACHER_TASKS_URL = "/api/teacher/tasks";
const TEACHER_STUDENTS_IMPORT_CSV_URL = "/api/teacher/students/import-csv";

async function getErrorDetail(response, fallbackMessage) {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string" && data.detail.trim()) {
      return data.detail.trim();
    }
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      return data.detail
        .map((item) => {
          const path = Array.isArray(item?.loc) ? item.loc.join(".") : "";
          const message = String(item?.msg || "").trim();
          return [path, message].filter(Boolean).join(": ");
        })
        .filter(Boolean)
        .join("；");
    }
    if (typeof data?.message === "string" && data.message.trim()) {
      return data.message.trim();
    }
  } catch {
    // ignore parse failures and fall back to the default message
  }

  return fallbackMessage;
}

function normalizeTask(task) {
  return {
    ...task,
    id: task.id ?? task.task_id,
    task_id: task.task_id ?? task.taskId ?? task.id,
    title: task.title ?? "",
    grade: task.grade ?? "",
    question_count: task.question_count ?? task.questionCount ?? 0,
    status:
      task.status ??
      task.publish_status ??
      task.publishStatus ??
      task.task_status ??
      task.taskStatus ??
      (task.is_archived || task.isArchived ? "archived" : ""),
    class_name: task.class_name ?? task.className ?? "",
    student_task_status: task.student_task_status ?? task.studentTaskStatus ?? "",
    attempt_count: task.attempt_count ?? task.attemptCount ?? 0,
    answered_count: task.answered_count ?? task.answeredCount ?? 0,
    correct_count: task.correct_count ?? task.correctCount ?? 0,
    accuracy: task.accuracy ?? null,
    progress: task.progress ?? null,
    last_submit_at: task.last_submit_at ?? task.lastSubmitAt ?? "",
  };
}

function normalizeStudentProfile(student, fallbackStudentNo = "") {
  if (!student || typeof student !== "object") {
    return null;
  }

  return {
    student_no: student.student_no ?? student.studentNo ?? fallbackStudentNo,
    student_name: student.student_name ?? student.studentName ?? "",
    grade: student.grade ?? "",
    class_name: student.class_name ?? student.className ?? "",
    status: student.status ?? "",
  };
}

function normalizeTeacherTask(task) {
  return {
    ...task,
    id: task.id ?? task.task_id,
    title: task.title ?? "",
    grade: task.grade ?? "",
    description: task.description ?? "",
    question_count: task.question_count ?? task.questionCount ?? 0,
    status: task.status ?? "",
    created_at: task.created_at ?? task.createdAt ?? "",
  };
}

function normalizeQuestion(question) {
  const correctAnswer = Array.isArray(question.correct_answer)
    ? question.correct_answer
    : Array.isArray(question.correctAnswer)
      ? question.correctAnswer
      : [];
  const acceptedAnswers = Array.isArray(question.accepted_answers)
    ? question.accepted_answers
    : Array.isArray(question.acceptedAnswers)
      ? question.acceptedAnswers
      : [];

  return {
    ...question,
    question_pk:
      question.question_pk ?? question.questionPk ?? question.question_id ?? question.questionId ?? "",
    knowledge_point: question.knowledge_point ?? question.knowledgePoint ?? "",
    question_type: question.question_type ?? question.questionType ?? "",
    difficulty: question.difficulty ?? "",
    stem: question.stem ?? "",
    options: Array.isArray(question.options) ? question.options : [],
    correct_answer: correctAnswer,
    accepted_answers: acceptedAnswers,
    encouragement: question.encouragement ?? {},
    student_explanation: question.student_explanation ?? question.studentExplanation ?? "",
    score: question.score ?? 0,
  };
}

function normalizeAttemptSummary(item) {
  if (!item || typeof item !== "object") {
    return null;
  }

  return {
    session_id: item.session_id ?? item.sessionId ?? "",
    answered_count: item.answered_count ?? item.answeredCount ?? 0,
    correct_count: item.correct_count ?? item.correctCount ?? 0,
    accuracy: item.accuracy ?? null,
    progress: item.progress ?? null,
    submitted_at: item.submitted_at ?? item.submittedAt ?? "",
  };
}

function normalizeQuestionResultItem(item) {
  return {
    question_pk: item.question_pk ?? item.questionPk ?? item.question_id ?? item.questionId ?? "",
    attempt_count: item.attempt_count ?? item.attemptCount ?? 0,
    first_is_correct: item.first_is_correct ?? item.firstIsCorrect ?? null,
    latest_is_correct: item.latest_is_correct ?? item.latestIsCorrect ?? null,
    best_is_correct: item.best_is_correct ?? item.bestIsCorrect ?? null,
  };
}

export async function getTasks(studentNo) {
  const params = new URLSearchParams();
  if (studentNo) {
    params.set("student_id", studentNo);
  }

  const url = params.toString()
    ? `${STUDENT_TASKS_URL}?${params.toString()}`
    : STUDENT_TASKS_URL;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to load tasks"));
  }

  const data = await response.json();
  const taskList = Array.isArray(data) ? data : data.tasks || [];
  const student = Array.isArray(data)
    ? null
    : normalizeStudentProfile(data.student, String(studentNo || "").trim());

  return {
    student,
    tasks: taskList.map(normalizeTask),
  };
}

export async function getStudentTaskSummary(taskId, studentNo) {
  const params = new URLSearchParams();
  if (studentNo) {
    params.set("student_id", studentNo);
  }

  const response = await fetch(`${STUDENT_TASKS_URL}/${taskId}/summary?${params.toString()}`);
  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to load task summary"));
  }

  const data = await response.json();

  return {
    ...data,
    task_id: data.task_id ?? data.taskId ?? Number(taskId),
    task_title: data.task_title ?? data.taskTitle ?? "",
    student_no: data.student_no ?? data.studentNo ?? String(studentNo || "").trim(),
    student_name: data.student_name ?? data.studentName ?? "",
    question_count: data.question_count ?? data.questionCount ?? 0,
    attempt_count: data.attempt_count ?? data.attemptCount ?? 0,
    latest_attempt: normalizeAttemptSummary(data.latest_attempt ?? data.latestAttempt),
    best_accuracy: data.best_accuracy ?? data.bestAccuracy ?? null,
    history: Array.isArray(data.history) ? data.history.map(normalizeAttemptSummary).filter(Boolean) : [],
    question_results: Array.isArray(data.question_results)
      ? data.question_results.map(normalizeQuestionResultItem)
      : Array.isArray(data.questionResults)
        ? data.questionResults.map(normalizeQuestionResultItem)
        : [],
  };
}

export async function getQuestions(taskId) {
  const response = await fetch(`${TASKS_URL}/${taskId}/questions`);
  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to load questions"));
  }
  return response.json();
}

export async function getTeacherTaskQuestions(taskId) {
  const data = await getQuestions(taskId);
  const questionList = Array.isArray(data) ? data : data.questions || [];
  return questionList.map(normalizeQuestion);
}

export async function getTeacherTasks() {
  const response = await fetch(TEACHER_TASKS_URL);
  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to load teacher tasks"));
  }

  const data = await response.json();
  const taskList = Array.isArray(data) ? data : data.tasks || [];
  return taskList.map(normalizeTeacherTask);
}

export async function createTeacherTask(payload) {
  const response = await fetch(TEACHER_TASKS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to create teacher task"));
  }

  const data = await response.json();
  return normalizeTeacherTask(data);
}

export async function updateTeacherTask(taskId, payload) {
  const response = await fetch(`${TEACHER_TASKS_URL}/${taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to update teacher task"));
  }

  const data = await response.json();
  return normalizeTeacherTask(data);
}

export async function deleteTeacherTask(taskId) {
  const response = await fetch(`${TEACHER_TASKS_URL}/${taskId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to delete teacher task"));
  }

  return response.json();
}

export async function importTeacherQuestions(taskId, questions) {
  const response = await fetch(`${TEACHER_TASKS_URL}/${taskId}/questions/import`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(questions),
  });

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to import teacher questions"));
  }

  return response.json();
}

export async function updateTeacherQuestion(taskId, questionPk, payload) {
  const response = await fetch(
    `${TEACHER_TASKS_URL}/${taskId}/questions/${encodeURIComponent(questionPk)}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to update teacher question"));
  }

  const data = await response.json();
  return normalizeQuestion(data);
}

export async function deleteTeacherQuestion(taskId, questionPk) {
  const response = await fetch(
    `${TEACHER_TASKS_URL}/${taskId}/questions/${encodeURIComponent(questionPk)}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to delete teacher question"));
  }

  return response.json();
}

export async function importTeacherStudentsCsv(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(TEACHER_STUDENTS_IMPORT_CSV_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to import students"));
  }

  return response.json();
}

function normalizeQuestionAnalysisItem(item) {
  const optionList = Array.isArray(item.options) ? item.options : [];
  const correctAnswer = Array.isArray(item.correct_answer)
    ? item.correct_answer
    : Array.isArray(item.correctAnswer)
      ? item.correctAnswer
      : [];
  const optionStats = Array.isArray(item.option_stats)
    ? item.option_stats
    : Array.isArray(item.optionStats)
      ? item.optionStats
      : [];

  return {
    question_id: item.question_id ?? item.questionId ?? item.question_pk ?? item.questionPk ?? "",
    question_pk: item.question_pk ?? item.questionPk ?? item.question_id ?? item.questionId ?? "",
    knowledge_point: item.knowledge_point ?? item.knowledgePoint ?? "",
    question_type: item.question_type ?? item.questionType ?? "",
    difficulty: item.difficulty ?? "",
    stem: item.stem ?? "",
    options: optionList.map((option) => ({
      id: option.id ?? option.option_id ?? option.optionId ?? "",
      text: option.text ?? option.option_text ?? option.optionText ?? "",
      explanation: option.explanation ?? "",
    })),
    correct_answer: correctAnswer,
    total_answers: item.total_answers ?? item.totalAnswers ?? 0,
    correct_count: item.correct_count ?? item.correctCount ?? 0,
    wrong_count: item.wrong_count ?? item.wrongCount ?? 0,
    accuracy: item.accuracy ?? null,
    option_stats: optionStats.map((option) => ({
      option_id: option.option_id ?? option.optionId ?? option.id ?? "",
      option_text: option.option_text ?? option.optionText ?? option.text ?? "",
      count: option.count ?? 0,
      is_correct: option.is_correct ?? option.isCorrect ?? false,
    })),
  };
}

function normalizeStudentProgressItem(item) {
  return {
    student_no: item.student_no ?? item.studentNo ?? "",
    student_name: item.student_name ?? item.studentName ?? "",
    grade: item.grade ?? "",
    class_name: item.class_name ?? item.className ?? "",
    answered_count: item.answered_count ?? item.answeredCount ?? 0,
    correct_count: item.correct_count ?? item.correctCount ?? 0,
    accuracy: item.accuracy ?? null,
    progress: item.progress ?? null,
    status: item.status ?? "",
    is_low_accuracy: item.is_low_accuracy ?? item.isLowAccuracy ?? false,
  };
}

function normalizeClassName(value) {
  return String(value || "").trim().replace(/班$/, "");
}

export async function getTaskAnalysis(taskId, filters = {}) {
  const params = new URLSearchParams();
  const grade = String(filters.grade || "").trim();
  const className = normalizeClassName(filters.class_name || filters.className);

  if (grade) {
    params.set("grade", grade);
  }
  if (className) {
    params.set("class_name", className);
  }

  const query = params.toString();
  const url = query
    ? `${TASKS_URL}/${taskId}/analysis?${query}`
    : `${TASKS_URL}/${taskId}/analysis`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to load task analysis"));
  }

  const data = await response.json();

  return {
    ...data,
    task_id: data.task_id ?? data.taskId ?? Number(taskId),
    task_title: data.task_title ?? data.taskTitle ?? data.title ?? "",
    total_students: data.total_students ?? data.totalStudents ?? 0,
    assigned_students: data.assigned_students ?? data.assignedStudents ?? data.total_students ?? data.totalStudents ?? 0,
    submitted_students: data.submitted_students ?? data.submittedStudents ?? 0,
    completed_students: data.completed_students ?? data.completedStudents ?? 0,
    completion_rate: data.completion_rate ?? data.completionRate ?? null,
    average_accuracy: data.average_accuracy ?? data.averageAccuracy ?? null,
    low_accuracy_student_count:
      data.low_accuracy_student_count ?? data.lowAccuracyStudentCount ?? 0,
    question_stats: Array.isArray(data.question_stats)
      ? data.question_stats.map(normalizeQuestionAnalysisItem)
      : Array.isArray(data.questionStats)
        ? data.questionStats.map(normalizeQuestionAnalysisItem)
        : [],
    student_progress: Array.isArray(data.student_progress)
      ? data.student_progress.map(normalizeStudentProgressItem)
      : Array.isArray(data.studentProgress)
        ? data.studentProgress.map(normalizeStudentProgressItem)
        : [],
    lowest_accuracy_questions: Array.isArray(data.lowest_accuracy_questions)
      ? data.lowest_accuracy_questions.map(normalizeQuestionAnalysisItem)
      : Array.isArray(data.lowestAccuracyQuestions)
        ? data.lowestAccuracyQuestions.map(normalizeQuestionAnalysisItem)
        : [],
  };
}

export async function getTeachingSummary(taskId, filters = {}) {
  const params = new URLSearchParams();
  const grade = String(filters.grade || "").trim();
  const className = normalizeClassName(filters.class_name || filters.className);

  if (grade) {
    params.set("grade", grade);
  }
  if (className) {
    params.set("class_name", className);
  }

  const query = params.toString();
  const url = query
    ? `${TASKS_URL}/${taskId}/teaching-summary?${query}`
    : `${TASKS_URL}/${taskId}/teaching-summary`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to load teaching summary"));
  }

  return response.json();
}

export async function submitSingleQuestion(taskId, questionPk, payload) {
  const response = await fetch(
    `${TASKS_URL}/${taskId}/questions/${encodeURIComponent(questionPk)}/submit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to submit current question"));
  }

  return response.json();
}

export async function submitAnswers(taskId, payload) {
  const response = await fetch(`${TASKS_URL}/${taskId}/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await getErrorDetail(response, "Failed to submit answers"));
  }

  return response.json();
}
