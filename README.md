# Media AI Agent

长视频/音频 语音转文字 + OCR + 摘要 + 关键词 AI Agent，基于 FastAPI + ffmpeg + 大模型 API。

## 目录结构

```
media_ai_agent/
├── app/
│   ├── agents/          # pipeline_agent.py  — 全流程编排
│   ├── api/
│   │   ├── main.py      — FastAPI app 入口
│   │   └── routes/      — upload / jobs / pages
│   ├── core/            — config / logger / constants
│   ├── prompts/         — OCR / merge / summary / keyword 提示词
│   ├── schemas/         — Pydantic 数据结构
│   ├── services/        — storage / media / audio / frame / ocr / asr / llm / result
│   └── web/             — templates/index.html + static/app.js + style.css
├── storage/             — 运行时文件（上传、音频、帧、结果）
├── run.py               — 启动入口
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
cd media_ai_agent
pip install -r requirements.txt
```

系统依赖（需要 ffmpeg）：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写 API Key：

```env
OCR_API_KEY=sk-xxx     # 支持 OpenAI / 兼容接口
ASR_API_KEY=sk-xxx
LLM_API_KEY=sk-xxx
```

如使用第三方兼容接口，修改对应的 `*_API_BASE` 和 `*_MODEL`。

### 3. 启动

```bash
python run.py
```

浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 4. 使用

1. 拖拽或点击上传音频/视频文件
2. 点击「开始处理」
3. 页面自动轮询处理状态
4. 完成后点击「查看结果」查看：音频播放器、视频帧、ASR 文字、OCR 文字、合并文本、摘要、关键词

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传文件，返回 JobResult |
| GET  | `/api/jobs` | 列出所有任务 |
| GET  | `/api/jobs/{job_id}` | 查询单个任务状态/结果 |
| GET  | `/files/...` | 访问静态媒体文件 |

## 流程说明

```
用户上传文件
    │
    ├─ 视频 ─┬─ ffmpeg 提取音频 ──► ASR (语音识别 API，分块处理)
    │        └─ ffmpeg 抽帧    ──► OCR (视觉 API，逐帧识别)
    │
    └─ 音频 ────────────────────► ASR (语音识别 API，分块处理)

                    ASR 文本 + OCR 文本
                          │
                    LLM 融合/去重 → merged_text
                          │
                    LLM 摘要     → summary
                          │
                    LLM 关键词   → keywords
```

## 配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FRAME_INTERVAL_SEC` | 5 | 每隔 N 秒抽一帧 |
| `AUDIO_CHUNK_SEC` | 60 | 音频分块大小（秒）|
| `OCR_MODEL` | gpt-4o | 支持图像输入的模型 |
| `ASR_MODEL` | whisper-1 | 语音识别模型 |
| `LLM_MODEL` | gpt-4o | 文本融合/摘要模型 |
