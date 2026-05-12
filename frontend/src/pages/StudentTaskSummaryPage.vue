<template>
  <div class="page">
    <h1>
      <RouterLink class="app-title-link" :to="{ name: 'home' }">学生端｜课堂巩固练习</RouterLink>
    </h1>

    <div class="card">
      <div class="analysis-header">
        <div>
          <h2>学习详情</h2>
          <p class="hint">
            {{ summaryTitle }}
          </p>
        </div>
        <div class="row-actions">
          <button class="secondary-btn row-action-btn" @click="goHome">返回首页</button>
          <button class="primary-btn row-action-btn" @click="goPractice">去答题</button>
        </div>
      </div>

      <p v-if="loading" class="hint">正在加载学习详情...</p>
      <p v-else-if="error" class="error">{{ error }}</p>
      <div v-else-if="!summary" class="empty-state">暂无学习详情</div>
      <div v-else class="analysis-content">
        <div class="analysis-summary-grid">
          <div class="summary-card">
            <span class="summary-label">总尝试次数</span>
            <strong>{{ summary.attempt_count }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">历史最佳正确率</span>
            <strong>{{ formatPercent(summary.best_accuracy) }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">最近一次完成进度</span>
            <strong>{{ formatPercent(summary.latest_attempt?.progress) }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">最近一次正确率</span>
            <strong>{{ formatPercent(summary.latest_attempt?.accuracy) }}</strong>
          </div>
        </div>

        <section class="analysis-section">
          <h3>最近一次练习</h3>
          <div v-if="summary.latest_attempt" class="teacher-panel">
            <div class="task-learning-grid">
              <div class="task-learning-item">
                <span class="summary-label">答题数</span>
                <strong>{{ summary.latest_attempt.answered_count }}</strong>
              </div>
              <div class="task-learning-item">
                <span class="summary-label">答对数</span>
                <strong>{{ summary.latest_attempt.correct_count }}</strong>
              </div>
              <div class="task-learning-item">
                <span class="summary-label">正确率</span>
                <strong>{{ formatPercent(summary.latest_attempt.accuracy) }}</strong>
              </div>
              <div class="task-learning-item">
                <span class="summary-label">提交时间</span>
                <strong>{{ formatDateTime(summary.latest_attempt.submitted_at) }}</strong>
              </div>
            </div>
          </div>
          <div v-else class="empty-inline">暂无最近一次练习数据</div>
        </section>

        <section class="analysis-section">
          <h3>历史尝试记录</h3>
          <div class="table-wrap">
            <table v-if="summary.history.length > 0" class="data-table">
              <thead>
                <tr>
                  <th>第几次</th>
                  <th>答题数</th>
                  <th>答对数</th>
                  <th>完成进度</th>
                  <th>正确率</th>
                  <th>提交时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in summary.history" :key="item.session_id || index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ item.answered_count }}</td>
                  <td>{{ item.correct_count }}</td>
                  <td>{{ formatPercent(item.progress) }}</td>
                  <td>{{ formatPercent(item.accuracy) }}</td>
                  <td>{{ formatDateTime(item.submitted_at) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-inline">暂无历史尝试记录</div>
          </div>
        </section>

        <section class="analysis-section">
          <h3>题目结果</h3>
          <div class="table-wrap">
            <table v-if="summary.question_results.length > 0" class="data-table">
              <thead>
                <tr>
                  <th>题目</th>
                  <th>作答次数</th>
                  <th>第一次</th>
                  <th>最近一次</th>
                  <th>历史最好</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in summary.question_results" :key="item.question_pk">
                  <td>{{ item.question_pk }}</td>
                  <td>{{ item.attempt_count }}</td>
                  <td>{{ formatCorrectState(item.first_is_correct) }}</td>
                  <td>{{ formatCorrectState(item.latest_is_correct) }}</td>
                  <td>{{ formatCorrectState(item.best_is_correct) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-inline">暂无题目结果数据</div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getStudentTaskSummary } from "../api/tasks";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const error = ref("");
const summary = ref(null);

const taskId = computed(() => String(route.params.taskId || "").trim());
const studentNo = computed(() => {
  const queryValue = String(route.query.student_no || "").trim();
  if (queryValue) return queryValue;
  return localStorage.getItem("studentNo") || "";
});

const summaryTitle = computed(() => {
  if (!summary.value) {
    return "查看单个任务的历史练习记录和题目结果";
  }

  return `${summary.value.student_name || summary.value.student_no} · ${summary.value.task_title}`;
});

async function loadSummary() {
  error.value = "";
  summary.value = null;

  if (!/^\d+$/.test(taskId.value)) {
    error.value = "任务 ID 无效。";
    return;
  }

  if (!/^\d{8}$/.test(studentNo.value)) {
    error.value = "学生学号无效，请返回首页重新查询。";
    return;
  }

  loading.value = true;

  try {
    summary.value = await getStudentTaskSummary(taskId.value, studentNo.value);
  } catch (err) {
    const message = String(err?.message || "").trim();
    error.value =
      message === "Student not found"
        ? "未找到该学号对应的学生，请先联系老师导入学生名单。"
        : message || "学习详情加载失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

function goHome() {
  router.push({ name: "home" });
}

function goPractice() {
  router.push({
    name: "practice",
    params: { taskId: taskId.value },
    query: { student_no: studentNo.value },
  });
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }

  return `${Math.round(Number(value) * 100)}%`;
}

function formatDateTime(value) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatCorrectState(value) {
  if (value === true) return "答对";
  if (value === false) return "答错";
  return "-";
}

watch(
  () => [route.params.taskId, route.query.student_no],
  () => {
    void loadSummary();
  },
  { immediate: true }
);
</script>
