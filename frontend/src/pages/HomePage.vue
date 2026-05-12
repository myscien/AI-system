<template>
  <div class="page">
    <h1>
      <RouterLink class="app-title-link" :to="{ name: 'home' }">学生端｜课堂巩固练习</RouterLink>
    </h1>

    <div class="home-layout">
      <div class="card">
        <div class="student-entry-header">
          <div>
            <h2>学生入口</h2>
            <p class="hint">
              {{ entryHintText }}
            </p>
          </div>
          <button
            class="teacher-unlock-hotspot"
            title="教师管理"
            aria-label="教师管理"
            @click="toggleTeacherUnlockPanel"
          ></button>
        </div>

        <div v-if="queryLocked" class="query-lock-card">
          <strong>查询已锁定</strong>
          <p>
            已查询学号：{{ queryLockRecord?.student_no || "-" }}
            <span v-if="queryLockRecord?.student_name">（{{ queryLockRecord.student_name }}）</span>
          </p>
          <p>查询时间：{{ formatDateTime(queryLockRecord?.locked_at) }}</p>
        </div>

        <div v-if="teacherUnlockPanelVisible" class="teacher-unlock-panel">
          <div class="teacher-unlock-panel-header">
            <strong>教师临时管理</strong>
            <button class="secondary-btn row-action-btn" @click="toggleTeacherUnlockPanel">收起</button>
          </div>

          <p class="hint">
            当前模式：{{ studentQueryLockEnabled ? "查询后锁定" : "测试不锁定" }}。
            “再次查询”只解除当前锁定，历史记录会保留；“清除记录”会清空本设备的锁定和记录。
          </p>

          <label class="setting-toggle-row">
            <input
              type="checkbox"
              :checked="!studentQueryLockEnabled"
              @change="toggleStudentQueryLock"
            />
            <span>测试模式：允许反复切换学生查询</span>
          </label>

          <div class="query-bar">
            <button class="primary-btn" :disabled="!queryLocked" @click="unlockStudentQuery">再次查询</button>
            <button class="secondary-btn danger-btn" @click="clearQueryRecords">清除记录</button>
          </div>

          <div v-if="queryHistory.length > 0" class="query-history-list">
            <div v-for="item in queryHistory" :key="item.id" class="query-history-item">
              <span>{{ item.student_no }}</span>
              <span>{{ item.student_name || "未命名学生" }}</span>
              <span>{{ formatDateTime(item.locked_at) }}</span>
            </div>
          </div>
          <p v-else class="empty-inline">暂无查询记录</p>
        </div>

        <div class="form-row">
          <label for="student-no">学号</label>
          <input
            id="student-no"
            v-model="studentNo"
            inputmode="numeric"
            maxlength="8"
            placeholder="请输入 8 位学号"
            :disabled="queryLocked"
            @keyup.enter="queryTasks"
          />
        </div>

        <div class="form-row">
          <label for="student-no-confirm">再次输入学号</label>
          <input
            id="student-no-confirm"
            v-model="studentNoConfirm"
            inputmode="numeric"
            maxlength="8"
            placeholder="请再次输入 8 位学号"
            :disabled="queryLocked"
            @keyup.enter="queryTasks"
          />
        </div>

        <div class="query-bar">
          <button class="primary-btn" :disabled="loading || queryLocked" @click="queryTasks">
            {{ loading ? "查询中..." : "查询可做任务" }}
          </button>
        </div>

        <p v-if="loading" class="hint">正在获取可做任务...</p>
        <p v-if="error" class="error">{{ error }}</p>

        <div v-if="searched" class="task-list">
          <div v-if="studentProfile" class="student-profile-card">
            <div class="student-profile-header">
              <h3>当前学生</h3>
              <span
                class="student-status-badge"
                :class="`student-status-${studentProfile.status || 'unknown'}`"
              >
                {{ getStudentStatusLabel(studentProfile.status) }}
              </span>
            </div>
            <div class="student-profile-meta">
              <span>{{ studentProfile.student_name || "未命名学生" }}</span>
              <span>{{ studentProfile.student_no }}</span>
              <span v-if="studentProfile.grade">{{ formatGrade(studentProfile.grade) }}</span>
              <span v-if="studentProfile.class_name">{{ formatClassName(studentProfile.class_name) }}</span>
            </div>
          </div>

          <h3>我的任务</h3>

          <div v-if="publishedTasks.length === 0 && archivedTasks.length === 0" class="empty-state">
            当前学号暂无可做任务。
          </div>

          <section v-if="publishedTasks.length > 0" class="student-task-section">
            <div class="student-task-section-header">
              <h4>已发布</h4>
              <span>{{ publishedTasks.length }} 个任务</span>
            </div>

            <div
              v-for="task in publishedTasks"
              :key="task.id"
              class="task-item task-item-detailed task-item-published"
              role="button"
              tabindex="0"
              @click="goPractice(task.id)"
              @keyup.enter="goPractice(task.id)"
            >
              <div class="task-item-body">
                <div class="task-title-row">
                  <div class="task-title">{{ task.title }}</div>
                  <span class="task-status-pill task-status-published">
                    {{ getTaskPublishStatusLabel(task.status) }}
                  </span>
                </div>
                <div class="task-meta">
                  <span v-if="task.grade">{{ formatGrade(task.grade) }}</span>
                  <span v-if="task.question_count !== undefined">
                    <template v-if="task.grade"> / </template>{{ task.question_count }} 题
                  </span>
                  <span v-if="task.student_task_status">
                    <template v-if="task.grade || task.question_count !== undefined"> / </template>
                    {{ getStudentTaskStatusLabel(task.student_task_status) }}
                  </span>
                </div>

                <div class="task-learning-grid">
                  <div class="task-learning-item">
                    <span class="summary-label">尝试次数</span>
                    <strong>{{ task.attempt_count ?? 0 }}</strong>
                  </div>
                  <div class="task-learning-item">
                    <span class="summary-label">完成进度</span>
                    <strong>{{ formatPercent(task.progress) }}</strong>
                  </div>
                  <div class="task-learning-item">
                    <span class="summary-label">正确率</span>
                    <strong>{{ formatPercent(task.accuracy) }}</strong>
                  </div>
                  <div class="task-learning-item">
                    <span class="summary-label">最近提交</span>
                    <strong>{{ formatDateTime(task.last_submit_at) }}</strong>
                  </div>
                </div>

                <p class="task-learning-inline">
                  已答 {{ task.answered_count ?? 0 }} 题，答对 {{ task.correct_count ?? 0 }} 题
                </p>
              </div>

              <div class="task-actions">
                <button class="secondary-btn" :disabled="loading" @click.stop="goTaskSummary(task.id)">
                  查看详情
                </button>
                <button class="enter-btn" :disabled="loading" @click.stop="goPractice(task.id)">
                  开始答题
                </button>
              </div>
            </div>
          </section>

          <section v-if="archivedTasks.length > 0" class="student-task-section student-task-section-archived">
            <div class="student-task-section-header">
              <h4>已归档</h4>
              <span>{{ archivedTasks.length }} 个任务</span>
            </div>

            <div
              v-for="task in archivedTasks"
              :key="task.id"
              class="task-item task-item-detailed task-item-archived"
            >
              <div class="task-item-body">
                <div class="task-title-row">
                  <div class="task-title">{{ task.title }}</div>
                  <span class="task-status-pill task-status-archived">
                    {{ getTaskPublishStatusLabel(task.status) }}
                  </span>
                </div>
                <div class="task-meta">
                  <span v-if="task.grade">{{ formatGrade(task.grade) }}</span>
                  <span v-if="task.question_count !== undefined">
                    <template v-if="task.grade"> / </template>{{ task.question_count }} 题
                  </span>
                  <span v-if="task.student_task_status">
                    <template v-if="task.grade || task.question_count !== undefined"> / </template>
                    {{ getStudentTaskStatusLabel(task.student_task_status) }}
                  </span>
                </div>

                <p class="task-learning-inline">
                  已答 {{ task.answered_count ?? 0 }} 题，答对 {{ task.correct_count ?? 0 }} 题，
                  正确率 {{ formatPercent(task.accuracy) }}
                </p>
              </div>

              <div class="task-actions">
                <button class="secondary-btn" :disabled="loading" @click.stop="goTaskSummary(task.id)">
                  查看详情
                </button>
                <button class="secondary-btn" disabled>已归档</button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getTasks } from "../api/tasks";
import {
  clearExpiredStudentStorage,
  listenStudentStorageTimeout,
  scheduleStudentStorageTimeout,
} from "../utils/studentStorageTimeout";

const STUDENT_PROFILE_STORAGE_KEY = "studentProfile";
const STUDENT_QUERY_LOCK_STORAGE_KEY = "studentQueryLock";
const STUDENT_QUERY_HISTORY_STORAGE_KEY = "studentQueryHistory";
const STUDENT_QUERY_LOCK_SETTING_STORAGE_KEY = "studentQueryLockEnabled";

clearExpiredStudentStorage();

const router = useRouter();

const tasks = ref([]);
const studentProfile = ref(readStoredStudentProfile());
const loading = ref(false);
const error = ref("");
const queryLockRecord = ref(readQueryLockRecord());
const queryHistory = ref(readQueryHistory());
const teacherUnlockPanelVisible = ref(false);
const studentQueryLockEnabled = ref(readStudentQueryLockEnabled());
const queryLocked = ref(studentQueryLockEnabled.value && Boolean(queryLockRecord.value));
const studentNo = ref(getInitialStudentNo());
const studentNoConfirm = ref(getInitialStudentNo());
const searched = ref(false);
const entryHintText = computed(() => {
  if (queryLocked.value) {
    return "本设备已完成一次查询，请联系老师重新开放查询。";
  }

  if (!studentQueryLockEnabled.value) {
    return "测试模式：可随时切换学号查询。";
  }

  return "请连续输入两遍 8 位学号，查询成功后本设备会锁定查询。";
});
const publishedTasks = computed(() => tasks.value.filter((task) => isPublishedTask(task)));
const archivedTasks = computed(() => tasks.value.filter((task) => isArchivedTask(task)));

function readStudentQueryLockEnabled() {
  const storedValue = localStorage.getItem(STUDENT_QUERY_LOCK_SETTING_STORAGE_KEY);
  if (storedValue === "false") return false;
  return true;
}

function getInitialStudentNo() {
  const lockedStudentNo = String(queryLockRecord.value?.student_no || "").trim();
  if (studentQueryLockEnabled.value && lockedStudentNo) return lockedStudentNo;

  const storedStudentNo = localStorage.getItem("studentNo") || "";
  if (!studentQueryLockEnabled.value) return storedStudentNo || "20280101";

  return "";
}

function validateStudentNo() {
  const value = studentNo.value.trim();
  const confirmValue = studentNoConfirm.value.trim();
  if (!/^\d{8}$/.test(value)) {
    error.value = "请输入 8 位学号。";
    return null;
  }
  if (!/^\d{8}$/.test(confirmValue)) {
    error.value = "请再次输入 8 位学号。";
    return null;
  }
  if (value !== confirmValue) {
    error.value = "两次输入的学号不一致，请重新确认。";
    return null;
  }
  return value;
}

async function queryTasks() {
  error.value = "";

  if (isQueryLocked()) {
    error.value = "本设备已完成一次查询，请联系老师重新开放查询。";
    return;
  }

  const validStudentNo = validateStudentNo();
  if (!validStudentNo) {
    tasks.value = [];
    studentProfile.value = null;
    searched.value = false;
    return;
  }

  loading.value = true;
  localStorage.setItem("studentNo", validStudentNo);

  try {
    const data = await getTasks(validStudentNo);
    tasks.value = data.tasks;
    studentProfile.value = data.student;
    persistStudentProfile(data.student);
    lockStudentQuery(validStudentNo, data.student);
    searched.value = true;
  } catch (err) {
    tasks.value = [];
    studentProfile.value = null;
    searched.value = false;
    error.value = getStudentFacingError(err, "获取任务失败，请稍后重试。");
  } finally {
    loading.value = false;
  }
}

async function loadLockedStudentTasks() {
  if (!queryLocked.value || !queryLockRecord.value?.student_no) return;

  const lockedStudentNo = String(queryLockRecord.value.student_no).trim();
  studentNo.value = lockedStudentNo;
  studentNoConfirm.value = lockedStudentNo;
  error.value = "";
  loading.value = true;

  try {
    const data = await getTasks(lockedStudentNo);
    tasks.value = data.tasks;
    studentProfile.value = data.student;
    persistStudentProfile(data.student);
    searched.value = true;
  } catch (err) {
    tasks.value = [];
    searched.value = false;
    error.value = getStudentFacingError(err, "获取任务失败，请稍后重试。");
  } finally {
    loading.value = false;
  }
}

function lockStudentQuery(validStudentNo, profile) {
  const record = {
    id: `${Date.now()}-${validStudentNo}`,
    student_no: validStudentNo,
    student_name: profile?.student_name || "",
    locked_at: new Date().toISOString(),
  };

  if (studentQueryLockEnabled.value) {
    queryLockRecord.value = record;
    queryLocked.value = true;
    localStorage.setItem(STUDENT_QUERY_LOCK_STORAGE_KEY, JSON.stringify(record));
  }

  queryHistory.value = [record, ...queryHistory.value].slice(0, 20);
  localStorage.setItem(STUDENT_QUERY_HISTORY_STORAGE_KEY, JSON.stringify(queryHistory.value));
  scheduleStudentStorageTimeout();
}

function unlockStudentQuery() {
  queryLocked.value = false;
  queryLockRecord.value = null;
  error.value = "";
  localStorage.removeItem(STUDENT_QUERY_LOCK_STORAGE_KEY);
}

function clearQueryRecords() {
  const confirmed = window.confirm("确定清除本设备的查询锁和查询记录吗？");
  if (!confirmed) return;

  unlockStudentQuery();
  queryHistory.value = [];
  tasks.value = [];
  searched.value = false;
  localStorage.removeItem(STUDENT_QUERY_HISTORY_STORAGE_KEY);
}

function resetStudentEntryAfterStorageTimeout() {
  tasks.value = [];
  studentProfile.value = null;
  queryLockRecord.value = null;
  queryHistory.value = [];
  studentQueryLockEnabled.value = true;
  queryLocked.value = false;
  studentNo.value = "";
  studentNoConfirm.value = "";
  searched.value = false;
  loading.value = false;
  error.value = "本设备已超过 20 分钟未重新查询，已自动清除本地记录。";
}

function toggleStudentQueryLock(event) {
  studentQueryLockEnabled.value = !event.target.checked;
  localStorage.setItem(
    STUDENT_QUERY_LOCK_SETTING_STORAGE_KEY,
    studentQueryLockEnabled.value ? "true" : "false"
  );

  if (!studentQueryLockEnabled.value) {
    unlockStudentQuery();
  } else {
    queryLocked.value = Boolean(queryLockRecord.value);
  }
}

function toggleTeacherUnlockPanel() {
  teacherUnlockPanelVisible.value = !teacherUnlockPanelVisible.value;
}

function readQueryLockRecord() {
  const raw = localStorage.getItem(STUDENT_QUERY_LOCK_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function readQueryHistory() {
  const raw = localStorage.getItem(STUDENT_QUERY_HISTORY_STORAGE_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function goPractice(taskId) {
  const validStudentNo = validateStudentNo();
  if (!validStudentNo) return;

  localStorage.setItem("studentNo", validStudentNo);
  persistStudentProfile(studentProfile.value);
  router.push({
    name: "practice",
    params: { taskId: String(taskId) },
    query: { student_no: validStudentNo },
  });
}

function goTaskSummary(taskId) {
  const validStudentNo = validateStudentNo();
  if (!validStudentNo) return;

  localStorage.setItem("studentNo", validStudentNo);
  persistStudentProfile(studentProfile.value);
  router.push({
    name: "student-task-summary",
    params: { taskId: String(taskId) },
    query: { student_no: validStudentNo },
  });
}

function isQueryLocked() {
  return studentQueryLockEnabled.value && queryLocked.value;
}

function readStoredStudentProfile() {
  const raw = localStorage.getItem(STUDENT_PROFILE_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function persistStudentProfile(profile) {
  if (!profile) {
    localStorage.removeItem(STUDENT_PROFILE_STORAGE_KEY);
    return;
  }

  localStorage.setItem(STUDENT_PROFILE_STORAGE_KEY, JSON.stringify(profile));
}

function getStudentStatusLabel(status) {
  if (status === "active") return "正常";
  if (status === "inactive") return "停用";
  if (status === "graduated") return "已毕业";
  return "未知状态";
}

function getStudentTaskStatusLabel(status) {
  if (status === "completed") return "已完成";
  if (status === "in_progress") return "进行中";
  if (status === "not_started") return "未开始";
  return "未开始";
}

function getTaskPublishStatusLabel(status) {
  if (status === "published" || !status) return "已发布";
  if (status === "archived") return "已归档";
  if (status === "draft") return "草稿";
  return status;
}

function isPublishedTask(task) {
  const status = String(task?.status || "").trim();
  return status === "" || status === "published";
}

function isArchivedTask(task) {
  return String(task?.status || "").trim() === "archived";
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

function formatGrade(value) {
  const normalized = String(value || "").trim();
  if (!normalized) return "-";
  if (/^\d+$/.test(normalized)) return `${normalized}年级`;
  return normalized;
}

function formatClassName(value) {
  const normalized = String(value || "").trim().replace(/班$/, "");
  return normalized ? `${normalized}班` : "-";
}

function getStudentFacingError(err, fallbackMessage) {
  const message = String(err?.message || "").trim();
  if (message === "Student not found") {
    return "未找到该学号对应的学生，请先联系老师导入学生名单。";
  }
  return message || fallbackMessage;
}

let stopStudentStorageTimeoutListener = null;

onMounted(() => {
  stopStudentStorageTimeoutListener = listenStudentStorageTimeout(resetStudentEntryAfterStorageTimeout);
  scheduleStudentStorageTimeout();
  void loadLockedStudentTasks();
});

onUnmounted(() => {
  if (stopStudentStorageTimeoutListener) {
    stopStudentStorageTimeoutListener();
    stopStudentStorageTimeoutListener = null;
  }
});
</script>
