# 课堂答题与学情分析系统

这是一个面向课堂巩固练习场景的全栈项目。系统支持教师创建练习任务、导入题目和学生名单，学生通过学号进入练习并逐题作答，后台自动判分并生成学情分析与教学摘要。

## 功能概览

- 学生端：学号识别、任务列表、逐题练习、即时反馈、再次尝试、查看答案、练习总结、学习详情。
- 教师端：任务管理、题目 JSON 导入、学生名单 CSV 导入、题目编辑与删除、学情分析、教学摘要复制。
- 后端能力：自动判分、作答记录保存、学生进度统计、题目正确率统计、选项分布统计、薄弱题目提取。
- AI/Dify 对接：当前主要接收外部 AI 或 Dify 工作流生成后的结构化题目 JSON；后端提供 Dify 创建任务并导入题目的接口。

## 技术栈

### 后端

- FastAPI
- SQLAlchemy 2.x
- Pydantic 2.x
- SQLite
- Uvicorn

### 前端

- Vue 3
- Vue Router
- Vite
- 原生 `fetch`

## 项目结构

```text
quiz-sys/
├─ backend/
│  ├─ api/              # FastAPI 路由
│  ├─ core/             # 数据库与通用工具
│  ├─ models/           # SQLAlchemy 数据模型
│  ├─ schemas/          # Pydantic 请求/响应结构
│  ├─ services/         # 判分、分析、学习记录等业务逻辑
│  ├─ docs/             # 后端说明文档
│  ├─ main.py           # 后端入口
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ api/           # 前端接口封装
│  │  ├─ pages/         # 页面组件
│  │  ├─ router/        # 路由配置
│  │  ├─ App.vue
│  │  ├─ main.js
│  │  └─ style.css
│  ├─ docs/             # 前端说明文档
│  ├─ package.json
│  └─ vite.config.js
└─ README.md
```

## 本地运行

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

后端默认运行在：

```text
http://127.0.0.1:8000
```

FastAPI 文档地址：

```text
http://127.0.0.1:8000/docs
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在：

```text
http://localhost:5173
```

前端 Vite 已配置 `/api` 代理到后端 `http://127.0.0.1:8000`。

## 数据库

当前使用 SQLite，默认数据库连接为：

```text
sqlite:///./app.db
```

后端启动时会自动创建基础数据表，并执行少量 SQLite 兼容字段补齐逻辑。当前适合原型验证和本地开发；如果用于正式部署，建议后续迁移到 MySQL 或 PostgreSQL，并引入 Alembic 管理数据库迁移。

## 主要页面

- `/student`：学生入口与任务列表
- `/practice/:taskId`：学生答题页
- `/student/tasks/:taskId/summary`：学生单个任务学习详情
- `/teacher/tasks`：教师任务管理
- `/teacher/analysis/:taskId`：教师学情分析

## 主要接口

### 学生端

```http
GET /api/student/tasks?student_id=20300101
GET /api/student/tasks/{task_id}/summary?student_id=20300101
POST /api/tasks/{task_id}/questions/{question_pk}/submit
```

### 教师端

```http
GET /api/teacher/tasks
POST /api/teacher/tasks
PATCH /api/teacher/tasks/{task_id}
DELETE /api/teacher/tasks/{task_id}
POST /api/teacher/tasks/{task_id}/questions/import
PATCH /api/teacher/tasks/{task_id}/questions/{question_pk}
DELETE /api/teacher/tasks/{task_id}/questions/{question_pk}
POST /api/teacher/students/import
POST /api/teacher/students/import-csv
GET /api/teacher/students
```

### 题目与分析

```http
GET /api/tasks/{task_id}/questions
GET /api/tasks/{task_id}/analysis
GET /api/tasks/{task_id}/teaching-summary
```

### Dify/外部工作流

```http
POST /api/dify/tasks/create-with-questions
```

如果设置了环境变量 `DIFY_API_TOKEN`，调用该接口时需要在请求头中携带：

```http
X-Dify-Token: <token>
```

## 题目 JSON 格式示例

导入题目时，每道题大致包含以下字段：

```json
{
  "knowledge_point": "变量与赋值",
  "question_type": "single_choice",
  "difficulty": "easy",
  "stem": "下面哪个符号常用于赋值？",
  "options": [
    {
      "id": "A",
      "text": "=",
      "explanation": "在许多编程语言中，= 用于赋值。"
    }
  ],
  "correct_answer": ["A"],
  "accepted_answers": [],
  "encouragement": {
    "correct": "答对了。",
    "wrong": "再想想赋值语句的写法。",
    "retryCorrect": "修正成功。",
    "retryWrong": "可以查看答案并复盘。"
  },
  "student_explanation": "赋值语句通常把右侧的值保存到左侧变量中。",
  "score": 1
}
```

支持的题型：

- `judgment`：判断题
- `single_choice`：单选题
- `multiple_choice`：多选题
- `blank`：填空题

支持的难度：

- `easy`
- `medium`
- `hard`


## 常用命令

前端构建：

```bash
cd frontend
npm run build
```

后端导入检查：

```bash
cd backend
python -c "import main; print('backend import ok')"
```
