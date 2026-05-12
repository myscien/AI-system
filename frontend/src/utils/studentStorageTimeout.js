const STUDENT_QUERY_LOCK_STORAGE_KEY = "studentQueryLock";
const STUDENT_STORAGE_TIMEOUT_MS = 20 * 60 * 1000;
const STUDENT_STORAGE_TIMEOUT_EVENT = "student-storage-timeout";

let studentStorageTimeoutId = null;

function getLockedAtTime() {
  const raw = localStorage.getItem(STUDENT_QUERY_LOCK_STORAGE_KEY);
  if (!raw) return null;

  try {
    const record = JSON.parse(raw);
    const lockedAt = new Date(record?.locked_at).getTime();
    return Number.isNaN(lockedAt) ? null : lockedAt;
  } catch {
    return null;
  }
}

function dispatchStudentStorageTimeout() {
  window.dispatchEvent(new CustomEvent(STUDENT_STORAGE_TIMEOUT_EVENT));
}

export function clearExpiredStudentStorage() {
  const lockedAt = getLockedAtTime();
  if (!lockedAt) return false;

  if (Date.now() - lockedAt < STUDENT_STORAGE_TIMEOUT_MS) {
    return false;
  }

  localStorage.clear();
  return true;
}

export function scheduleStudentStorageTimeout() {
  if (studentStorageTimeoutId) {
    window.clearTimeout(studentStorageTimeoutId);
    studentStorageTimeoutId = null;
  }

  if (clearExpiredStudentStorage()) {
    dispatchStudentStorageTimeout();
    return true;
  }

  const lockedAt = getLockedAtTime();
  if (!lockedAt) return false;

  const remainingMs = Math.max(STUDENT_STORAGE_TIMEOUT_MS - (Date.now() - lockedAt), 0);
  studentStorageTimeoutId = window.setTimeout(() => {
    localStorage.clear();
    studentStorageTimeoutId = null;
    dispatchStudentStorageTimeout();
  }, remainingMs);

  return true;
}

export function listenStudentStorageTimeout(handler) {
  window.addEventListener(STUDENT_STORAGE_TIMEOUT_EVENT, handler);
  return () => window.removeEventListener(STUDENT_STORAGE_TIMEOUT_EVENT, handler);
}
