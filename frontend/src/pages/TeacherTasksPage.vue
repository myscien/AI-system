<template>
  <div class="page teacher-admin-page">
    <h1>
      <RouterLink class="app-title-link" :to="{ name: 'teacher-tasks' }">教师端｜课堂巩固练习</RouterLink>
    </h1>

    <div class="card">
      <div class="teacher-page-header">
        <div>
          <h2>任务列表</h2>
          <p class="hint">可编辑、删除任务，继续导入题目或跳转到任务分析页。</p>
        </div>
        <div class="row-actions">
          <button class="primary-btn row-action-btn" @click="goCreateTask">
            新建任务
          </button>
          <button class="secondary-btn row-action-btn" :disabled="loadingTasks" @click="loadTeacherTasks">
            {{ loadingTasks ? "刷新中..." : "刷新列表" }}
          </button>
        </div>
      </div>

      <p v-if="loadingTasks" class="hint">正在加载任务列表...</p>
      <p v-else-if="listErrorMessage" class="error">{{ listErrorMessage }}</p>
      <div v-else-if="teacherTasks.length === 0" class="empty-state">暂无任务数据</div>
      <div v-else class="table-wrap">
        <table class="data-table task-table">
          <colgroup>
            <col class="task-col-id" />
            <col class="task-col-title" />
            <col class="task-col-grade" />
            <col class="task-col-status" />
            <col class="task-col-count" />
            <col class="task-col-time" />
            <col class="task-col-actions" />
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>年级</th>
              <th>状态</th>
              <th>题目数</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in teacherTasks" :key="task.id">
              <td>{{ task.id }}</td>
              <td>
                <div class="task-table-title">{{ task.title || "-" }}</div>
                <div v-if="task.description" class="task-table-description">
                  {{ task.description }}
                </div>
              </td>
              <td>{{ formatGrade(task.grade) }}</td>
              <td>
                <span class="task-status-pill" :class="`task-status-${task.status || 'unknown'}`">
                  {{ getTaskStatusLabel(task.status) }}
                </span>
              </td>
              <td>{{ task.question_count }}</td>
              <td class="task-created-at">{{ formatCreatedAt(task.created_at) }}</td>
              <td>
                <div class="task-actions-cell">
                  <button class="primary-btn row-action-btn analysis-action-btn" @click="goAnalysis(task.id)">
                    查看分析
                  </button>
                  <div class="task-secondary-actions" aria-label="任务快捷操作">
                    <button
                      class="secondary-btn row-action-btn compact-action-btn"
                      title="编辑任务"
                      aria-label="编辑任务"
                      @click="startEditTask(task)"
                    >
                      编辑任务
                    </button>
                    <button
                      class="secondary-btn row-action-btn compact-action-btn"
                      title="编辑题目"
                      aria-label="编辑题目"
                      @click="openQuestionManager(task)"
                    >
                      编辑题目
                    </button>
                    <button
                      class="secondary-btn row-action-btn compact-action-btn"
                      title="导入题目"
                      aria-label="导入题目"
                      @click="fillImportTask(task.id)"
                    >
                      导入
                    </button>
                    <button
                      class="secondary-btn row-action-btn compact-action-btn danger-btn"
                      :disabled="deletingTaskId === task.id"
                      title="删除任务"
                      aria-label="删除任务"
                      @click="handleDeleteTask(task)"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="taskActionSuccessMessage" class="success-text">{{ taskActionSuccessMessage }}</p>
      <p v-if="taskActionErrorMessage" class="error">{{ taskActionErrorMessage }}</p>
    </div>

    <div v-if="editingTask" ref="editTaskSection" class="card">
      <div class="teacher-page-header">
        <div>
          <h2>编辑任务</h2>
          <p class="hint">当前任务 ID：{{ editingTask.id }}</p>
        </div>
        <button class="secondary-btn" :disabled="updatingTask" @click="cancelEditTask">取消</button>
      </div>

      <div class="teacher-grid">
        <section class="teacher-panel">
          <div class="form-row">
            <label for="edit-task-title">标题</label>
            <input id="edit-task-title" v-model="editTaskForm.title" placeholder="请输入任务标题" />
          </div>

          <div class="form-row">
            <label for="edit-task-grade">年级</label>
            <select id="edit-task-grade" v-model="editTaskForm.grade" class="form-row-select">
              <option value="">请选择年级</option>
              <option value="6">6</option>
              <option value="7">7</option>
              <option value="8">8</option>
            </select>
          </div>

          <div class="form-row">
            <label for="edit-task-status">状态</label>
            <select id="edit-task-status" v-model="editTaskForm.status" class="form-row-select">
              <option value="">不设置</option>
              <option value="draft">草稿</option>
              <option value="published">已发布</option>
              <option value="archived">已归档</option>
            </select>
          </div>

          <div class="form-row">
            <label for="edit-task-description">说明</label>
            <textarea
              id="edit-task-description"
              v-model="editTaskForm.description"
              class="textarea-input"
              placeholder="请输入任务说明"
            />
          </div>

          <div class="query-bar">
            <button class="primary-btn" :disabled="updatingTask" @click="handleUpdateTask">
              {{ updatingTask ? "保存中..." : "保存修改" }}
            </button>
          </div>

          <p v-if="editTaskSuccessMessage" class="success-text">{{ editTaskSuccessMessage }}</p>
          <p v-if="editTaskErrorMessage" class="error">{{ editTaskErrorMessage }}</p>
        </section>
      </div>
    </div>

    <div ref="questionManagerSection" class="card">
      <div class="teacher-page-header">
        <div>
          <h2>题目管理</h2>
          <p class="hint">题目列表仍使用现有接口加载，保存时只提交变更字段。</p>
        </div>
        <div class="row-actions">
          <button
            class="secondary-btn row-action-btn"
            :disabled="questionLoading || questions.length === 0"
            @click="exportAllQuestionsJson"
          >
            导出 JSON
          </button>
          <button
            class="secondary-btn row-action-btn"
            :disabled="questionLoading || questions.length === 0"
            @click="exportAllQuestionsWjx"
          >
            导出问卷星
          </button>
          <button class="secondary-btn row-action-btn" :disabled="questionLoading" @click="loadSelectedTaskQuestions">
            {{ questionLoading ? "加载中..." : "刷新题目" }}
          </button>
        </div>
      </div>

      <div class="analysis-query-bar">
        <div class="form-row analysis-query-field">
          <label for="question-task-select">选择任务</label>
          <select
            id="question-task-select"
            v-model="questionManagerTaskId"
            class="form-row-select"
            :disabled="loadingTasks || teacherTasks.length === 0"
            @change="handleQuestionTaskChange"
          >
            <option value="">{{ loadingTasks ? "正在加载任务..." : "请选择任务" }}</option>
            <option v-for="task in teacherTasks" :key="task.id" :value="String(task.id)">
              {{ formatTaskOption(task) }}
            </option>
          </select>
        </div>
        <div class="form-row analysis-filter-field">
          <label for="question-keyword-filter">搜索题目</label>
          <input
            id="question-keyword-filter"
            v-model="questionKeywordFilter"
            placeholder="题号、题干、知识点"
          />
        </div>
        <div class="form-row analysis-filter-field">
          <label for="question-type-filter">题型</label>
          <select id="question-type-filter" v-model="questionTypeFilter" class="form-row-select">
            <option value="">全部题型</option>
            <option value="single_choice">单选题</option>
            <option value="multiple_choice">多选题</option>
            <option value="judgment">判断题</option>
            <option value="blank">填空题</option>
          </select>
        </div>
        <div class="form-row analysis-filter-field">
          <label for="question-difficulty-filter">难度</label>
          <select id="question-difficulty-filter" v-model="questionDifficultyFilter" class="form-row-select">
            <option value="">全部难度</option>
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
            <option value="__empty">未标注</option>
          </select>
        </div>
      </div>

      <p v-if="questionErrorMessage" class="error">{{ questionErrorMessage }}</p>
      <p v-if="questionSuccessMessage" class="success-text">{{ questionSuccessMessage }}</p>
      <div v-if="!questionManagerTaskId" class="empty-state">请选择一个任务后编辑题目</div>
      <p v-else-if="questionLoading" class="hint">正在加载题目列表...</p>
      <div v-else-if="questions.length === 0" class="empty-state">当前任务暂无题目</div>
      <div v-else-if="filteredQuestions.length === 0" class="empty-state">没有匹配筛选条件的题目</div>

      <div v-else class="question-management-layout">
        <div class="question-list-panel">
          <article
            v-for="question in filteredQuestions"
            :key="question.question_pk"
            class="question-edit-card"
            :class="{ 'question-edit-card-active': selectedQuestionPk === question.question_pk }"
          >
            <div class="question-stat-header">
              <div class="question-stat-title-block">
                <div class="question-stat-title">第 {{ question.question_pk }} 题</div>
                <div class="question-stat-meta">
                  <span>{{ getQuestionTypeLabel(question.question_type) }}</span>
                  <span>{{ getDifficultyLabel(question.difficulty) }}</span>
                  <span>{{ question.knowledge_point || "未标注知识点" }}</span>
                </div>
              </div>
              <div class="question-card-actions">
                <button
                  class="secondary-btn row-action-btn"
                  :disabled="deletingQuestionPk === question.question_pk"
                  @click="startEditQuestion(question)"
                >
                  编辑
                </button>
                <div class="question-export-menu">
                  <button
                    class="secondary-btn row-action-btn"
                    :disabled="deletingQuestionPk === question.question_pk"
                    @click="toggleQuestionExportMenu(question.question_pk)"
                  >
                    导出
                  </button>
                  <div
                    v-if="String(openQuestionExportMenuPk) === String(question.question_pk)"
                    class="question-export-dropdown"
                  >
                    <button type="button" @click="copySingleQuestionJson(question)">复制 JSON</button>
                    <button type="button" @click="copySingleQuestionWjx(question)">复制问卷星</button>
                  </div>
                </div>
                <button
                  class="secondary-btn row-action-btn danger-btn"
                  :disabled="deletingQuestionPk === question.question_pk || updatingQuestion"
                  @click="handleDeleteQuestion(question)"
                >
                  {{ deletingQuestionPk === question.question_pk ? "删除中..." : "删除" }}
                </button>
              </div>
            </div>
            <p class="question-stat-stem">{{ question.stem || "暂无题干" }}</p>
          </article>
        </div>

        <section v-if="editingQuestion" ref="questionEditorSection" class="teacher-panel question-editor-panel">
          <h3>编辑第 {{ editingQuestion.question_pk }} 题</h3>
          <p class="hint">
            修改题目会影响之后学生的新作答评分，历史作答记录不会自动重算。
          </p>

          <div class="form-row">
            <label for="question-knowledge-point">知识点</label>
            <input id="question-knowledge-point" v-model="editQuestionForm.knowledge_point" />
          </div>

          <div class="form-row">
            <label for="question-type">题型</label>
            <select id="question-type" v-model="editQuestionForm.question_type" class="form-row-select">
              <option value="single_choice">单选题</option>
              <option value="multiple_choice">多选题</option>
              <option value="judgment">判断题</option>
              <option value="blank">填空题</option>
            </select>
          </div>

          <div class="form-row">
            <label for="question-difficulty">难度</label>
            <select id="question-difficulty" v-model="editQuestionForm.difficulty" class="form-row-select">
              <option value="">未标注</option>
              <option value="easy">简单</option>
              <option value="medium">中等</option>
              <option value="hard">困难</option>
            </select>
          </div>

          <div class="form-row">
            <label for="question-stem">题干</label>
            <textarea id="question-stem" v-model="editQuestionForm.stem" class="textarea-input" />
          </div>

          <div class="form-row">
            <div class="form-row-header">
              <label>选项</label>
              <button class="secondary-btn row-action-btn compact-action-btn" type="button" @click="addQuestionOption">
                添加选项
              </button>
            </div>
            <div v-if="editQuestionForm.options.length === 0" class="empty-inline">当前题目没有选项</div>
            <div v-else class="question-option-editor-list">
              <div
                v-for="(option, optionIndex) in editQuestionForm.options"
                :key="`edit-option-${optionIndex}`"
                class="question-option-editor-row"
              >
                <div class="form-row option-id-field">
                  <label :for="`question-option-id-${optionIndex}`">编号</label>
                  <input
                    :id="`question-option-id-${optionIndex}`"
                    v-model="option.id"
                    placeholder="A"
                  />
                </div>
                <div class="form-row option-text-field">
                  <label :for="`question-option-text-${optionIndex}`">选项内容</label>
                  <input
                    :id="`question-option-text-${optionIndex}`"
                    v-model="option.text"
                    placeholder="请输入选项内容"
                  />
                </div>
                <div class="form-row option-explanation-field">
                  <label :for="`question-option-explanation-${optionIndex}`">选项解释</label>
                  <input
                    :id="`question-option-explanation-${optionIndex}`"
                    v-model="option.explanation"
                    placeholder="可填写该选项反馈"
                  />
                </div>
                <button
                  class="secondary-btn row-action-btn compact-action-btn danger-btn option-remove-btn"
                  type="button"
                  @click="removeQuestionOption(optionIndex)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>

          <div class="form-row">
            <label for="question-correct-answer">正确答案</label>
            <input
              id="question-correct-answer"
              v-model="editQuestionForm.correctAnswerText"
              placeholder="多个答案用逗号分隔，例如 A,B"
            />
          </div>

          <div class="form-row">
            <label for="question-accepted-answers">填空可接受答案</label>
            <input
              id="question-accepted-answers"
              v-model="editQuestionForm.acceptedAnswersText"
              placeholder="多个答案用逗号分隔"
            />
          </div>

          <div class="form-row">
            <label for="question-score">分值</label>
            <input id="question-score" v-model="editQuestionForm.score" type="number" min="0" />
          </div>

          <div class="teacher-grid compact-grid">
            <div class="form-row">
              <label for="encouragement-correct">答对鼓励语</label>
              <input id="encouragement-correct" v-model="editQuestionForm.encouragement.correct" />
            </div>
            <div class="form-row">
              <label for="encouragement-wrong">答错鼓励语</label>
              <input id="encouragement-wrong" v-model="editQuestionForm.encouragement.wrong" />
            </div>
            <div class="form-row">
              <label for="encouragement-retry-correct">订正正确鼓励语</label>
              <input id="encouragement-retry-correct" v-model="editQuestionForm.encouragement.retryCorrect" />
            </div>
            <div class="form-row">
              <label for="encouragement-retry-wrong">再次错误鼓励语</label>
              <input id="encouragement-retry-wrong" v-model="editQuestionForm.encouragement.retryWrong" />
            </div>
          </div>

          <div class="form-row">
            <label for="question-explanation">学生解析</label>
            <textarea
              id="question-explanation"
              v-model="editQuestionForm.student_explanation"
              class="textarea-input"
            />
          </div>

          <div class="query-bar">
            <button class="primary-btn" :disabled="updatingQuestion" @click="handleUpdateQuestion">
              {{ updatingQuestion ? "保存中..." : "保存题目" }}
            </button>
            <button class="secondary-btn" :disabled="updatingQuestion" @click="cancelEditQuestion">
              取消
            </button>
          </div>
        </section>
      </div>
    </div>

    <div class="card">
      <div class="teacher-page-header">
        <div>
          <h2>任务操作</h2>
          <p class="hint">创建任务、导入题目 JSON，并导入学生名单。</p>
        </div>
        <button class="secondary-btn" @click="openStudentApp">打开学生端</button>
      </div>

      <div class="teacher-grid">
        <section ref="createTaskSection" class="teacher-panel">
          <h3>创建任务</h3>

          <div class="form-row">
            <label for="task-title">标题</label>
            <input id="task-title" ref="createTaskTitleInput" v-model="createForm.title" placeholder="请输入任务标题" />
          </div>

          <div class="form-row">
            <label for="task-grade">年级</label>
            <select id="task-grade" v-model="createForm.grade" class="form-row-select">
              <option value="">请选择年级</option>
              <option value="6">6</option>
              <option value="7">7</option>
              <option value="8">8</option>
            </select>
          </div>

          <div class="form-row">
            <label for="task-description">说明</label>
            <textarea
              id="task-description"
              v-model="createForm.description"
              class="textarea-input"
              placeholder="请输入任务说明"
            />
          </div>

          <div class="query-bar">
            <button class="primary-btn" :disabled="creatingTask" @click="handleCreateTask">
              {{ creatingTask ? "创建中..." : "创建任务" }}
            </button>
          </div>

          <p v-if="createSuccessMessage" class="success-text">{{ createSuccessMessage }}</p>
          <p v-if="createErrorMessage" class="error">{{ createErrorMessage }}</p>
        </section>

        <section ref="importQuestionsSection" class="teacher-panel">
          <h3>导入题目</h3>

          <div class="form-row">
            <label for="import-task-select">选择任务</label>
            <select
              id="import-task-select"
              v-model="importForm.taskId"
              class="form-row-select"
              :disabled="loadingTasks || teacherTasks.length === 0"
            >
              <option value="">
                {{ loadingTasks ? "正在加载任务..." : "请选择任务" }}
              </option>
              <option v-for="task in teacherTasks" :key="task.id" :value="String(task.id)">
                {{ formatTaskOption(task) }}
              </option>
            </select>
            <p v-if="!loadingTasks && teacherTasks.length === 0" class="hint">
              暂无可选任务，可先创建任务。
            </p>
          </div>

          <div class="form-row">
            <label for="import-task-id">或手动输入任务 ID</label>
            <input
              id="import-task-id"
              v-model="importForm.taskId"
              inputmode="numeric"
              placeholder="请输入任务 ID"
            />
          </div>

          <div class="form-row">
            <label for="import-json">JSON 文本</label>
            <textarea
              id="import-json"
              v-model="importForm.jsonText"
              class="textarea-input textarea-large"
              placeholder='请输入形如 {"questions": [...]} 的 JSON'
            />
          </div>

          <div class="query-bar">
            <button class="primary-btn" :disabled="importingQuestions" @click="handleImportQuestions">
              {{ importingQuestions ? "导入中..." : "导入题目" }}
            </button>
          </div>

          <p v-if="importSuccessMessage" class="success-text">{{ importSuccessMessage }}</p>
          <div v-if="importSuccessTaskId" class="query-bar">
            <button class="secondary-btn" type="button" @click="viewImportedQuestions">
              查看题目
            </button>
            <button class="secondary-btn" type="button" @click="goAnalysis(importSuccessTaskId)">
              查看分析
            </button>
          </div>
          <p v-if="importErrorMessage" class="error">{{ importErrorMessage }}</p>
        </section>

        <section class="teacher-panel">
          <h3>导入学生名单</h3>
          <p class="hint">可上传 CSV 批量导入，也可以在网页上直接新增或更新单个学生。</p>

          <div class="query-bar">
            <button class="secondary-btn" type="button" @click="downloadStudentCsvTemplate">
              下载 CSV 模板
            </button>
          </div>

          <div class="form-row">
            <label for="student-csv">学生 CSV 文件</label>
            <input
              id="student-csv"
              ref="studentCsvInput"
              type="file"
              accept=".csv,text/csv"
              @change="handleStudentCsvChange"
            />
          </div>

          <div class="csv-template-box">
            <div class="csv-template-title">模板字段</div>
            <code>student_no,student_name,grade,class_name,status</code>
            <div class="hint">也支持：学号,姓名,年级,班级,状态</div>
            <div class="hint">班级请填写 1、2、3、4，不需要填写“1班”。</div>
          </div>

          <div class="query-bar">
            <button class="primary-btn" :disabled="importingStudents" @click="handleImportStudents">
              {{ importingStudents ? "上传中..." : "导入学生" }}
            </button>
            <button class="secondary-btn" :disabled="importingStudents || !studentCsvFile" @click="resetStudentImport">
              清空
            </button>
          </div>

          <p v-if="studentImportSuccessMessage" class="success-text">
            {{ studentImportSuccessMessage }}
          </p>
          <p v-if="studentImportErrorMessage" class="error">{{ studentImportErrorMessage }}</p>

          <div v-if="studentImportResult" class="import-result-grid">
            <div class="summary-card">
              <span class="summary-label">读取总数</span>
              <strong>{{ studentImportResult.count }}</strong>
            </div>
            <div class="summary-card">
              <span class="summary-label">新增人数</span>
              <strong>{{ studentImportResult.created_count }}</strong>
            </div>
            <div class="summary-card">
              <span class="summary-label">更新人数</span>
              <strong>{{ studentImportResult.updated_count }}</strong>
            </div>
          </div>

          <div class="single-student-form">
            <h4>单个学生</h4>
            <div class="teacher-grid compact-grid">
              <div class="form-row">
                <label for="single-student-no">学号</label>
                <input
                  id="single-student-no"
                  v-model="singleStudentForm.student_no"
                  inputmode="numeric"
                  maxlength="8"
                  placeholder="8 位学号"
                />
              </div>
              <div class="form-row">
                <label for="single-student-name">姓名</label>
                <input id="single-student-name" v-model="singleStudentForm.student_name" placeholder="学生姓名" />
              </div>
              <div class="form-row">
                <label for="single-student-grade">年级</label>
                <select id="single-student-grade" v-model="singleStudentForm.grade" class="form-row-select">
                  <option value="">请选择年级</option>
                  <option value="6">6</option>
                  <option value="7">7</option>
                  <option value="8">8</option>
                </select>
              </div>
              <div class="form-row">
                <label for="single-student-class">班级</label>
                <select id="single-student-class" v-model="singleStudentForm.class_name" class="form-row-select">
                  <option value="">请选择班级</option>
                  <option value="1">1班</option>
                  <option value="2">2班</option>
                  <option value="3">3班</option>
                  <option value="4">4班</option>
                </select>
              </div>
              <div class="form-row">
                <label for="single-student-status">状态</label>
                <select id="single-student-status" v-model="singleStudentForm.status" class="form-row-select">
                  <option value="active">正常</option>
                  <option value="inactive">停用</option>
                  <option value="graduated">已毕业</option>
                </select>
              </div>
            </div>

            <div class="query-bar">
              <button class="primary-btn" :disabled="importingSingleStudent" @click="handleImportSingleStudent">
                {{ importingSingleStudent ? "保存中..." : "保存单个学生" }}
              </button>
              <button class="secondary-btn" :disabled="importingSingleStudent" @click="resetSingleStudentForm">
                清空
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import {
  createTeacherTask,
  deleteTeacherQuestion,
  deleteTeacherTask,
  getTeacherTaskQuestions,
  getTeacherTasks,
  importTeacherQuestions,
  importTeacherStudentsCsv,
  updateTeacherQuestion,
  updateTeacherTask,
} from "../api/tasks";

const router = useRouter();

const teacherTasks = ref([]);
const loadingTasks = ref(false);
const creatingTask = ref(false);
const importingQuestions = ref(false);
const importingStudents = ref(false);
const importingSingleStudent = ref(false);
const updatingTask = ref(false);
const deletingTaskId = ref(null);
const questionLoading = ref(false);
const updatingQuestion = ref(false);
const deletingQuestionPk = ref(null);
const studentCsvInput = ref(null);
const studentCsvFile = ref(null);
const createTaskSection = ref(null);
const createTaskTitleInput = ref(null);
const editTaskSection = ref(null);
const questionManagerSection = ref(null);
const questionEditorSection = ref(null);
const importQuestionsSection = ref(null);

const listErrorMessage = ref("");
const createErrorMessage = ref("");
const createSuccessMessage = ref("");
const importErrorMessage = ref("");
const importSuccessMessage = ref("");
const importSuccessTaskId = ref("");
const studentImportErrorMessage = ref("");
const studentImportSuccessMessage = ref("");
const studentImportResult = ref(null);
const taskActionErrorMessage = ref("");
const taskActionSuccessMessage = ref("");
const editTaskErrorMessage = ref("");
const editTaskSuccessMessage = ref("");
const questionErrorMessage = ref("");
const questionSuccessMessage = ref("");

const editingTask = ref(null);
const questionManagerTaskId = ref("");
const questions = ref([]);
const editingQuestion = ref(null);
const selectedQuestionPk = ref("");
const openQuestionExportMenuPk = ref("");
const questionKeywordFilter = ref("");
const questionTypeFilter = ref("");
const questionDifficultyFilter = ref("");

const createForm = reactive({
  title: "",
  grade: "",
  description: "",
});

const editTaskForm = reactive({
  title: "",
  grade: "",
  description: "",
  status: "",
});

const importForm = reactive({
  taskId: "",
  jsonText: "",
});

const singleStudentForm = reactive({
  student_no: "",
  student_name: "",
  grade: "",
  class_name: "",
  status: "active",
});

const editQuestionForm = reactive({
  knowledge_point: "",
  question_type: "",
  difficulty: "",
  stem: "",
  options: [],
  correctAnswerText: "",
  acceptedAnswersText: "",
  encouragement: {
    correct: "",
    wrong: "",
    retryCorrect: "",
    retryWrong: "",
  },
  student_explanation: "",
  score: "",
});

const filteredQuestions = computed(() => {
  const keyword = questionKeywordFilter.value.trim().toLowerCase();
  const type = questionTypeFilter.value;
  const difficulty = questionDifficultyFilter.value;

  return questions.value.filter((question) => {
    if (type && question.question_type !== type) return false;
    if (difficulty === "__empty" && question.difficulty) return false;
    if (difficulty && difficulty !== "__empty" && question.difficulty !== difficulty) return false;
    if (!keyword) return true;

    const searchableText = [
      question.question_pk,
      question.stem,
      question.knowledge_point,
      getQuestionTypeLabel(question.question_type),
      getDifficultyLabel(question.difficulty),
    ]
      .join(" ")
      .toLowerCase();

    return searchableText.includes(keyword);
  });
});

async function loadTeacherTasks() {
  loadingTasks.value = true;
  listErrorMessage.value = "";

  try {
    teacherTasks.value = await getTeacherTasks();
  } catch {
    teacherTasks.value = [];
    listErrorMessage.value = "任务列表加载失败，请稍后重试";
  } finally {
    loadingTasks.value = false;
  }
}

function resetCreateMessages() {
  createErrorMessage.value = "";
  createSuccessMessage.value = "";
}

function resetImportMessages() {
  importErrorMessage.value = "";
  importSuccessMessage.value = "";
  importSuccessTaskId.value = "";
}

function resetStudentImportMessages() {
  studentImportErrorMessage.value = "";
  studentImportSuccessMessage.value = "";
}

function resetTaskActionMessages() {
  taskActionErrorMessage.value = "";
  taskActionSuccessMessage.value = "";
}

function resetQuestionMessages() {
  questionErrorMessage.value = "";
  questionSuccessMessage.value = "";
}

async function handleCreateTask() {
  resetCreateMessages();

  const title = createForm.title.trim();
  const grade = normalizeGrade(createForm.grade);
  const description = createForm.description.trim();

  if (!title) {
    createErrorMessage.value = "请输入任务标题";
    return;
  }

  if (!grade) {
    createErrorMessage.value = "请输入年级";
    return;
  }

  creatingTask.value = true;

  try {
    const createdTask = await createTeacherTask({
      title,
      grade,
      description,
    });

    createForm.title = "";
    createForm.grade = "";
    createForm.description = "";
    createSuccessMessage.value = `任务创建成功，任务 ID：${createdTask.id}`;
    await loadTeacherTasks();
  } catch {
    createErrorMessage.value = "任务创建失败，请稍后重试";
  } finally {
    creatingTask.value = false;
  }
}

function startEditTask(task) {
  editingTask.value = { ...task };
  editTaskForm.title = task.title || "";
  editTaskForm.grade = normalizeGrade(task.grade);
  editTaskForm.description = task.description || "";
  editTaskForm.status = task.status || "";
  editTaskErrorMessage.value = "";
  editTaskSuccessMessage.value = "";
  void scrollToSection(editTaskSection);
}

function cancelEditTask() {
  editingTask.value = null;
  editTaskErrorMessage.value = "";
  editTaskSuccessMessage.value = "";
}

async function handleUpdateTask() {
  editTaskErrorMessage.value = "";
  editTaskSuccessMessage.value = "";

  if (!editingTask.value?.id) return;

  const title = editTaskForm.title.trim();
  const grade = normalizeGrade(editTaskForm.grade);
  const description = editTaskForm.description.trim();
  const status = editTaskForm.status.trim();

  if (!title) {
    editTaskErrorMessage.value = "请输入任务标题";
    return;
  }

  if (!grade) {
    editTaskErrorMessage.value = "请输入年级";
    return;
  }

  const payload = {};
  if (title !== (editingTask.value.title || "")) payload.title = title;
  if (grade !== normalizeGrade(editingTask.value.grade)) payload.grade = grade;
  if (description !== (editingTask.value.description || "")) payload.description = description;
  if (status !== (editingTask.value.status || "")) payload.status = status;

  if (Object.keys(payload).length === 0) {
    editTaskErrorMessage.value = "没有检测到需要保存的修改";
    return;
  }

  updatingTask.value = true;

  try {
    const updatedTask = await updateTeacherTask(editingTask.value.id, payload);
    teacherTasks.value = teacherTasks.value.map((task) =>
      task.id === updatedTask.id ? updatedTask : task
    );
    editingTask.value = { ...updatedTask };
    editTaskSuccessMessage.value = "任务修改成功";
  } catch (error) {
    editTaskErrorMessage.value = error.message || "任务修改失败，请稍后重试";
  } finally {
    updatingTask.value = false;
  }
}

async function handleDeleteTask(task) {
  resetTaskActionMessages();

  const confirmed = window.confirm(
    `确定删除任务「${task.title || task.id}」吗？该任务下的题目、提交记录和答题记录也会被删除。`
  );
  if (!confirmed) return;

  deletingTaskId.value = task.id;

  try {
    await deleteTeacherTask(task.id);
    teacherTasks.value = teacherTasks.value.filter((item) => item.id !== task.id);
    taskActionSuccessMessage.value = "任务已删除";

    if (editingTask.value?.id === task.id) {
      cancelEditTask();
    }
    if (String(questionManagerTaskId.value) === String(task.id)) {
      resetQuestionManager();
    }
  } catch (error) {
    taskActionErrorMessage.value = error.message || "任务删除失败，请稍后重试";
  } finally {
    deletingTaskId.value = null;
  }
}

function openQuestionManager(task) {
  questionManagerTaskId.value = String(task.id);
  void scrollToSection(questionManagerSection);
  void loadSelectedTaskQuestions();
}

function handleQuestionTaskChange() {
  questions.value = [];
  cancelEditQuestion();
  closeQuestionExportMenu();
  resetQuestionMessages();
  if (questionManagerTaskId.value) {
    void loadSelectedTaskQuestions();
  }
}

async function loadSelectedTaskQuestions() {
  resetQuestionMessages();
  cancelEditQuestion();
  closeQuestionExportMenu();

  const taskId = String(questionManagerTaskId.value || "").trim();
  if (!/^\d+$/.test(taskId)) {
    questionErrorMessage.value = "请先选择正确的任务";
    return;
  }

  questionLoading.value = true;

  try {
    questions.value = await getTeacherTaskQuestions(taskId);
  } catch (error) {
    questions.value = [];
    questionErrorMessage.value = error.message || "题目列表加载失败，请稍后重试";
  } finally {
    questionLoading.value = false;
  }
}

function resetQuestionManager() {
  questionManagerTaskId.value = "";
  questions.value = [];
  resetQuestionFilters();
  cancelEditQuestion();
  closeQuestionExportMenu();
  resetQuestionMessages();
}

function startEditQuestion(question) {
  closeQuestionExportMenu();
  editingQuestion.value = cloneQuestion(question);
  selectedQuestionPk.value = question.question_pk;
  editQuestionForm.knowledge_point = question.knowledge_point || "";
  editQuestionForm.question_type = question.question_type || "";
  editQuestionForm.difficulty = question.difficulty || "";
  editQuestionForm.stem = question.stem || "";
  editQuestionForm.options = cloneQuestionOptions(question.options);
  editQuestionForm.correctAnswerText = formatArrayInput(question.correct_answer);
  editQuestionForm.acceptedAnswersText = formatArrayInput(question.accepted_answers);
  editQuestionForm.encouragement.correct = question.encouragement?.correct || "";
  editQuestionForm.encouragement.wrong = question.encouragement?.wrong || "";
  editQuestionForm.encouragement.retryCorrect = question.encouragement?.retryCorrect || "";
  editQuestionForm.encouragement.retryWrong = question.encouragement?.retryWrong || "";
  editQuestionForm.student_explanation = question.student_explanation || "";
  editQuestionForm.score = question.score ?? 0;
  resetQuestionMessages();
  void scrollToSection(questionEditorSection);
}

function cancelEditQuestion() {
  editingQuestion.value = null;
  selectedQuestionPk.value = "";
  editQuestionForm.options = [];
}

function resetQuestionFilters() {
  questionKeywordFilter.value = "";
  questionTypeFilter.value = "";
  questionDifficultyFilter.value = "";
}

function addQuestionOption() {
  editQuestionForm.options.push({
    id: getNextOptionId(editQuestionForm.options),
    text: "",
    explanation: "",
  });
}

function removeQuestionOption(optionIndex) {
  editQuestionForm.options.splice(optionIndex, 1);
}

function toggleQuestionExportMenu(questionPk) {
  const currentPk = String(questionPk ?? "");
  openQuestionExportMenuPk.value =
    String(openQuestionExportMenuPk.value) === currentPk ? "" : currentPk;
}

function closeQuestionExportMenu() {
  openQuestionExportMenuPk.value = "";
}

async function handleUpdateQuestion() {
  resetQuestionMessages();

  const taskId = String(questionManagerTaskId.value || "").trim();
  const questionPk = editingQuestion.value?.question_pk;
  if (!/^\d+$/.test(taskId) || !questionPk) {
    questionErrorMessage.value = "请先选择要编辑的题目";
    return;
  }

  let payload;
  try {
    payload = buildQuestionUpdatePayload();
  } catch (error) {
    questionErrorMessage.value = error.message;
    return;
  }

  if (Object.keys(payload).length === 0) {
    questionErrorMessage.value = "没有检测到需要保存的修改";
    return;
  }

  updatingQuestion.value = true;

  try {
    const updatedQuestion = await updateTeacherQuestion(taskId, questionPk, payload);
    questions.value = questions.value.map((question) =>
      String(question.question_pk) === String(updatedQuestion.question_pk) ? updatedQuestion : question
    );
    startEditQuestion(updatedQuestion);
    questionSuccessMessage.value = "题目修改成功";
  } catch (error) {
    questionErrorMessage.value = getQuestionUpdateErrorMessage(error);
  } finally {
    updatingQuestion.value = false;
  }
}

async function handleDeleteQuestion(question) {
  closeQuestionExportMenu();
  resetQuestionMessages();

  const taskId = String(questionManagerTaskId.value || "").trim();
  const questionPk = question?.question_pk;
  if (!/^\d+$/.test(taskId) || !questionPk) {
    questionErrorMessage.value = "请先选择要删除的题目";
    return;
  }

  const confirmed = window.confirm(
    `确定删除第 ${questionPk} 题吗？如果该题已有学生作答，相关答题记录和统计可能一并删除。`
  );
  if (!confirmed) return;

  deletingQuestionPk.value = questionPk;

  try {
    await deleteTeacherQuestion(taskId, questionPk);
    questions.value = questions.value.filter(
      (item) => String(item.question_pk) !== String(questionPk)
    );
    if (String(editingQuestion.value?.question_pk) === String(questionPk)) {
      cancelEditQuestion();
    }
    questionSuccessMessage.value = `第 ${questionPk} 题已删除`;
    await loadTeacherTasks();
  } catch (error) {
    questionErrorMessage.value = error.message || "题目删除失败，请稍后重试";
  } finally {
    deletingQuestionPk.value = null;
  }
}

function buildQuestionUpdatePayload() {
  const original = editingQuestion.value;
  const payload = {};

  addChangedField(payload, "knowledge_point", editQuestionForm.knowledge_point.trim(), original.knowledge_point || "");
  addChangedField(payload, "question_type", editQuestionForm.question_type, original.question_type || "");
  addChangedField(payload, "difficulty", editQuestionForm.difficulty, original.difficulty || "");
  addChangedField(payload, "stem", editQuestionForm.stem.trim(), original.stem || "");

  const options = normalizeOptionsForm(editQuestionForm.options);
  if (!isSameJson(options, original.options || [])) payload.options = options;

  const correctAnswer = parseArrayInput(editQuestionForm.correctAnswerText);
  if (!isSameJson(correctAnswer, original.correct_answer || [])) payload.correct_answer = correctAnswer;

  const acceptedAnswers = parseArrayInput(editQuestionForm.acceptedAnswersText);
  if (!isSameJson(acceptedAnswers, original.accepted_answers || [])) {
    payload.accepted_answers = acceptedAnswers;
  }

  const score = Number(editQuestionForm.score);
  if (!Number.isFinite(score) || score < 0) {
    throw new Error("请输入有效的分值");
  }
  if (score !== Number(original.score ?? 0)) payload.score = score;

  const encouragement = {
    correct: editQuestionForm.encouragement.correct.trim(),
    wrong: editQuestionForm.encouragement.wrong.trim(),
    retryCorrect: editQuestionForm.encouragement.retryCorrect.trim(),
    retryWrong: editQuestionForm.encouragement.retryWrong.trim(),
  };
  if (!isSameJson(encouragement, normalizeEncouragement(original.encouragement))) {
    payload.encouragement = encouragement;
  }

  addChangedField(
    payload,
    "student_explanation",
    editQuestionForm.student_explanation.trim(),
    original.student_explanation || ""
  );

  return payload;
}

function addChangedField(payload, key, currentValue, originalValue) {
  if (currentValue !== originalValue) {
    payload[key] = currentValue;
  }
}

function parseQuestionsJson() {
  if (!importForm.jsonText.trim()) {
    importErrorMessage.value = "请输入题目 JSON";
    return null;
  }

  let parsed;
  try {
    parsed = JSON.parse(importForm.jsonText);
  } catch {
    importErrorMessage.value = "题目 JSON 格式不合法";
    return null;
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    importErrorMessage.value = "题目 JSON 必须包含非空 questions 数组";
    return null;
  }

  if (!Array.isArray(parsed.questions) || parsed.questions.length === 0) {
    importErrorMessage.value = "题目 JSON 必须包含非空 questions 数组";
    return null;
  }

  return parsed.questions;
}

async function handleImportQuestions() {
  resetImportMessages();

  const taskId = String(importForm.taskId || "").trim();
  if (!/^\d+$/.test(taskId)) {
    importErrorMessage.value = "请输入正确的任务 ID";
    return;
  }

  const questions = parseQuestionsJson();
  if (!questions) return;

  importingQuestions.value = true;

  try {
    const result = await importTeacherQuestions(taskId, questions);
    importSuccessMessage.value = `导入成功，共处理 ${result.count ?? questions.length} 题`;
    importSuccessTaskId.value = taskId;
    await loadTeacherTasks();
  } catch {
    importErrorMessage.value = "题目导入失败，请稍后重试";
  } finally {
    importingQuestions.value = false;
  }
}

function handleStudentCsvChange(event) {
  resetStudentImportMessages();
  studentImportResult.value = null;

  const [file] = event.target.files || [];
  studentCsvFile.value = file || null;

  if (!file) {
    return;
  }

  if (!isCsvFile(file)) {
    studentCsvFile.value = null;
    studentImportErrorMessage.value = "只允许选择 .csv 文件";
    if (studentCsvInput.value) {
      studentCsvInput.value.value = "";
    }
    return;
  }

  if (file.size <= 0) {
    studentCsvFile.value = null;
    studentImportErrorMessage.value = "CSV 文件不能为空";
    if (studentCsvInput.value) {
      studentCsvInput.value.value = "";
    }
  }
}

async function handleImportStudents() {
  resetStudentImportMessages();
  studentImportResult.value = null;

  const file = studentCsvFile.value;
  if (!file) {
    studentImportErrorMessage.value = "请先选择学生 CSV 文件";
    return;
  }

  if (!isCsvFile(file)) {
    studentImportErrorMessage.value = "只允许选择 .csv 文件";
    return;
  }

  if (file.size <= 0) {
    studentImportErrorMessage.value = "CSV 文件不能为空";
    return;
  }

  importingStudents.value = true;

  try {
    const result = await importTeacherStudentsCsv(file);
    studentImportResult.value = {
      count: result.count ?? 0,
      created_count: result.created_count ?? 0,
      updated_count: result.updated_count ?? 0,
    };
    studentImportSuccessMessage.value = result.message || "学生名单导入成功";
  } catch (error) {
    studentImportErrorMessage.value = error.message || "学生名单导入失败，请稍后重试";
  } finally {
    importingStudents.value = false;
  }
}

async function handleImportSingleStudent() {
  resetStudentImportMessages();
  studentImportResult.value = null;

  const studentNo = singleStudentForm.student_no.trim();
  const studentName = singleStudentForm.student_name.trim();
  const grade = normalizeGrade(singleStudentForm.grade);
  const className = normalizeClassName(singleStudentForm.class_name);
  const status = singleStudentForm.status.trim() || "active";

  if (!/^\d{8}$/.test(studentNo)) {
    studentImportErrorMessage.value = "请输入 8 位学号";
    return;
  }
  if (!studentName) {
    studentImportErrorMessage.value = "请输入学生姓名";
    return;
  }
  if (!grade) {
    studentImportErrorMessage.value = "请选择年级";
    return;
  }
  if (!className) {
    studentImportErrorMessage.value = "请输入班级";
    return;
  }

  const csvText = buildStudentCsv([
    {
      student_no: studentNo,
      student_name: studentName,
      grade,
      class_name: className,
      status,
    },
  ]);
  const file = new File([csvText], "single-student.csv", {
    type: "text/csv;charset=utf-8",
  });

  importingSingleStudent.value = true;

  try {
    const result = await importTeacherStudentsCsv(file);
    studentImportResult.value = {
      count: result.count ?? 1,
      created_count: result.created_count ?? 0,
      updated_count: result.updated_count ?? 0,
    };
    studentImportSuccessMessage.value = result.message || "学生保存成功";
  } catch (error) {
    studentImportErrorMessage.value = error.message || "学生保存失败，请稍后重试";
  } finally {
    importingSingleStudent.value = false;
  }
}

function resetStudentImport() {
  studentCsvFile.value = null;
  studentImportResult.value = null;
  resetStudentImportMessages();
  if (studentCsvInput.value) {
    studentCsvInput.value.value = "";
  }
}

function resetSingleStudentForm() {
  singleStudentForm.student_no = "";
  singleStudentForm.student_name = "";
  singleStudentForm.grade = "";
  singleStudentForm.class_name = "";
  singleStudentForm.status = "active";
  resetStudentImportMessages();
  studentImportResult.value = null;
}

function downloadStudentCsvTemplate() {
  const csvText = buildStudentCsv([
    {
      student_no: "20280101",
      student_name: "张三",
      grade: "6",
      class_name: "1",
      status: "active",
    },
  ]);
  downloadTextFile("学生名单导入模板.csv", csvText, "text/csv;charset=utf-8");
}

function exportAllQuestionsJson() {
  exportQuestionsJson(questions.value, `task-${getCurrentTaskFilePart()}-questions.json`);
}

function exportAllQuestionsWjx() {
  exportQuestionsWjx(questions.value, `task-${getCurrentTaskFilePart()}-wjx.txt`);
}

async function copySingleQuestionJson(question) {
  closeQuestionExportMenu();
  const content = buildQuestionsJsonText([question]);
  await copyQuestionText(content, "已复制该题 JSON");
}

async function copySingleQuestionWjx(question) {
  closeQuestionExportMenu();
  const content = buildQuestionsWjxText([question]);
  await copyQuestionText(content, "已复制该题问卷星文本");
}

function exportQuestionsJson(targetQuestions, filename) {
  downloadTextFile(filename, buildQuestionsJsonText(targetQuestions), "application/json;charset=utf-8");
  questionSuccessMessage.value = `已导出 ${targetQuestions.length} 题 JSON`;
}

function exportQuestionsWjx(targetQuestions, filename) {
  downloadTextFile(filename, `\uFEFF${buildQuestionsWjxText(targetQuestions)}\n`, "text/plain;charset=utf-8");
  questionSuccessMessage.value = `已导出 ${targetQuestions.length} 题问卷星文本`;
}

function buildQuestionsJsonText(targetQuestions) {
  const payload = {
    questions: targetQuestions.map(normalizeQuestionForExport),
  };
  return JSON.stringify(payload, null, 2);
}

function buildQuestionsWjxText(targetQuestions) {
  return targetQuestions
    .map((question, index) => formatQuestionForWjx(question, index))
    .filter(Boolean)
    .join("\n\n");
}

async function copyQuestionText(content, successMessage) {
  resetQuestionMessages();

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(content);
    } else {
      copyTextWithTextarea(content);
    }
    questionSuccessMessage.value = successMessage;
  } catch {
    questionErrorMessage.value = "复制失败，请检查浏览器剪贴板权限";
  }
}

function copyTextWithTextarea(content) {
  const textarea = document.createElement("textarea");
  textarea.value = content;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(textarea);

  if (!copied) {
    throw new Error("copy failed");
  }
}

function normalizeQuestionForExport(question) {
  return {
    question_pk: question.question_pk ?? "",
    knowledge_point: question.knowledge_point ?? "",
    question_type: question.question_type ?? "",
    difficulty: question.difficulty ?? "",
    stem: question.stem ?? "",
    options: Array.isArray(question.options) ? question.options.map(normalizeOptionForExport) : [],
    correct_answer: Array.isArray(question.correct_answer) ? [...question.correct_answer] : [],
    accepted_answers: Array.isArray(question.accepted_answers) ? [...question.accepted_answers] : [],
    encouragement: normalizeEncouragement(question.encouragement),
    student_explanation: question.student_explanation ?? "",
    score: question.score ?? 0,
  };
}

function normalizeOptionForExport(option) {
  return {
    id: option?.id ?? "",
    text: option?.text ?? "",
    explanation: option?.explanation ?? "",
  };
}

function formatQuestionForWjx(question, index) {
  const number = index + 1;
  const type = question.question_type;
  const stem = String(question.stem || "未命名题目").trim();
  const answerText = formatWjxAnswer(question);
  const typeLabel = getWjxTypeLabel(type);
  const optionLines = formatWjxOptionLines(question);
  const analysis = String(question.student_explanation || "").trim();
  const lines = [`${number}. ${stem}${answerText ? `（${answerText}）` : ""}${typeLabel}`];

  if (optionLines.length > 0) {
    lines.push(...optionLines);
  }

  if (type === "blank") {
    const blankAnswers = getQuestionAnswers(question);
    if (blankAnswers.length > 0) {
      lines.push(`答案：${blankAnswers.join("；")}`);
    }
  }

  if (analysis) {
    lines.push(`答案解析：${analysis}`);
  }

  return lines.join("\n");
}

function getWjxTypeLabel(type) {
  if (type === "single_choice") return "[单选题]";
  if (type === "multiple_choice") return "[多选题]";
  if (type === "judgment") return "[判断题]";
  if (type === "blank") return "[填空题]";
  return "";
}

function formatWjxOptionLines(question) {
  if (!["single_choice", "multiple_choice", "judgment"].includes(question.question_type)) {
    return [];
  }

  return (Array.isArray(question.options) ? question.options : [])
    .filter((option) => option?.id && option?.text)
    .map((option) => `${option.id}. ${option.text}`);
}

function formatWjxAnswer(question) {
  const answers = getQuestionAnswers(question);
  if (question.question_type === "blank") {
    return "";
  }

  if (question.question_type === "judgment") {
    const firstAnswer = answers[0] || "";
    return normalizeJudgmentAnswer(firstAnswer, question.options);
  }

  return answers.join("");
}

function getQuestionAnswers(question) {
  const acceptedAnswers = Array.isArray(question.accepted_answers) ? question.accepted_answers : [];
  const correctAnswer = Array.isArray(question.correct_answer) ? question.correct_answer : [];
  const source = question.question_type === "blank" && acceptedAnswers.length > 0
    ? acceptedAnswers
    : correctAnswer;
  return source.map((answer) => String(answer).trim()).filter(Boolean);
}

function normalizeJudgmentAnswer(answer, options = []) {
  const normalized = String(answer || "").trim().toLowerCase();
  if (["true", "t", "yes", "y", "1", "对", "正确"].includes(normalized)) return "对";
  if (["false", "f", "no", "n", "0", "错", "错误"].includes(normalized)) return "错";

  const matchedOption = (Array.isArray(options) ? options : []).find(
    (option) => String(option?.id || "").trim().toLowerCase() === normalized
  );
  if (matchedOption) {
    const optionText = String(matchedOption.text || "").trim();
    if (["对", "正确", "true"].includes(optionText.toLowerCase())) return "对";
    if (["错", "错误", "false"].includes(optionText.toLowerCase())) return "错";
  }

  return answer;
}

function buildStudentCsv(rows) {
  const headers = ["student_no", "student_name", "grade", "class_name", "status"];
  const lines = [headers.join(",")];
  rows.forEach((row) => {
    lines.push(headers.map((key) => escapeCsvCell(row[key])).join(","));
  });
  return `\uFEFF${lines.join("\n")}\n`;
}

function escapeCsvCell(value) {
  const text = String(value ?? "");
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function downloadTextFile(filename, content, type = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function getCurrentTaskFilePart() {
  return safeFilenamePart(questionManagerTaskId.value || "unknown");
}

function safeFilenamePart(value) {
  const normalized = String(value ?? "").trim();
  return normalized ? normalized.replace(/[\\/:*?"<>|]+/g, "-") : "unknown";
}

async function goCreateTask() {
  await scrollToSection(createTaskSection);
  createTaskTitleInput.value?.focus();
}

function isCsvFile(file) {
  return /\.csv$/i.test(file.name || "");
}

function fillImportTask(taskId) {
  importForm.taskId = String(taskId);
  resetImportMessages();
  void scrollToSection(importQuestionsSection);
}

function viewImportedQuestions() {
  if (!importSuccessTaskId.value) return;
  questionManagerTaskId.value = String(importSuccessTaskId.value);
  resetQuestionFilters();
  void scrollToSection(questionManagerSection);
  void loadSelectedTaskQuestions();
}

function goAnalysis(taskId) {
  router.push({
    name: "teacher-analysis",
    params: { taskId: String(taskId) },
  });
}

function openStudentApp() {
  const route = router.resolve({ name: "home" });
  window.open(route.href, "_blank", "noopener,noreferrer");
}

function cloneQuestionOptions(options) {
  return (Array.isArray(options) ? options : []).map((option) => ({
    id: option?.id ?? "",
    text: option?.text ?? "",
    explanation: option?.explanation ?? "",
  }));
}

function normalizeOptionsForm(options) {
  const normalizedOptions = (Array.isArray(options) ? options : []).map((option, index) =>
    normalizeOptionInput(option, index)
  );
  const optionIds = new Set();
  normalizedOptions.forEach((option) => {
    const normalizedId = option.id.toLowerCase();
    if (optionIds.has(normalizedId)) {
      throw new Error(`选项编号 ${option.id} 重复`);
    }
    optionIds.add(normalizedId);
  });
  return normalizedOptions;
}

function getNextOptionId(options) {
  const usedIds = new Set(
    (Array.isArray(options) ? options : [])
      .map((option) => String(option?.id || "").trim().toUpperCase())
      .filter(Boolean)
  );
  const candidates = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  return candidates.find((id) => !usedIds.has(id)) || "";
}

function normalizeOptionInput(option, index) {
  if (!option || typeof option !== "object" || Array.isArray(option)) {
    throw new Error(`第 ${index + 1} 个选项必须是对象`);
  }

  const id = option.id;
  const text = option.text;
  const explanation = option.explanation;
  if (typeof id !== "string" || !id.trim()) {
    throw new Error(`第 ${index + 1} 个选项缺少 id 字符串字段`);
  }
  if (typeof text !== "string") {
    throw new Error(`第 ${index + 1} 个选项缺少 text 字符串字段，请不要使用 option_text`);
  }
  if (typeof explanation !== "string") {
    throw new Error(`第 ${index + 1} 个选项缺少 explanation 字符串字段`);
  }

  return {
    id: id.trim(),
    text,
    explanation,
  };
}

function parseArrayInput(value) {
  return String(value || "")
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatArrayInput(value) {
  return Array.isArray(value) ? value.join(",") : "";
}

function normalizeEncouragement(value) {
  return {
    correct: value?.correct || "",
    wrong: value?.wrong || "",
    retryCorrect: value?.retryCorrect || "",
    retryWrong: value?.retryWrong || "",
  };
}

function cloneQuestion(question) {
  return JSON.parse(JSON.stringify(question));
}

function isSameJson(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function getQuestionUpdateErrorMessage(error) {
  const message = String(error?.message || "");
  if (message.includes("answer records") || message.includes("scoring fields")) {
    return "该题已有作答记录，只能修改题干、知识点、难度、解析、鼓励语等不影响评分历史的内容。";
  }
  return message || "题目修改失败，请稍后重试";
}

function formatCreatedAt(value) {
  const normalized = String(value || "").trim();
  if (!normalized) return "-";

  const hasTimezone = /(?:z|[+-]\d{2}:?\d{2})$/i.test(normalized);
  const normalizedUtcValue = normalized
    .replace(" ", "T")
    .replace(/(\.\d{3})\d+/, "$1");
  const parseValue = hasTimezone ? normalizedUtcValue : `${normalizedUtcValue}Z`;
  const date = new Date(parseValue);

  if (Number.isNaN(date.getTime())) {
    return normalized;
  }

  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    hourCycle: "h23",
  })
    .formatToParts(date)
    .reduce((result, part) => {
      result[part.type] = part.value;
      return result;
    }, {});

  return `${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
}

function formatTaskOption(task) {
  const title = String(task.title || "").trim();
  return title ? `${task.id} - ${title}` : `${task.id}`;
}

function normalizeGrade(value) {
  const normalized = String(value || "").trim().replace("年级", "");
  if (["6", "7", "8"].includes(normalized)) {
    return normalized;
  }
  return "";
}

function normalizeClassName(value) {
  const normalized = String(value || "").trim().replace(/班$/, "");
  if (["1", "2", "3", "4"].includes(normalized)) {
    return normalized;
  }
  return normalized;
}

function formatGrade(value) {
  const normalized = normalizeGrade(value);
  return normalized ? `${normalized}年级` : "-";
}

function getTaskStatusLabel(status) {
  if (status === "draft") return "草稿";
  if (status === "published") return "已发布";
  if (status === "archived") return "已归档";
  return status || "-";
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

async function scrollToSection(sectionRef) {
  await nextTick();
  sectionRef.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

onMounted(() => {
  void loadTeacherTasks();
});
</script>
