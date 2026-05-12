import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../pages/HomePage.vue";
import PracticePage from "../pages/PracticePage.vue";
import StudentTaskSummaryPage from "../pages/StudentTaskSummaryPage.vue";
import TeacherAnalysisPage from "../pages/TeacherAnalysisPage.vue";
import TeacherTasksPage from "../pages/TeacherTasksPage.vue";
import { clearExpiredStudentStorage } from "../utils/studentStorageTimeout";

const routes = [
  // {
  //   path: "/",
  //   redirect: { name: "home" },
  // },
  {
    path: "/student",
    name: "home",
    component: HomePage,
    meta: { title: "学生端 - 课堂巩固练习" },
  },
  {
    path: "/practice/:taskId",
    name: "practice",
    component: PracticePage,
    meta: { title: "学生答题 - 课堂巩固练习" },
  },
  {
    path: "/student/tasks/:taskId/summary",
    name: "student-task-summary",
    component: StudentTaskSummaryPage,
    meta: { title: "学习详情 - 课堂巩固练习" },
  },
  {
    path: "/teacher/analysis/:taskId",
    name: "teacher-analysis",
    component: TeacherAnalysisPage,
    meta: { title: "教师学情分析 - 课堂巩固练习" },
  },
  {
    path: "/teacher/tasks",
    name: "teacher-tasks",
    component: TeacherTasksPage,
    meta: { title: "教师任务管理 - 课堂巩固练习" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const expired = clearExpiredStudentStorage();
  const isStudentIdentityPage = to.name === "practice" || to.name === "student-task-summary";

  if (expired && isStudentIdentityPage) {
    return { name: "home", replace: true };
  }

  return true;
});

router.afterEach((to) => {
  document.title = to.meta?.title || "课堂巩固练习";
});

export default router;

