# Dify 自动创建任务并导入题目接口

## 接口

```http
POST /api/dify/tasks/create-with-questions?title=任务标题&grade=8
X-Dify-Token: 后端配置的密钥
Content-Type: application/json
```

该接口供 Dify HTTP 请求节点直接调用，用于一次性完成：

- 创建 `Task`
- 批量写入 `questions`
- 返回学生访问地址和教师分析地址

后端通过环境变量 `DIFY_API_TOKEN` 配置调用密钥。只有配置了 `DIFY_API_TOKEN` 时才会校验请求头 `X-Dify-Token`；未配置时接口会直接放行，方便本地或临时测试。部署到公网环境前建议务必配置该密钥。请求头不匹配时返回 `401`。

## Dify 配置方式

在 Dify HTTP 请求节点中：

- Method: `POST`
- URL: `http://你的后端地址/api/dify/tasks/create-with-questions?title={{title}}&grade={{grade}}`
- Headers:
  - `Content-Type: application/json`
  - `X-Dify-Token: 你的密钥`，如果服务器未配置 `DIFY_API_TOKEN`，该请求头可暂时不填
- Body: JSON，只需要放 `description` 和 `questions`

`title` 和 `grade` 推荐放在 URL query params 中。接口仍兼容旧格式：如果 URL 没传 `title` 或 `grade`，会尝试从 JSON body 中读取。

## 请求体

```json
{
  "description": "由 Dify 工作流根据教案、PPT 和学情自动生成",
  "questions": [
    {
      "knowledge_point": "物联网通信方式",
      "question_type": "single_choice",
      "difficulty": "easy",
      "stem": "蓝牙通信更适合下列哪种场景？",
      "options": [
        {
          "key": "A",
          "text": "远距离高速上网",
          "explanation": "蓝牙不适合远距离高速通信。"
        },
        {
          "key": "B",
          "text": "近距离低功耗设备连接",
          "explanation": "蓝牙适合近距离、低功耗通信。"
        }
      ],
      "correct_answer": ["B"],
      "accepted_answers": [],
      "encouragement": {
        "correct": "判断准确，你抓住了蓝牙近距离、低功耗的特点。",
        "wrong": "再想想蓝牙常见在哪些设备之间使用。"
      },
      "student_explanation": "蓝牙常用于耳机、鼠标、手环、键盘鼠标等近距离低功耗设备连接。",
      "score": 1
    }
  ]
}
```

字段校验：

- `title` 必填，推荐通过 URL query params 传入
- `grade` 必填，推荐通过 URL query params 传入
- `questions` 不能为空
- 每道题必须包含 `stem`、`question_type`、`correct_answer`
- `question_type` 支持 `judgment`、`single_choice`、`multiple_choice`、`blank`
- `difficulty` 支持 `easy`、`medium`、`hard`，不传时默认为 `medium`
- `options` 兼容 Dify 的 `key` 字段，也兼容系统原有的 `id` 字段
- `encouragement.retryCorrect`、`encouragement.retryWrong` 可不传，默认空字符串

## 返回体

```json
{
  "success": true,
  "task_id": 12,
  "title": "八年级《物联网通信方式》课末巩固练习",
  "grade": "8",
  "question_count": 5,
  "student_url": "/",
  "teacher_analysis_url": "/teacher/analysis/12",
  "message": "任务创建成功，已导入 5 道题。"
}
```

## 事务说明

创建任务和导入题目在同一个数据库事务中完成。如果题目导入过程中发生异常，后端会执行回滚，不会留下只创建任务但没有题目的半成品数据。

## curl 测试

启动后端：

```powershell
uvicorn main:app --reload
```

如果需要启用 token 校验，先配置：

```powershell
$env:DIFY_API_TOKEN="dev-dify-token"
```

调用接口：

```bash
curl -X POST "http://127.0.0.1:8000/api/dify/tasks/create-with-questions?title=%E5%85%AB%E5%B9%B4%E7%BA%A7%E3%80%8A%E7%89%A9%E8%81%94%E7%BD%91%E9%80%9A%E4%BF%A1%E6%96%B9%E5%BC%8F%E3%80%8B%E8%AF%BE%E6%9C%AB%E5%B7%A9%E5%9B%BA%E7%BB%83%E4%B9%A0&grade=8" \
  -H "Content-Type: application/json" \
  -H "X-Dify-Token: dev-dify-token" \
  -d '{
    "description": "由 Dify 工作流根据教案、PPT 和学情自动生成",
    "questions": [
      {
        "knowledge_point": "物联网通信方式",
        "question_type": "single_choice",
        "difficulty": "easy",
        "stem": "蓝牙通信更适合下列哪种场景？",
        "options": [
          {
            "key": "A",
            "text": "远距离高速上网",
            "explanation": "蓝牙不适合远距离高速通信。"
          },
          {
            "key": "B",
            "text": "近距离低功耗设备连接",
            "explanation": "蓝牙适合近距离、低功耗通信。"
          }
        ],
        "correct_answer": ["B"],
        "accepted_answers": [],
        "encouragement": {
          "correct": "判断准确，你抓住了蓝牙近距离、低功耗的特点。",
          "wrong": "再想想蓝牙常见在哪些设备之间使用。"
        },
        "student_explanation": "蓝牙常用于耳机、鼠标、手环、键盘鼠标等近距离低功耗设备连接。",
        "score": 1
      }
    ]
  }'
```
