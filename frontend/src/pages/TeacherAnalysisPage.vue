<template>
  <div class="page">
    <h1>
      <RouterLink class="app-title-link" :to="{ name: 'teacher-tasks' }">教师端｜课堂巩固练习</RouterLink>
    </h1>

    <div class="card">
      <div class="analysis-header">
        <div>
          <h2>教师学情分析</h2>
          <p class="hint">当前任务：{{ analysisTaskTitle }}</p>
        </div>
        <div class="row-actions">
          <button class="secondary-btn row-action-btn" @click="goTeacherTasks">返回任务管理</button>
          <button class="secondary-btn row-action-btn" @click="openStudentApp">打开学生端</button>
        </div>
      </div>

      <div class="analysis-query-bar">
        <div class="form-row analysis-query-field">
          <label for="analysis-task-select">选择任务</label>
          <select
            id="analysis-task-select"
            v-model="analysisTaskIdInput"
            class="form-row-select"
            :disabled="teacherTasksLoading || teacherTasks.length === 0"
          >
            <option value="">
              {{ teacherTasksLoading ? "正在加载任务..." : "请选择任务" }}
            </option>
            <option v-for="task in teacherTasks" :key="task.id" :value="String(task.id)">
              {{ formatTaskOption(task) }}
            </option>
          </select>
          <p v-if="!teacherTasksLoading && teacherTasks.length === 0" class="hint">
            暂无可选任务，请先创建任务。
          </p>
        </div>

        <div class="form-row analysis-filter-field">
          <label for="analysis-grade">年级</label>
          <select id="analysis-grade" v-model="analysisGradeInput" class="form-row-select">
            <option value="">任务默认年级</option>
            <option value="6">6年级</option>
            <option value="7">7年级</option>
            <option value="8">8年级</option>
          </select>
        </div>

        <div class="form-row analysis-filter-field">
          <label for="analysis-class-name">班级</label>
          <select
            id="analysis-class-name"
            v-model="analysisClassNameInput"
            class="form-row-select"
          >
            <option value="">全部班级</option>
            <option value="1">1班</option>
            <option value="2">2班</option>
            <option value="3">3班</option>
            <option value="4">4班</option>
          </select>
        </div>

        <button class="primary-btn analysis-query-submit" :disabled="analysisLoading" @click="goAnalysis">
          {{ analysisLoading ? "查询中..." : "查询分析" }}
        </button>
      </div>

      <p class="hint">不选年级时使用任务默认年级；填写班级时会在当前年级范围内继续筛选。</p>
      <p v-if="teachingSummaryMessage" class="success-text">{{ teachingSummaryMessage }}</p>
      <p v-if="teachingSummaryError" class="error">{{ teachingSummaryError }}</p>

      <p v-if="analysisLoading" class="hint">正在加载学情分析数据...</p>
      <p v-else-if="analysisError" class="error">{{ analysisError }}</p>
      <div v-else-if="!analysisHasData" class="empty-state">暂无作答数据</div>
      <div v-else class="analysis-content">
        <div class="analysis-result-toolbar">
          <div class="analysis-scope">
            当前范围：{{ analysisScopeText }}
          </div>
          <div class="analysis-copy-actions">
            <div class="form-row analysis-copy-field">
              <label for="teaching-summary-template">复制模板</label>
              <select
                id="teaching-summary-template"
                v-model="teachingSummaryTemplateMode"
                class="form-row-select"
              >
                <option value="none">不整合</option>
                <option value="standard">1：标准教学分析</option>
                <option value="research">2：教研级分析</option>
              </select>
            </div>

            <button
              class="secondary-btn"
              :disabled="teachingSummaryLoading || analysisLoading"
              @click="copyTeachingSummary"
            >
              {{ teachingSummaryLoading ? "生成中..." : "复制反馈摘要" }}
            </button>
          </div>
        </div>

        <div class="analysis-summary-grid">
          <div class="summary-card">
            <span class="summary-label">应参与学生数</span>
            <strong>{{ analysisData?.assigned_students ?? 0 }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">已提交学生数</span>
            <strong>{{ analysisData?.submitted_students ?? 0 }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">已完成学生数</span>
            <strong>{{ analysisData?.completed_students ?? 0 }}</strong>
          </div>
          <div class="summary-card summary-card-emphasis">
            <span class="summary-label">完成率</span>
            <strong>{{ formatPercent(analysisData?.completion_rate) }}</strong>
          </div>
          <div class="summary-card summary-card-emphasis">
            <span class="summary-label">班级平均正确率</span>
            <strong>{{ formatPercent(analysisData?.average_accuracy) }}</strong>
          </div>
          <div class="summary-card summary-card-emphasis summary-card-warning">
            <span class="summary-label">低正确率学生数</span>
            <strong>{{ analysisData?.low_accuracy_student_count ?? lowAccuracyStudents.length }}</strong>
          </div>
        </div>

        <div class="teacher-grid analysis-focus-grid">
          <section class="teacher-panel analysis-section">
            <h3>薄弱题目</h3>
            <div v-if="weakQuestions.length > 0" class="weak-list">
              <div v-for="item in weakQuestions" :key="item.question_pk" class="focus-list-item">
                <div class="focus-list-main">
                  <strong>第 {{ item.question_pk }} 题</strong>
                  <span>{{ getQuestionStemPreview(item) }}</span>
                  <div class="focus-list-meta">
                    <span>{{ item.knowledge_point || "未标注知识点" }}</span>
                    <span>作答 {{ item.total_answers ?? 0 }} 次</span>
                    <span>错误 {{ item.wrong_count ?? 0 }} 次</span>
                  </div>
                </div>
                <span>{{ formatPercent(item.accuracy) }}</span>
              </div>
            </div>
            <div v-else class="empty-inline">暂无薄弱题目数据</div>
          </section>

          <section class="teacher-panel analysis-section">
            <h3>需要关注的学生</h3>
            <div class="focus-block">
              <p class="focus-subtitle">低正确率学生</p>
              <div v-if="lowAccuracyStudents.length > 0" class="weak-list">
                <div
                  v-for="item in lowAccuracyStudents"
                  :key="`low-${item.student_no}`"
                  class="focus-list-item"
                >
                  <span>{{ item.student_name || item.student_no }}</span>
                  <span>{{ formatPercent(item.accuracy) }}</span>
                </div>
              </div>
              <div v-else class="empty-inline">暂无低正确率学生</div>
            </div>

          </section>
        </div>

        <section class="analysis-section">
          <h3>学生完成情况表</h3>
          <div class="table-toolbar">
            <div class="form-row table-toolbar-field">
              <label for="student-status-filter">状态筛选</label>
              <select id="student-status-filter" v-model="studentStatusFilter">
                <option value="">全部状态</option>
                <option value="not_started">未开始</option>
                <option value="in_progress">进行中</option>
                <option value="completed">已完成</option>
              </select>
            </div>

            <div class="form-row table-toolbar-field">
              <label for="student-sort-mode">排序方式</label>
              <select id="student-sort-mode" v-model="studentSortMode">
                <option value="status">按状态</option>
                <option value="progress_asc">完成进度低到高</option>
                <option value="progress_desc">完成进度高到低</option>
                <option value="accuracy_asc">正确率低到高</option>
                <option value="student_no">学号升序</option>
              </select>
            </div>
          </div>
          <div class="table-wrap">
            <table v-if="analysisStudentProgress.length > 0" class="data-table">
              <thead>
                <tr>
                  <th>学号</th>
                  <th>姓名</th>
                  <th>年级</th>
                  <th>班级</th>
                  <th>已答题数</th>
                  <th>正确数</th>
                  <th>正确率</th>
                  <th>完成进度</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in displayedStudentProgress" :key="item.student_no">
                  <td>{{ item.student_no }}</td>
                  <td>{{ item.student_name || "-" }}</td>
                  <td>{{ formatGrade(item.grade) }}</td>
                  <td>{{ formatClassName(item.class_name) }}</td>
                  <td>{{ item.answered_count }}</td>
                  <td>{{ item.correct_count }}</td>
                  <td>{{ formatPercent(item.accuracy) }}</td>
                  <td>{{ formatPercent(item.progress) }}</td>
                  <td>
                    <span class="student-progress-status" :class="getStatusClass(item.status)">
                      {{ getStatusLabel(item.status) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div
              v-if="analysisStudentProgress.length > 0 && displayedStudentProgress.length === 0"
              class="empty-inline"
            >
              当前状态筛选下暂无学生
            </div>
            <div v-else-if="analysisStudentProgress.length === 0" class="empty-inline">暂无作答数据</div>
          </div>
        </section>

        <section class="analysis-section">
          <h3>详细题目统计</h3>
          <div v-if="analysisQuestionStats.length > 0" class="question-stat-list">
            <article
              v-for="item in analysisQuestionStats"
              :key="item.question_pk"
              class="question-stat-card"
            >
              <div class="question-stat-header">
                <div class="question-stat-title-block">
                  <div class="question-stat-title">第 {{ item.question_pk }} 题</div>
                  <div class="question-stat-meta">
                    <span>{{ getQuestionTypeLabel(item.question_type) }}</span>
                    <span>{{ getDifficultyLabel(item.difficulty) }}</span>
                    <span>{{ item.knowledge_point || "未标注知识点" }}</span>
                  </div>
                </div>
                <div class="question-stat-score">
                  <span>正确率</span>
                  <strong>{{ formatPercent(item.accuracy) }}</strong>
                </div>
              </div>

              <p class="question-stat-stem">{{ item.stem || "暂无题干" }}</p>

              <div class="question-stat-summary">
                <span>作答 {{ item.total_answers }} 次</span>
                <span>正确 {{ item.correct_count }} 次</span>
                <span>错误 {{ item.wrong_count }} 次</span>
                <span>正确答案：{{ formatAnswerList(item.correct_answer) }}</span>
              </div>

              <div class="option-stat-list">
                <div v-if="item.option_stats.length === 0" class="empty-inline">
                  {{ item.question_type === "blank" ? "填空题暂无选项统计" : "暂无选项统计" }}
                </div>
                <template v-else>
                  <div
                    v-for="option in item.option_stats"
                    :key="`${item.question_pk}-${option.option_id}`"
                    class="option-stat-row"
                  >
                    <div class="option-stat-label">
                      <span
                        class="option-stat-id"
                        :class="{ 'option-stat-id-correct': option.is_correct }"
                      >
                        {{ option.option_id || "-" }}
                      </span>
                      <span class="option-stat-text">{{ option.option_text || "未填写选项内容" }}</span>
                      <span v-if="option.is_correct" class="option-stat-correct">正确选项</span>
                    </div>
                    <div class="option-stat-meter">
                      <div
                        class="option-stat-bar"
                        :class="{ 'option-stat-bar-correct': option.is_correct }"
                        :style="{ width: getOptionStatWidth(option, item) }"
                      ></div>
                    </div>
                    <span class="option-stat-count">{{ option.count }} 次</span>
                  </div>
                </template>
              </div>
            </article>
          </div>
          <div v-else class="empty-inline">暂无题目统计</div>
        </section>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getTaskAnalysis, getTeacherTasks, getTeachingSummary } from "../api/tasks";

const route = useRoute();
const router = useRouter();

const analysisTaskIdInput = ref(String(route.params.taskId || "3"));
const analysisGradeInput = ref(String(route.query.grade || ""));
const analysisClassNameInput = ref(normalizeClassName(route.query.class_name));
const analysisData = ref(null);
const analysisLoading = ref(false);
const analysisError = ref("");
const teacherTasks = ref([]);
const teacherTasksLoading = ref(false);
const teachingSummaryLoading = ref(false);
const teachingSummaryMessage = ref("");
const teachingSummaryError = ref("");
const teachingSummaryTemplateMode = ref("none");
const studentStatusFilter = ref("");
const studentSortMode = ref("status");

const TEACHING_SUMMARY_TEMPLATES = {
  standard: `模板1：标准教学分析 Prompt
你是一名有经验的信息技术教师和教研员。

请基于以下学生作答数据，从“教学改进”的角度进行分析，要求输出：

1. 核心问题诊断（指出最关键的2-3个问题，而不是罗列现象）
2. 学生错误的深层原因（从认知角度分析，而不是重复题目）
3. 针对每个问题给出具体、可操作的教学建议（必须能直接用于课堂）
4. 给出下一节课的教学策略设计（包括：讲解方式、互动形式、练习安排）

要求：
- 避免空泛表述（如“加强练习”）
- 尽量具体到“怎么做”
- 适合小学六年级学生

【数据如下】`,
  research: `模板2：教研级分析

你是一名教育数据分析专家，同时具备一线教学经验。

请对以下课堂练习数据进行“诊断式分析”，输出内容包括：

一、数据有效性评估
- 当前样本量是否足以支撑结论？
- 是否存在误判风险？

二、关键问题识别（按优先级排序）
- 不超过3个核心问题
- 每个问题说明其影响程度

三、错误模式分析
- 学生错误属于哪种类型（概念混淆/审题错误/知识缺失/策略问题等）
- 是否具有共性

四、教学改进建议（分层）
- 全班层面策略
- 低水平学生干预方案
- 高水平学生拓展策略

五、下一步教学行动建议
- 本节课是否需要重讲？讲什么？
- 是否需要调整教学顺序？

要求：
- 语言专业但清晰
- 不重复题目内容
- 强调“为什么错”而不是“错在哪”

【数据如下】`,
};

const analysisQuestionStats = computed(() => {
  return Array.isArray(analysisData.value?.question_stats)
    ? analysisData.value.question_stats
    : [];
});

const analysisStudentProgress = computed(() => {
  return Array.isArray(analysisData.value?.student_progress)
    ? analysisData.value.student_progress
    : [];
});

const weakQuestions = computed(() => {
  const backendItems = Array.isArray(analysisData.value?.lowest_accuracy_questions)
    ? analysisData.value.lowest_accuracy_questions.filter((item) => item?.question_pk)
    : [];

  if (backendItems.length > 0) {
    return backendItems;
  }

  const stats = analysisQuestionStats.value
    .filter((item) => item?.question_pk)
    .slice()
    .sort((a, b) => {
      const accuracyA = typeof a.accuracy === "number" ? a.accuracy : Number.POSITIVE_INFINITY;
      const accuracyB = typeof b.accuracy === "number" ? b.accuracy : Number.POSITIVE_INFINITY;
      if (accuracyA !== accuracyB) return accuracyA - accuracyB;
      return String(a.question_pk).localeCompare(String(b.question_pk));
    });

  return stats.slice(0, 5);
});

const lowAccuracyStudents = computed(() => {
  return analysisStudentProgress.value.filter((item) => item.is_low_accuracy);
});

const displayedStudentProgress = computed(() => {
  return analysisStudentProgress.value
    .filter((item) => {
      if (!studentStatusFilter.value) return true;
      return item.status === studentStatusFilter.value;
    })
    .slice()
    .sort(compareStudentProgress);
});

const analysisHasData = computed(() => {
  if (!analysisData.value) return false;
  return (
    Number(analysisData.value.assigned_students || 0) > 0 ||
    Number(analysisData.value.submitted_students || 0) > 0 ||
    analysisQuestionStats.value.length > 0 ||
    analysisStudentProgress.value.length > 0
  );
});

const analysisTaskTitle = computed(() => {
  const title = analysisData.value?.task_title || analysisData.value?.title || "";
  if (title) {
    return `${title}（ID: ${analysisData.value?.task_id ?? analysisTaskIdInput.value}）`;
  }
  return `任务 ${analysisData.value?.task_id ?? analysisTaskIdInput.value}`;
});

const analysisScopeText = computed(() => {
  const grade = String(analysisData.value?.filter_grade ?? (analysisGradeInput.value || "")).trim();
  const className = normalizeClassName(
    analysisData.value?.filter_class_name ?? (analysisClassNameInput.value || "")
  );
  const parts = [];

  if (grade) {
    parts.push(`${formatGrade(grade)}`);
  } else {
    parts.push("任务默认年级");
  }

  if (className) {
    parts.push(formatClassName(className));
  } else {
    parts.push("全部班级");
  }

  return parts.join(" / ");
});

function normalizeTaskId(value) {
  const normalized = String(value || "").trim();
  if (!/^\d+$/.test(normalized)) {
    return null;
  }
  return normalized;
}

function getAnalysisFilters() {
  return {
    grade: String(analysisGradeInput.value || "").trim(),
    class_name: normalizeClassName(analysisClassNameInput.value),
  };
}

async function fetchTaskAnalysis(taskId) {
  analysisLoading.value = true;
  analysisError.value = "";
  analysisData.value = null;

  try {
    analysisData.value = await getTaskAnalysis(taskId, getAnalysisFilters());
  } catch {
    analysisError.value = "学情分析数据加载失败，请稍后重试";
  } finally {
    analysisLoading.value = false;
  }
}

async function syncFromRoute(taskIdValue) {
  const taskId = normalizeTaskId(taskIdValue) || "3";
  analysisTaskIdInput.value = taskId;
  analysisGradeInput.value = String(route.query.grade || "");
  analysisClassNameInput.value = normalizeClassName(route.query.class_name);
  await fetchTaskAnalysis(taskId);
}

async function loadTeacherTasks() {
  teacherTasksLoading.value = true;

  try {
    teacherTasks.value = await getTeacherTasks();
  } catch {
    teacherTasks.value = [];
  } finally {
    teacherTasksLoading.value = false;
  }
}

async function goAnalysis() {
  const taskId = normalizeTaskId(analysisTaskIdInput.value);
  if (!taskId) {
    analysisError.value = "请输入正确的任务 ID";
    analysisData.value = null;
    return;
  }

  analysisError.value = "";

  const filters = getAnalysisFilters();
  const query = {};
  if (filters.grade) query.grade = filters.grade;
  if (filters.class_name) query.class_name = filters.class_name;

  if (
    String(route.params.taskId) === taskId &&
    String(route.query.grade || "") === filters.grade &&
    normalizeClassName(route.query.class_name) === filters.class_name
  ) {
    await fetchTaskAnalysis(taskId);
    return;
  }

  router.push({
    name: "teacher-analysis",
    params: { taskId },
    query,
  });
}

async function copyTeachingSummary() {
  teachingSummaryMessage.value = "";
  teachingSummaryError.value = "";

  const taskId = normalizeTaskId(analysisTaskIdInput.value);
  if (!taskId) {
    teachingSummaryError.value = "请先选择正确的任务";
    return;
  }

  teachingSummaryLoading.value = true;

  try {
    const data = await getTeachingSummary(taskId, getAnalysisFilters());
    const copyText = String(data?.copy_text || "").trim();
    if (!copyText) {
      teachingSummaryError.value = "暂无可复制的教学摘要";
      return;
    }

    await copyTextToClipboard(buildTeachingSummaryCopyText(copyText));
    teachingSummaryMessage.value =
      teachingSummaryTemplateMode.value === "none"
        ? "教学摘要已复制"
        : "教学摘要已复制，已整合所选模板";
  } catch (error) {
    teachingSummaryError.value = error.message || "教学摘要生成失败，请稍后重试";
  } finally {
    teachingSummaryLoading.value = false;
  }
}

function buildTeachingSummaryCopyText(copyText) {
  const mode = teachingSummaryTemplateMode.value;
  if (mode === "standard") {
    return `${TEACHING_SUMMARY_TEMPLATES.standard}\n\n${copyText}`;
  }

  if (mode === "research") {
    return `${TEACHING_SUMMARY_TEMPLATES.research}\n\n${copyText}`;
  }

  return copyText;
}

async function copyTextToClipboard(text) {
  if (navigator?.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();

  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

function goTeacherTasks() {
  router.push({ name: "teacher-tasks" });
}

function openStudentApp() {
  const route = router.resolve({ name: "home" });
  window.open(route.href, "_blank", "noopener,noreferrer");
}

function formatTaskOption(task) {
  const title = String(task.title || "").trim();
  return title ? `${task.id} - ${title}` : `${task.id}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }

  return `${Math.round(Number(value) * 100)}%`;
}

function formatAnswerList(answer) {
  if (!Array.isArray(answer) || answer.length === 0) {
    return "-";
  }

  return answer.join("、");
}

function getQuestionTypeLabel(type) {
  if (type === "single_choice") return "单选题";
  if (type === "multiple_choice") return "多选题";
  if (type === "judgment") return "判断题";
  if (type === "blank") return "填空题";
  return type || "未知题型";
}

function getDifficultyLabel(difficulty) {
  if (difficulty === "easy") return "简单";
  if (difficulty === "medium") return "中等";
  if (difficulty === "hard") return "困难";
  return difficulty || "未标注难度";
}

function getQuestionStemPreview(item) {
  const stem = String(item.stem || "").trim();
  if (!stem) return "暂无题干";
  return stem.length > 28 ? `${stem.slice(0, 28)}...` : stem;
}

function getOptionStatWidth(option, question) {
  const total = Number(question.total_answers || 0);
  const count = Number(option.count || 0);

  if (total <= 0 || count <= 0) {
    return "0%";
  }

  return `${Math.max(4, Math.round((count / total) * 100))}%`;
}

function getStatusLabel(status) {
  if (status === "completed") return "已完成";
  if (status === "in_progress") return "进行中";
  if (status === "not_started") return "未开始";
  return "-";
}

function getStatusClass(status) {
  if (status === "completed") return "student-progress-status-completed";
  if (status === "in_progress") return "student-progress-status-in-progress";
  if (status === "not_started") return "student-progress-status-not-started";
  return "student-progress-status-unknown";
}

function compareStudentProgress(a, b) {
  if (studentSortMode.value === "progress_asc") {
    return compareNumber(a.progress, b.progress) || compareStudentNo(a, b);
  }

  if (studentSortMode.value === "progress_desc") {
    return compareNumber(b.progress, a.progress) || compareStudentNo(a, b);
  }

  if (studentSortMode.value === "accuracy_asc") {
    return compareNumber(a.accuracy, b.accuracy) || compareStudentNo(a, b);
  }

  if (studentSortMode.value === "student_no") {
    return compareStudentNo(a, b);
  }

  return compareStatus(a.status, b.status) || compareNumber(a.progress, b.progress) || compareStudentNo(a, b);
}

function compareStatus(a, b) {
  const order = {
    not_started: 0,
    in_progress: 1,
    completed: 2,
  };
  return (order[a] ?? 99) - (order[b] ?? 99);
}

function compareNumber(a, b) {
  const valueA = Number.isFinite(Number(a)) ? Number(a) : Number.POSITIVE_INFINITY;
  const valueB = Number.isFinite(Number(b)) ? Number(b) : Number.POSITIVE_INFINITY;
  return valueA - valueB;
}

function compareStudentNo(a, b) {
  return String(a.student_no || "").localeCompare(String(b.student_no || ""));
}

function formatGrade(value) {
  const normalized = String(value || "").trim();
  if (!normalized) return "-";
  if (/^\d+$/.test(normalized)) return `${normalized}年级`;
  return normalized;
}

function normalizeClassName(value) {
  return String(value || "").trim().replace(/班$/, "");
}

function formatClassName(value) {
  const normalized = normalizeClassName(value);
  return normalized ? `${normalized}班` : "-";
}

watch(
  () => [route.params.taskId, route.query.grade, route.query.class_name],
  ([taskId]) => {
    void syncFromRoute(taskId);
  },
  { immediate: true }
);

onMounted(() => {
  void loadTeacherTasks();
});
</script>
