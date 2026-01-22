# PPTAS 系统快速使用指南

## 简介

PPTAS（PPT 智能扩展系统）是一个 AI 驱动的学习辅助工具，能够自动分析 PPT 文档，生成学习笔记和补充说明。

## 快速开始

### 1. 环境要求

- Python 3.9+
- Node.js 16.0+
- 为支持 PPTX 文件的预览功能，需要安装 LibreOffice：
  - Windows: 从 https://www.libreoffice.org/ 下载并安装（请不要变更下载位置，保持默认安全路径）
  - Linux: `sudo apt-get install libreoffice` 或 `sudo yum install libreoffice`
  - Mac: `brew install --cask libreoffice`  
  
  安装后，系统会自动检测 LibreOffice 并将 PPTX 文件转换为 PDF 以便在前端显示预览。

### 2. 安装步骤

#### 后端安装

```bash
cd backend
pip install -r requirements.txt
```

#### 前端安装

```bash
cd frontend
npm install
```

#### 配置 LLM

编辑 `backend/config.json`:

```json
{
  "llm": {
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  }
}
```

### 3. 启动服务

#### 启动后端

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动前端

```bash
cd frontend
npm run dev
```

访问地址: http://localhost:5173

### 4. 使用 Docker（推荐）

```bash
docker-compose up --build -d
```

访问:  
```
# 启动容器
docker-compose up --build -d

# 访问应用
# 前端：http://localhost
# 后端 API：http://localhost:8000/docs

# 查看日志
docker-compose logs -f backend

# 停止容器
docker-compose down
```

## 基本使用

### 步骤 1: 上传文档

1. 打开前端界面
2. 点击上传区域
3. 选择 PPTX 或 PDF 文件

### 步骤 2: 全局分析（可选）

1. 点击"全局分析"按钮
2. 等待分析完成
3. 查看文档主题和知识点框架

### 步骤 3: 单页分析

1. 选择要分析的页面
2. 点击"使用 AI 深度分析此页面"
3. 实时查看分析进度
4. 查看分析结果

## 分析结果说明

- **知识聚类**: 识别难以理解的概念
- **学习笔记**: 结构化的 Markdown 笔记
- **知识缺口**: 需要补充的知识点
- **补充说明**: 为缺口生成的详细说明
- **参考资料**: 从外部知识源检索的资料

## 配置说明

### LLM 配置

编辑 `backend/config.json`:

```json
{
  "llm": {
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  }
}
```

### 支持的 LLM 提供商

- OpenAI: `base_url: "https://api.openai.com/v1"`, `model: "gpt-4"`
- SiliconFlow: `base_url: "https://api.siliconflow.cn/v1"`, `model: "deepseek-ai/DeepSeek-V3.2-Exp"`

## 常见问题

### Q: 如何配置不同的 LLM？

A: 修改 `config.json` 中的 `llm.base_url` 和 `llm.model`

### Q: 分析结果保存在哪里？

A: 保存在 `backend/pptas_cache.sqlite3` 数据库中

### Q: 如何强制重新分析？

A: 在 API 请求中设置 `force: true`，或在前端点击"重新分析"按钮

### Q: 如何查看分析历史？

A: 系统会自动加载缓存的分析结果，无需手动查询

## 获取帮助

- 详细文档: 查看 `USER_GUIDE_DETAILED.md`
- 技术文档: 查看 `TECHNICAL_REPORT.md`
- API 文档: 访问 http://localhost:8000/docs
