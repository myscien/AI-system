import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import {
  listenStudentStorageTimeout,
  scheduleStudentStorageTimeout,
} from "./utils/studentStorageTimeout";

scheduleStudentStorageTimeout();
listenStudentStorageTimeout(() => {
  const currentRoute = router.currentRoute.value;
  if (currentRoute.name === "practice" || currentRoute.name === "student-task-summary") {
    router.replace({ name: "home" });
  }
});
createApp(App).use(router).mount("#app");

