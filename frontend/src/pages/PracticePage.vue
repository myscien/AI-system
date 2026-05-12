<template>
  <div class="page practice-page">
    <h1>
      <RouterLink class="app-title-link" :to="{ name: 'home' }">学生端｜课堂巩固练习</RouterLink>
    </h1>

    <div v-if="loadingQuestions" class="card">
      <p class="hint">正在加载题目...</p>
    </div>

    <div v-else-if="routeError" class="card">
      <p class="error">{{ routeError }}</p>
      <div class="result-btn-row">
        <button class="secondary-btn" @click="goHome">返回首页</button>
      </div>
    </div>

    <div v-else-if="result" class="card">
      <h2>提交完成</h2>
      <p><strong>总分：</strong>{{ result.total_score }}</p>
      <p v-if="studentProfile?.student_name"><strong>姓名：</strong>{{ studentProfile.student_name }}</p>
      <p><strong>学号：</strong>{{ result.student_no }}</p>

      <div v-for="item in result.results" :key="item.question_pk" class="result-item">
        <h3>{{ item.question_pk }}</h3>
        <p><strong>是否正确：</strong>{{ item.is_correct ? "是" : "否" }}</p>
        <p><strong>第一次答案：</strong>{{ formatAnswer(item.student_answer) }}</p>
        <p><strong>正确答案：</strong>{{ formatAnswer(item.correct_answer) }}</p>
        <p v-if="item.selected_option_explanation">
          <strong>选项反馈：</strong>{{ item.selected_option_explanation }}
        </p>
        <p><strong>题目解析：</strong>{{ item.student_explanation }}</p>
      </div>

      <div class="result-btn-row">
        <button class="primary-btn" @click="restartTask">重新开始</button>
        <button class="secondary-btn" @click="goHome">返回首页</button>
      </div>
    </div>

    <div v-else-if="showSummaryPage && allQuestionsCompleted" class="card practice-summary-page">
      <h2 class="practice-summary-title">本次练习总结</h2>
      <p class="practice-summary-subtitle">
        全部 {{ practiceSummary.totalQuestions }} 题已完成，可以回顾本次掌握情况。
      </p>

      <div class="practice-summary-mastery">
        <div>
          <span class="summary-label">掌握度</span>
          <strong>{{ formatPercent(practiceSummary.firstTryAccuracy) }}</strong>
        </div>
        <div class="star-rating" :aria-label="`首次掌握度 ${practiceSummary.starScore} 星`">
          <span
            v-for="(star, index) in practiceSummaryStars"
            :key="index"
            class="star-icon"
            :class="`star-icon-${star}`"
          >
            {{ getStarSymbol(star) }}
          </span>
        </div>
      </div>

      <div class="practice-summary-grid">
        <div class="summary-card summary-card-emphasis">
          <span class="summary-label">完成题数</span>
          <strong>{{ practiceSummary.completedQuestions }} / {{ practiceSummary.totalQuestions }}</strong>
        </div>
        <div class="summary-card summary-card-emphasis">
          <span class="summary-label">首次答对</span>
          <strong>{{ practiceSummary.firstTryCorrectCount }} 题</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">订正后掌握</span>
          <strong>{{ practiceSummary.correctedCount }} 题</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">查看答案</span>
          <strong>{{ practiceSummary.answerViewedCount }} 题</strong>
        </div>
      </div>

      <div class="practice-summary-section practice-summary-highlight">
        <h3 class="practice-summary-section-title">{{ practiceSummary.encouragementTitle }}</h3>
        <p class="practice-summary-text">{{ practiceSummary.suggestion }}</p>
      </div>

      <div class="practice-summary-section">
        <h3 class="practice-summary-section-title">不熟悉的知识点</h3>
        <div v-if="practiceSummary.weakKnowledgePoints.length > 0" class="knowledge-point-list">
          <span
            v-for="item in practiceSummary.weakKnowledgePoints"
            :key="item.name"
            class="knowledge-point-tag"
          >
            {{ item.name }}
            <span v-if="item.count > 1"> x{{ item.count }}</span>
          </span>
        </div>
        <p v-else class="empty-inline">本次练习中暂未识别出明显不熟悉的知识点。</p>
      </div>

      <div class="practice-summary-section">
        <h3 class="practice-summary-section-title">下一轮目标</h3>
        <p class="practice-summary-text practice-summary-goal">{{ practiceSummary.challengeGoal }}</p>
      </div>

      <div class="result-btn-row">
        <button class="secondary-btn" @click="backToLastQuestion">返回最后一题</button>
        <button class="primary-btn restart-highlight-btn" @click="restartTask">重新开始</button>
        <button class="secondary-btn" @click="goHome">返回首页</button>
      </div>
    </div>

    <div v-else-if="currentQuestion" class="card practice-card">
      <div v-if="studentProfile" class="practice-student-bar">
        <div class="practice-student-name">
          {{ studentProfile.student_name || studentProfile.student_no }}
          <span v-if="studentProfile.student_no"> · {{ studentProfile.student_no }}</span>
        </div>
        <div class="practice-student-meta">
          <span v-if="studentProfile.grade">{{ formatGrade(studentProfile.grade) }}</span>
          <span v-if="studentProfile.class_name">{{ formatClassName(studentProfile.class_name) }}</span>
          <span v-if="studentProfile.status">{{ getStudentStatusLabel(studentProfile.status) }}</span>
        </div>
      </div>

      <div class="top-bar">
        <div class="practice-progress-text">
          第 {{ currentIndex + 1 }} / {{ questions.length }} 题
        </div>

        <div class="status-bar" aria-label="答题进度">
          <span
            v-for="(q, idx) in questions"
            :key="q.question_pk"
            class="status-dot"
            :class="getQuestionStatusClass(q.question_pk, idx)"
          >
            {{ idx + 1 }}
          </span>
        </div>
      </div>

      <div class="question-block">
        <div class="question-heading-row">
          <span class="question-type-badge">{{ getQuestionTypeLabel(currentQuestion.question_type) }}</span>
        </div>
        <h2>{{ currentQuestion.stem }}</h2>

        <div
          v-if="
            currentQuestion.question_type === 'judgment' ||
            currentQuestion.question_type === 'single_choice'
          "
        >
          <p class="hint">请选择后点击“提交本题”。</p>

          <label
            v-for="(option, optionIndex) in currentQuestion.options"
            :key="option.id"
            class="option"
            :class="getOptionClass(option.id)"
          >
            <input
              type="radio"
              :name="String(currentQuestion.question_pk)"
              :value="option.id"
              :checked="getSingleChoiceValue() === option.id"
              :disabled="currentState.completed"
              @change="handleSingleChoice(option.id)"
            />
            <div class="option-content">
              <div>{{ getDisplayOptionId(optionIndex) }}. {{ option.text }}</div>

              <div
                v-if="
                  shouldShowOptionExplanation(option.id) &&
                  !shouldShowCorrectAnswerUnderOption(option.id)
                "
                class="option-explanation option-explanation-wrong"
              >
                {{ getOptionExplanation(option.id) }}
              </div>

              <div
                v-if="shouldShowCorrectAnswerUnderOption(option.id)"
                class="option-explanation option-explanation-correct"
              >
                正确答案：{{ getOptionExplanation(option.id) }}
              </div>
            </div>
          </label>
        </div>

        <div v-else-if="currentQuestion.question_type === 'multiple_choice'">
          <p class="hint">请选择后点击“提交本题”。</p>

          <label
            v-for="(option, optionIndex) in currentQuestion.options"
            :key="option.id"
            class="option"
            :class="getOptionClass(option.id)"
          >
            <input
              type="checkbox"
              :value="option.id"
              :checked="getMultipleChoiceValues().includes(option.id)"
              :disabled="currentState.completed"
              @change="handleMultipleChoice(option.id, $event)"
            />
            <div class="option-content">
              <div>{{ getDisplayOptionId(optionIndex) }}. {{ option.text }}</div>

              <div
                v-if="
                  shouldShowOptionExplanation(option.id) &&
                  !shouldShowCorrectAnswerUnderOption(option.id)
                "
                class="option-explanation option-explanation-wrong"
              >
                {{ getOptionExplanation(option.id) }}
              </div>

              <div
                v-if="shouldShowCorrectAnswerUnderOption(option.id)"
                class="option-explanation option-explanation-correct"
              >
                正确答案：{{ getOptionExplanation(option.id) }}
              </div>
            </div>
          </label>
        </div>

        <div v-else-if="currentQuestion.question_type === 'blank'">
          <p class="hint">请输入答案后点击“提交本题”。</p>

          <input
            v-model="blankInput"
            class="blank-input"
            :disabled="currentState.completed"
            placeholder="请输入答案"
          />

          <div v-if="shouldShowBlankAnswerBlock" class="blank-answer-card">
            <p>
              <strong>正确答案：</strong>{{ formatAnswer(getQuestionCorrectAnswers(currentQuestion)) }}
            </p>
            <p>
              <strong>可接受答案：</strong>{{ formatAnswer(getQuestionAcceptedAnswers(currentQuestion)) }}
            </p>
          </div>
        </div>
      </div>

      <div
        v-if="
          currentEncouragementCard ||
          shouldShowExplanationBlock ||
          (!currentState.completed &&
            currentState.submitCount === 1 &&
            !currentState.currentIsCorrect) ||
          (!currentState.completed &&
            currentState.submitCount >= 2 &&
            !currentState.currentIsCorrect &&
            !currentState.answerVisible) ||
          currentQuestionSaving
        "
        ref="feedbackSectionRef"
        class="feedback-stack"
      >
        <div
          v-if="currentEncouragementCard"
          class="encouragement-card"
          :class="`encouragement-card-${currentEncouragementCard.tone}`"
        >
          <div class="encouragement-icon" aria-hidden="true">
            {{ currentEncouragementCard.icon }}
          </div>
          <div class="encouragement-body">
            <p class="encouragement-title">{{ currentEncouragementCard.title }}</p>
            <p class="encouragement-text">{{ currentEncouragementCard.body }}</p>
          </div>
        </div>

        <div v-if="shouldShowExplanationBlock" class="explanation-card">
          <p class="explanation-title">{{ explanationBlockTitle }}</p>

          <p v-if="showExplanationHintOnly" class="explanation-hint">
            {{ explanationHintText }}
          </p>

          <details v-else-if="shouldShowCollapsedExplanation" class="explanation-details">
            <summary>查看本题解析</summary>
            <p class="explanation-text">
              {{ currentState.studentExplanation }}
            </p>
          </details>

          <p v-else-if="shouldShowFullExplanation" class="explanation-text">
            {{ currentState.studentExplanation }}
          </p>
        </div>

        <p
          v-if="
            !currentState.completed &&
            currentState.submitCount === 1 &&
            !currentState.currentIsCorrect
          "
          class="action-hint"
        >
          你还可以再尝试一次。
        </p>

        <p
          v-if="
            !currentState.completed &&
            currentState.submitCount >= 2 &&
            !currentState.currentIsCorrect &&
            !currentState.answerVisible
          "
          class="action-hint"
        >
          你已尝试两次，可以点击“查看答案”。
        </p>

        <p v-if="currentQuestionSaving" class="action-hint">本题保存中...</p>
      </div>

      <p v-if="currentQuestionSaveError" class="error">
        {{ currentQuestionSaveError }}
      </p>

      <div class="practice-bottom-bar" role="navigation" aria-label="答题操作">
        <div class="practice-bottom-inner">
          <button class="secondary-btn practice-nav-btn" :disabled="currentIndex === 0" @click="goPrev">
            上一题
          </button>

          <div class="question-action-bar">
            <button
              class="primary-btn"
              :disabled="primaryPracticeActionDisabled"
              @click="handlePrimaryPracticeAction"
            >
              {{ primaryPracticeActionText }}
            </button>
          </div>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getQuestions, submitAnswers, submitSingleQuestion } from "../api/tasks";

const STUDENT_PROFILE_STORAGE_KEY = "studentProfile";

const route = useRoute();
const router = useRouter();

const questions = ref([]);
const currentIndex = ref(0);
const result = ref(null);
const error = ref("");
const routeError = ref("");
const loadingQuestions = ref(false);
const blankInput = ref("");
const sessionId = ref("");
const showSummaryPage = ref(false);

const questionStates = ref({});
const submittedQuestionMap = ref({});
const savingQuestionMap = ref({});
const saveErrorMap = ref({});
const feedbackSectionRef = ref(null);

const taskId = computed(() => String(route.params.taskId || ""));
const studentNo = computed(() => {
  const queryValue = String(route.query.student_no || "").trim();
  if (queryValue) return queryValue;
  return localStorage.getItem("studentNo") || "";
});
const studentProfile = computed(() => {
  const profile = readStoredStudentProfile();
  if (!profile) return null;
  return String(profile.student_no || "").trim() === studentNo.value ? profile : null;
});

const currentQuestion = computed(() => questions.value[currentIndex.value] || null);

const currentState = computed(() => {
  if (!currentQuestion.value) return {};
  return questionStates.value[currentQuestion.value.question_pk] || {};
});

const completedCount = computed(() => {
  return Object.values(questionStates.value).filter((state) => state.completed).length;
});

const allQuestionsCompleted = computed(() => {
  return questions.value.length > 0 && completedCount.value === questions.value.length;
});

const currentQuestionSaving = computed(() => {
  const questionPk = currentQuestion.value?.question_pk;
  return questionPk ? Boolean(savingQuestionMap.value[questionPk]) : false;
});

const currentQuestionSaveError = computed(() => {
  const questionPk = currentQuestion.value?.question_pk;
  return questionPk ? saveErrorMap.value[questionPk] || "" : "";
});

const computedNextButtonText = computed(() => {
  if (isLastQuestion.value && allQuestionsCompleted.value) {
    return "查看总结";
  }

  return "下一题";
});

const primaryPracticeActionText = computed(() => {
  if (!currentState.value.completed && currentState.value.submitCount === 0) {
    return "提交本题";
  }

  if (
    !currentState.value.completed &&
    currentState.value.submitCount === 1 &&
    !currentState.value.currentIsCorrect
  ) {
    return "再次提交";
  }

  if (
    !currentState.value.completed &&
    currentState.value.submitCount >= 2 &&
    !currentState.value.currentIsCorrect &&
    !currentState.value.answerVisible
  ) {
    return "查看答案";
  }

  return computedNextButtonText.value;
});

const primaryPracticeActionDisabled = computed(() => {
  return currentQuestionSaving.value;
});

const practiceSummary = computed(() => {
  const summary = {
    totalQuestions: questions.value.length,
    completedQuestions: completedCount.value,
    firstTryCorrectCount: 0,
    correctedCount: 0,
    answerViewedCount: 0,
    weakKnowledgePoints: [],
    encouragementTitle: "",
    suggestion: "",
    challengeGoal: "",
    firstTryAccuracy: 0,
    starScore: 0,
  };

  const knowledgePointCountMap = new Map();

  for (const question of questions.value) {
    const state = questionStates.value[question.question_pk] || {};
    const knowledgePoint = String(question.knowledge_point || "").trim();
    const shouldMarkWeakPoint =
      Boolean(knowledgePoint) &&
      (state.firstIsCorrect === false || state.answerVisible === true);

    if (state.firstIsCorrect === true) {
      summary.firstTryCorrectCount += 1;
    } else if (state.completed && !state.answerVisible && state.firstIsCorrect === false) {
      summary.correctedCount += 1;
    }

    if (state.answerVisible) {
      summary.answerViewedCount += 1;
    }

    if (shouldMarkWeakPoint) {
      knowledgePointCountMap.set(
        knowledgePoint,
        (knowledgePointCountMap.get(knowledgePoint) || 0) + 1
      );
    }
  }

  summary.weakKnowledgePoints = [...knowledgePointCountMap.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "zh-Hans-CN"));
  summary.firstTryAccuracy =
    summary.totalQuestions > 0 ? summary.firstTryCorrectCount / summary.totalQuestions : 0;
  summary.starScore = Math.round(summary.firstTryAccuracy * 10) / 2;

  if (
    summary.firstTryCorrectCount === summary.totalQuestions &&
    summary.answerViewedCount === 0 &&
    summary.totalQuestions > 0
  ) {
    summary.encouragementTitle = "这次完成得很稳，你真棒！";
    summary.suggestion =
      "这组题你已经掌握得比较扎实了，再重新开始过一遍，继续保持全对状态。";
    summary.challengeGoal = "不看答案，只靠思考，再完成一遍全对！";
  } else if (summary.answerViewedCount > 0 || summary.weakKnowledgePoints.length >= 2) {
    summary.encouragementTitle = "这次把遗憾找出来了";
    summary.suggestion =
      "先把总结里的知识点回顾清楚，再重新做一遍，把这次卡住的地方一题一题补齐。";
    summary.challengeGoal = "把这次查看过答案的题目全部独立做对，你可以的，加油！";
  } else {
    summary.encouragementTitle = "已经很接近成功了，加油！";
    summary.suggestion =
      "这次大部分问题都修正过来了，说明你已经会了，只是还不够熟。再做一遍，很有机会直接全对。";
    summary.challengeGoal = "把这次首次答错的题目全部一次做对，相信自己可以的！";
  }

  return summary;
});

const practiceSummaryStars = computed(() => {
  const score = practiceSummary.value.starScore;
  return Array.from({ length: 5 }, (_, index) => {
    const value = index + 1;
    if (score >= value) return "full";
    if (score >= value - 0.5) return "half";
    return "empty";
  });
});

const isLastQuestion = computed(() => {
  return questions.value.length > 0 && currentIndex.value === questions.value.length - 1;
});

const defaultEncouragement = {
  correct: "本题掌握得不错，继续保持。",
  wrong: "先看清题意和选项，再试一次。",
  retryCorrect: "调整得很及时，这次答对了。",
  retryWrong: "已经更接近了，结合解析再梳理一遍。",
};

const encouragementPresentationMap = {
  correct: {
    icon: "🎉",
    title: "答对了！",
    tone: "correct",
  },
  wrong: {
    icon: "💡",
    title: "再想一想",
    tone: "wrong",
  },
  retryCorrect: {
    icon: "👏",
    title: "很好，修正成功！",
    tone: "retry-correct",
  },
  retryWrong: {
    icon: "🌱",
    title: "继续巩固",
    tone: "retry-wrong",
  },
};

const currentEncouragement = computed(() => {
  const state = currentState.value;
  const question = currentQuestion.value;

  if (!question || !state?.submitCount) return "";

  const encouragementType = getEncouragementType(state);
  const questionEncouragement = question.encouragement;

  if (typeof questionEncouragement === "string" && questionEncouragement.trim()) {
    return questionEncouragement.trim();
  }

  if (
    questionEncouragement &&
    typeof questionEncouragement === "object" &&
    typeof questionEncouragement[encouragementType] === "string" &&
    questionEncouragement[encouragementType].trim()
  ) {
    return questionEncouragement[encouragementType].trim();
  }

  return defaultEncouragement[encouragementType];
});

const currentEncouragementCard = computed(() => {
  const state = currentState.value;
  if (!state?.submitCount) return null;

  const encouragementType = getEncouragementType(state);
  const presentation = encouragementPresentationMap[encouragementType];

  return {
    ...presentation,
    body: currentEncouragement.value,
  };
});

const shouldShowFullExplanation = computed(() => {
  const state = currentState.value;
  if (!state?.studentExplanation) return false;

  return Boolean(state.answerVisible || (state.currentIsCorrect && state.submitCount >= 2));
});

const shouldShowCollapsedExplanation = computed(() => {
  const state = currentState.value;
  if (!state?.studentExplanation) return false;

  return Boolean(state.currentIsCorrect && state.submitCount === 1);
});

const showExplanationHintOnly = computed(() => {
  const state = currentState.value;
  if (!state?.submitCount) return false;

  return Boolean(!state.currentIsCorrect && !state.answerVisible);
});

const shouldShowExplanationBlock = computed(() => {
  return (
    showExplanationHintOnly.value ||
    shouldShowCollapsedExplanation.value ||
    shouldShowFullExplanation.value
  );
});

const shouldShowBlankAnswerBlock = computed(() => {
  const question = currentQuestion.value;
  const state = currentState.value;

  if (question?.question_type !== "blank") return false;
  return Boolean(state?.answerVisible || state?.currentIsCorrect);
});

const explanationBlockTitle = computed(() => {
  if (showExplanationHintOnly.value) return "本题提示";
  return "本题解析";
});

const explanationHintText = computed(() => {
  const state = currentState.value;
  if (!state?.submitCount) return "";

  return state.submitCount === 1
    ? "先根据选项反馈和题目条件再试一次，完成后可查看完整解析。"
    : "你可以先自己回顾题意，再点击“查看答案”获取完整解析。";
});

function getStorageKey(currentTaskId, currentStudentNo) {
  return `quiz_state_${currentTaskId}_${currentStudentNo}`;
}

function persistQuizState() {
  if (!taskId.value || !studentNo.value || questions.value.length === 0) return;

  const payload = {
    taskId: taskId.value,
    studentNo: studentNo.value,
    currentIndex: currentIndex.value,
    questionStates: questionStates.value,
  };

  localStorage.setItem(getStorageKey(taskId.value, studentNo.value), JSON.stringify(payload));
}

function restoreQuizState(currentTaskId, currentStudentNo) {
  const raw = localStorage.getItem(getStorageKey(currentTaskId, currentStudentNo));
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function clearQuizState() {
  if (!taskId.value || !studentNo.value) return;
  localStorage.removeItem(getStorageKey(taskId.value, studentNo.value));
}

function generateSessionId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function resetRealtimeSubmitState() {
  sessionId.value = generateSessionId();
  submittedQuestionMap.value = {};
  savingQuestionMap.value = {};
  saveErrorMap.value = {};
}

function validateRouteContext() {
  const normalizedTaskId = String(taskId.value || "").trim();
  if (!/^\d+$/.test(normalizedTaskId)) {
    routeError.value = "任务 ID 无效。";
    return null;
  }

  const normalizedStudentNo = String(studentNo.value || "").trim();
  if (!/^\d{8}$/.test(normalizedStudentNo)) {
    routeError.value = "student_no 缺失或格式不正确。";
    return null;
  }

  routeError.value = "";
  localStorage.setItem("studentNo", normalizedStudentNo);

  return {
    taskId: normalizedTaskId,
    studentNo: normalizedStudentNo,
  };
}

function createInitialState() {
  return {
    selectedAnswer: [],
    firstSubmittedAnswer: [],
    firstWrongAnswer: [],
    submitCount: 0,
    firstResultRecorded: false,
    firstIsCorrect: null,
    currentIsCorrect: null,
    feedbackAnswer: [],
    feedbackOptionExplanation: "",
    studentExplanation: "",
    answerVisible: false,
    completed: false,
  };
}

function createQuestionStateMap(questionList, restoredStates = {}) {
  const states = {};

  for (const question of questionList) {
    const restoredState = restoredStates[question.question_pk] || {};
    const initialState = createInitialState();
    states[question.question_pk] = {
      ...initialState,
      ...restoredState,
      selectedAnswer: Array.isArray(restoredState.selectedAnswer)
        ? [...restoredState.selectedAnswer]
        : [...initialState.selectedAnswer],
      firstSubmittedAnswer: Array.isArray(restoredState.firstSubmittedAnswer)
        ? [...restoredState.firstSubmittedAnswer]
        : [...initialState.firstSubmittedAnswer],
      firstWrongAnswer: Array.isArray(restoredState.firstWrongAnswer)
        ? [...restoredState.firstWrongAnswer]
        : [...initialState.firstWrongAnswer],
      feedbackAnswer: Array.isArray(restoredState.feedbackAnswer)
        ? [...restoredState.feedbackAnswer]
        : [...initialState.feedbackAnswer],
    };
  }

  return states;
}

function getEncouragementType(state) {
  const isRetry = Number(state.submitCount || 0) >= 2;

  if (state.currentIsCorrect) {
    return isRetry ? "retryCorrect" : "correct";
  }

  return isRetry ? "retryWrong" : "wrong";
}

async function loadPractice() {
  const context = validateRouteContext();
  questions.value = [];
  result.value = null;
  showSummaryPage.value = false;
  currentIndex.value = 0;
  blankInput.value = "";
  error.value = "";

  if (!context) {
    questionStates.value = {};
    return;
  }

  loadingQuestions.value = true;
  resetRealtimeSubmitState();

  try {
    const data = await getQuestions(context.taskId);
    const shuffledQuestions = data.map(shuffleQuestionOptions);
    questions.value = shuffledQuestions;

    const restored = restoreQuizState(context.taskId, context.studentNo);
    questionStates.value = createQuestionStateMap(shuffledQuestions, restored?.questionStates || {});
    currentIndex.value = restored?.currentIndex || 0;
    syncBlankInput();
  } catch (err) {
    routeError.value = getStudentFacingError(err, "获取题目失败，请稍后重试。");
    questionStates.value = {};
  } finally {
    loadingQuestions.value = false;
  }
}

watch(
  [questionStates, currentIndex],
  () => {
    persistQuizState();
  },
  { deep: true }
);

watch(
  () => [route.params.taskId, route.query.student_no],
  () => {
    void loadPractice();
  },
  { immediate: true }
);

watch(
  () => allQuestionsCompleted.value,
  (completed) => {
    if (!completed) {
      showSummaryPage.value = false;
    }
  }
);

function arraysEqual(a, b) {
  if (a.length !== b.length) return false;
  const sortedA = [...a].sort();
  const sortedB = [...b].sort();
  return sortedA.every((val, idx) => val === sortedB[idx]);
}

function shuffleQuestionOptions(question) {
  if (!Array.isArray(question?.options) || question.options.length <= 1) {
    return question;
  }

  return {
    ...question,
    options: shuffleArray(question.options),
  };
}

function shuffleArray(items) {
  const result = [...items];

  for (let index = result.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [result[index], result[randomIndex]] = [result[randomIndex], result[index]];
  }

  return result;
}

function getSingleChoiceValue() {
  return currentState.value?.selectedAnswer?.[0] || "";
}

function getMultipleChoiceValues() {
  return currentState.value?.selectedAnswer || [];
}

function handleSingleChoice(optionId) {
  if (currentState.value.completed) return;
  currentState.value.selectedAnswer = [optionId];
}

function handleMultipleChoice(optionId, event) {
  if (currentState.value.completed) return;

  const checked = event.target.checked;
  const current = new Set(currentState.value.selectedAnswer);

  if (checked) current.add(optionId);
  else current.delete(optionId);

  currentState.value.selectedAnswer = [...current];
}

function syncBlankInput() {
  if (!currentQuestion.value) return;
  if (currentQuestion.value.question_type === "blank") {
    blankInput.value = currentState.value.selectedAnswer?.[0] || "";
  } else {
    blankInput.value = "";
  }
}

function findOptionExplanation(question, selectedId) {
  const option = question.options.find((opt) => opt.id === selectedId);
  return option ? option.explanation : "";
}

function findMultipleOptionExplanation(question, selectedIds) {
  const parts = [];
  for (const id of selectedIds) {
    const option = question.options.find((opt) => opt.id === id);
    if (option) {
      parts.push(`${option.id}: ${option.explanation}`);
    }
  }
  return parts.join(" ");
}

function evaluateCurrentAnswer() {
  const question = currentQuestion.value;
  const state = currentState.value;

  let selectedAnswer = [];

  if (question.question_type === "blank") {
    const value = blankInput.value.trim();
    selectedAnswer = value ? [value] : [];
    state.selectedAnswer = selectedAnswer;
  } else {
    selectedAnswer = state.selectedAnswer || [];
  }

  if (selectedAnswer.length === 0) {
    error.value = "请先完成本题作答。";
    return null;
  }

  let isCorrect = false;
  let optionExplanation = "";

  if (question.question_type === "judgment" || question.question_type === "single_choice") {
    isCorrect = arraysEqual(selectedAnswer, getQuestionCorrectAnswers(question));
    optionExplanation = findOptionExplanation(question, selectedAnswer[0]);
  } else if (question.question_type === "multiple_choice") {
    isCorrect = arraysEqual(selectedAnswer, getQuestionCorrectAnswers(question));
    optionExplanation = findMultipleOptionExplanation(question, selectedAnswer);
  } else if (question.question_type === "blank") {
    const accepted = getQuestionAcceptedAnswers(question).map((item) => item.trim());
    const value = selectedAnswer[0]?.trim() || "";
    isCorrect = accepted.includes(value);
  }

  return {
    selectedAnswer,
    isCorrect,
    optionExplanation,
  };
}

async function saveQuestionResult(questionId, selectedAnswer) {
  if (!taskId.value || !questionId) return;
  if (submittedQuestionMap.value[questionId]) return;
  if (savingQuestionMap.value[questionId]) return;

  const resolvedStudentNo = String(studentNo.value || "").trim() || "20280101";

  saveErrorMap.value = {
    ...saveErrorMap.value,
    [questionId]: "",
  };
  savingQuestionMap.value = {
    ...savingQuestionMap.value,
    [questionId]: true,
  };

  try {
    await submitSingleQuestion(taskId.value, questionId, {
      student_name: getResolvedStudentName(),
      student_no: resolvedStudentNo,
      student_answer: [...selectedAnswer],
      session_id: sessionId.value,
    });

    submittedQuestionMap.value = {
      ...submittedQuestionMap.value,
      [questionId]: true,
    };
  } catch (err) {
    saveErrorMap.value = {
      ...saveErrorMap.value,
      [questionId]: getStudentFacingError(err, "本题保存失败，请稍后重试。"),
    };
  } finally {
    savingQuestionMap.value = {
      ...savingQuestionMap.value,
      [questionId]: false,
    };
  }
}

async function submitCurrentQuestion() {
  error.value = "";

  const questionPk = currentQuestion.value?.question_pk;
  const state = currentState.value;
  const evaluated = evaluateCurrentAnswer();
  if (!evaluated) return;

  state.submitCount += 1;
  state.currentIsCorrect = evaluated.isCorrect;
  state.studentExplanation = currentQuestion.value.student_explanation;
  state.feedbackAnswer = [...evaluated.selectedAnswer];
  state.feedbackOptionExplanation = evaluated.optionExplanation;

  if (!state.firstResultRecorded) {
    state.firstResultRecorded = true;
    state.firstIsCorrect = evaluated.isCorrect;
    state.firstSubmittedAnswer = [...evaluated.selectedAnswer];
  }

  if (state.submitCount === 1 && !evaluated.isCorrect) {
    state.firstWrongAnswer = [...evaluated.selectedAnswer];
    state.selectedAnswer = [];

    if (currentQuestion.value.question_type === "blank") {
      blankInput.value = "";
    }
  }

  state.completed = evaluated.isCorrect;
  persistQuizState();

  await scrollToFeedbackIfNeeded();
  await saveQuestionResult(questionPk, evaluated.selectedAnswer);
}

async function showAnswer() {
  currentState.value.answerVisible = true;
  currentState.value.completed = true;
  persistQuizState();
  await scrollToFeedbackIfNeeded();
}

async function handlePrimaryPracticeAction() {
  if (!currentState.value.completed && currentState.value.submitCount === 0) {
    await submitCurrentQuestion();
    return;
  }

  if (
    !currentState.value.completed &&
    currentState.value.submitCount === 1 &&
    !currentState.value.currentIsCorrect
  ) {
    await submitCurrentQuestion();
    return;
  }

  if (
    !currentState.value.completed &&
    currentState.value.submitCount >= 2 &&
    !currentState.value.currentIsCorrect &&
    !currentState.value.answerVisible
  ) {
    await showAnswer();
    return;
  }

  goNext();
}

function shouldShowOptionExplanation(optionId) {
  const question = currentQuestion.value;
  const state = currentState.value;

  if (!state.submitCount) return false;
  if (question.question_type === "blank") return false;

  const feedbackAnswer = state.feedbackAnswer || [];
  const isFeedbackSelected = feedbackAnswer.includes(optionId);
  const firstWrongAnswer = state.firstWrongAnswer || [];
  const isCurrentSelected = (state.selectedAnswer || []).includes(optionId);

  if (state.answerVisible) {
    return isFeedbackSelected || getQuestionCorrectAnswers(question).includes(optionId);
  }

  if (state.submitCount === 1 && !state.currentIsCorrect) {
    return firstWrongAnswer.includes(optionId) && !isCurrentSelected;
  }

  return isFeedbackSelected;
}

function shouldShowCorrectAnswerUnderOption(optionId) {
  const question = currentQuestion.value;
  const state = currentState.value;

  if (!state.answerVisible) return false;
  if (question.question_type === "blank") return false;

  return getQuestionCorrectAnswers(question).includes(optionId);
}

function getOptionExplanation(optionId) {
  const option = currentQuestion.value.options.find((opt) => opt.id === optionId);
  return option ? option.explanation : "";
}

function getQuestionStatusClass(questionId, idx) {
  if (idx === currentIndex.value) return "status-current";
  if (questionStates.value[questionId]?.completed) return "status-done";
  return "status-pending";
}

function getOptionClass(optionId) {
  const question = currentQuestion.value;
  const state = currentState.value;
  const classNames = [];
  const selectedAnswer = state.selectedAnswer || [];
  const isCurrentSelected = selectedAnswer.includes(optionId);

  if (isCurrentSelected && !state.completed) {
    classNames.push("option-selected");
  }

  if (!state.submitCount) return classNames.join(" ");

  const feedbackAnswer = state.feedbackAnswer || [];
  const firstWrongAnswer = state.firstWrongAnswer || [];
  const isFeedbackSelected = feedbackAnswer.includes(optionId);
  const isCorrectOption = getQuestionCorrectAnswers(question).includes(optionId);

  if (state.answerVisible) {
    if (isCorrectOption) classNames.push("option-correct");
    else if (isFeedbackSelected) classNames.push("option-wrong");
    return classNames.join(" ");
  }

  if (state.submitCount === 1 && !state.currentIsCorrect) {
    if (!isCurrentSelected && firstWrongAnswer.includes(optionId)) {
      classNames.push("option-wrong");
    }
    return classNames.join(" ");
  }

  if (state.currentIsCorrect && isFeedbackSelected) {
    classNames.push("option-correct");
    return classNames.join(" ");
  }

  if (!state.currentIsCorrect && isFeedbackSelected) {
    classNames.push("option-wrong");
  }

  return classNames.join(" ");
}

function goPrev() {
  if (currentIndex.value > 0) {
    currentIndex.value -= 1;
    syncBlankInput();
  }
}

function goNext() {
  if (!currentState.value.completed) {
    error.value = "请先完成本题。";
    return;
  }

  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value += 1;
  } else if (allQuestionsCompleted.value) {
    showSummaryPage.value = true;
  } else {
    currentIndex.value = 0;
  }

  syncBlankInput();
  error.value = "";
}

function backToLastQuestion() {
  showSummaryPage.value = false;
  currentIndex.value = Math.max(questions.value.length - 1, 0);
  syncBlankInput();
  error.value = "";
}

async function scrollToFeedbackIfNeeded() {
  await nextTick();

  const feedbackEl = feedbackSectionRef.value;
  if (!feedbackEl) return;

  const rect = feedbackEl.getBoundingClientRect();
  const bottomSafeArea = 120;
  const isMostlyVisible = rect.top >= 80 && rect.bottom <= window.innerHeight - bottomSafeArea;
  if (isMostlyVisible) return;

  feedbackEl.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
}

async function submitQuiz() {
  error.value = "";

  const unfinished = questions.value.filter(
    (question) => !questionStates.value[question.question_pk]?.completed
  );

  if (unfinished.length > 0) {
    const confirmed = window.confirm(
      `还有 ${unfinished.length} 题未完成。未完成的题目会按第一次已提交结果或空答案提交。确定继续吗？`
    );
    if (!confirmed) return;
  }

  try {
    const payload = {
      student_name: getResolvedStudentName(),
      student_no: studentNo.value,
      answers: questions.value.map((question) => {
        const state = questionStates.value[question.question_pk];
        return {
          question_pk: question.question_pk,
          student_answer: state.firstSubmittedAnswer || [],
        };
      }),
    };

    result.value = await submitAnswers(taskId.value, payload);
    clearQuizState();
  } catch (err) {
    error.value = getStudentFacingError(err, "提交失败，请重试。");
  }
}

async function restartTask() {
  clearQuizState();
  result.value = null;
  await loadPractice();
}

function goHome() {
  router.push({ name: "home" });
}

function formatAnswer(answer) {
  if (!answer || answer.length === 0) return "(空)";
  return answer.join(", ");
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }

  return `${Math.round(Number(value) * 100)}%`;
}

function getStarSymbol(star) {
  if (star === "full") return "★";
  if (star === "half") return "◐";
  return "☆";
}

function getDisplayOptionId(index) {
  return String.fromCharCode(65 + index);
}

function getQuestionTypeLabel(type) {
  const typeMap = {
    single_choice: "单选题",
    multiple_choice: "多选题",
    judgment: "判断题",
    blank: "填空题",
  };

  return typeMap[type] || "题目";
}

function getQuestionCorrectAnswers(question) {
  if (Array.isArray(question?.correct_answer)) return question.correct_answer;
  if (Array.isArray(question?.correctAnswer)) return question.correctAnswer;
  return [];
}

function getQuestionAcceptedAnswers(question) {
  if (Array.isArray(question?.accepted_answers) && question.accepted_answers.length > 0) {
    return question.accepted_answers;
  }
  if (Array.isArray(question?.acceptedAnswers) && question.acceptedAnswers.length > 0) {
    return question.acceptedAnswers;
  }
  return getQuestionCorrectAnswers(question);
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

function getResolvedStudentName() {
  const profileName = String(studentProfile.value?.student_name || "").trim();
  if (profileName) return profileName;
  return "测试学生";
}

function getStudentStatusLabel(status) {
  if (status === "active") return "正常";
  if (status === "inactive") return "停用";
  if (status === "graduated") return "已毕业";
  return "未知状态";
}

function getStudentFacingError(err, fallbackMessage) {
  const message = String(err?.message || "").trim();
  if (message === "Student not found") {
    return "未找到该学号对应的学生，请先联系老师导入学生名单。";
  }
  return message || fallbackMessage;
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
</script>
