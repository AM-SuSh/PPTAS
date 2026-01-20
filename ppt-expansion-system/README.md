# PPT 智能扩展系统 - 配置与部署指南

## 📋 目录结构

```
ppt-expansion-system/
├── ppt_expansion_system.py      # 核心系统架构
├── mcp_tools.py                  # MCP 工具集成
├── streaming_demo.py             # 完整使用示例
├── config.json                   # 配置文件
├── requirements.txt              # 依赖项
├── knowledge_sources/            # 本地知识库文件夹
│   ├── textbooks/
│   ├── papers/
│   └── notes/
├── knowledge_base/               # 向量数据库存储
└── outputs/                      # 输出文件夹
```

## 🔧 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.20
langgraph>=0.0.20
chromadb>=0.4.22
pydantic>=2.5.0
python-pptx>=0.6.21
beautifulsoup4>=4.12.0
requests>=2.31.0
PyPDF2>=3.0.0
```

### 2. 配置 config.json

```json
{
  "llm": {
    "api_key": "your-api-key-here",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  },
  "retrieval": {
    "preferred_sources": ["arxiv", "wikipedia"],
    "max_results": 3,
    "local_rag_priority": true
  },
  "expansion": {
    "max_revisions": 2,
    "min_gap_priority": 3,
    "temperature": 0.7
  },
  "streaming": {
    "enabled": true,
    "chunk_size": 50
  },
  "knowledge_base": {
    "path": "./knowledge_base",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

### 3. 环境变量设置

创建 `.env` 文件：
```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 可选：其他 LLM 提供商
# ANTHROPIC_API_KEY=...
# AZURE_OPENAI_ENDPOINT=...
```

## 🚀 快速开始

### 基础使用

```python
from streaming_demo import PPTExpansionPipeline

# 初始化
pipeline = PPTExpansionPipeline("config.json")

# 准备 PPT 文本
ppt_texts = [
    "第1页：主题介绍...",
    "第2页：核心概念...",
    "第3页：应用示例..."
]

# 运行
result = pipeline.run(ppt_texts)

# 导出
pipeline.export_to_markdown(result, "output.md")
```

### 从文件加载

```python
# 加载 PPTX 文件
ppt_texts = pipeline.load_ppt("lecture.pptx")

# 运行流程
result = pipeline.run(ppt_texts)
```

### 流式处理

```python
import asyncio

async def process_streaming():
    pipeline = PPTExpansionPipeline()
    ppt_texts = [...]
    
    async for chunk in pipeline.run_streaming(ppt_texts):
        print(chunk, end="", flush=True)

asyncio.run(process_streaming())
```

## 📚 知识库管理

### 添加本地文档

```python
from streaming_demo import KnowledgeBaseManager

kb_manager = KnowledgeBaseManager()

# 从文件夹批量添加
docs = kb_manager.add_documents_from_folder("./knowledge_sources/textbooks")

# 查看统计
stats = kb_manager.get_stats()
print(f"总文档数: {stats['total_documents']}")
```

### 支持的文档格式

- `.txt` - 纯文本
- `.md` - Markdown
- `.pdf` - PDF 文档
- `.pptx` - PowerPoint（需要额外解析）

## 🔍 MCP 工具配置

### 配置搜索源优先级

```python
# 在 config.json 中
{
  "retrieval": {
    "preferred_sources": ["arxiv", "wikipedia", "baike"],
    "source_weights": {
      "arxiv": 1.0,
      "wikipedia": 0.8,
      "baike": 0.6
    }
  }
}
```

### 使用特定搜索源

```python
from mcp_tools import MCPRouter

router = MCPRouter()

# 仅使用学术源
results = router.search("transformer attention", preferred_sources=["arxiv"])

# 仅使用百科源
results = router.search("深度学习", preferred_sources=["wikipedia", "baike"])
```

## ⚙️ 高级配置

### 自定义 Agent 参数

```python
from ppt_expansion_system import LLMConfig, StructureUnderstandingAgent

config = LLMConfig(
    api_key="...",
    base_url="...",
    model="gpt-4"
)

# 创建自定义 Agent
agent = StructureUnderstandingAgent(config)

# 修改 temperature
agent.llm.temperature = 0.3
```

### 调整校验严格度

```python
# 在 GraphState 中设置
initial_state = {
    "max_revisions": 3,  # 最多修订3次
    "check_threshold": 0.8,  # 校验通过阈值
    ...
}
```

## 📊 性能优化

### 1. 向量数据库优化

```python
# 增加检索数量
retrieval_agent.vectorstore.similarity_search(query, k=5)

# 使用 MMR（最大边际相关性）
retrieval_agent.vectorstore.max_marginal_relevance_search(query, k=5)
```

### 2. 并行处理知识单元

```python
from concurrent.futures import ThreadPoolExecutor

def process_unit(unit):
    # 处理单个知识单元
    return pipeline.process_knowledge_unit(unit)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_unit, knowledge_units))
```

### 3. 批量 LLM 调用

```python
# 使用 LangChain 的批处理
from langchain.schema.runnable import RunnableLambda

batch_chain = RunnableLambda(lambda x: [
    expansion_agent.run(gap) for gap in x
])

results = batch_chain.batch(knowledge_gaps)
```

## 🐛 调试与监控

### 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ppt_expansion")

# 在 Agent 中添加日志
logger.debug(f"处理知识缺口: {gap.concept}")
```

### 使用 LangSmith 追踪

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
export LANGCHAIN_API_KEY=your-langsmith-key
export LANGCHAIN_PROJECT=ppt-expansion
```

## 🔐 安全性建议

1. **API Key 管理**
   - 使用环境变量存储 API Key
   - 不要将 config.json 提交到版本控制

2. **输入验证**
   ```python
   def validate_ppt_text(text: str) -> bool:
       # 检查文本长度
       if len(text) > 10000:
           return False
       # 检查敏感内容
       # ...
       return True
   ```

3. **速率限制**
   ```python
   from ratelimit import limits, sleep_and_retry
   
   @sleep_and_retry
   @limits(calls=10, period=60)
   def call_llm(prompt):
       # 限制每分钟10次调用
       pass
   ```

## 📖 使用示例

### 示例 1：处理机器学习课程 PPT

```python
# 加载 PPT
ppt_texts = pipeline.load_ppt("ml_lecture.pptx")

# 配置倾向学术源
config_manager.config["retrieval"]["preferred_sources"] = ["arxiv", "scholar"]

# 运行
result = pipeline.run(ppt_texts)

# 查看扩展的知识点
for content in result["expanded_content"]:
    print(f"{content.concept} - {content.gap_type}")
    print(content.content)
```

### 示例 2：批量处理多个 PPT

```python
import glob

ppt_files = glob.glob("lectures/*.pptx")

for ppt_file in ppt_files:
    print(f"处理: {ppt_file}")
    ppt_texts = pipeline.load_ppt(ppt_file)
    result = pipeline.run(ppt_texts)
    
    # 导出到对应文件
    output_name = f"output_{Path(ppt_file).stem}.md"
    pipeline.export_to_markdown(result, output_name)
```

### 示例 3：集成到 Web 应用

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
pipeline = PPTExpansionPipeline()

@app.route('/expand', methods=['POST'])
def expand_ppt():
    data = request.json
    ppt_texts = data.get('ppt_texts', [])
    
    result = pipeline.run(ppt_texts)
    
    return jsonify({
        'success': True,
        'ppt_id': result['ppt_id'],
        'final_notes': result['final_notes'],
        'stats': result['stats']
    })

@app.route('/stream-expand', methods=['POST'])
async def stream_expand():
    # 流式响应
    async def generate():
        async for chunk in pipeline.run_streaming(ppt_texts):
            yield f"data: {chunk}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
```

## 🧪 测试

### 单元测试示例

```python
import unittest

class TestPPTExpansion(unittest.TestCase):
    def setUp(self):
        self.pipeline = PPTExpansionPipeline("test_config.json")
    
    def test_structure_understanding(self):
        ppt_text = "Self-Attention: Q, K, V matrices"
        # 测试结构理解
        # ...
    
    def test_gap_identification(self):
        # 测试缺口识别
        # ...

if __name__ == '__main__':
    unittest.main()
```

## 📞 故障排查

### 常见问题

1. **向量数据库初始化失败**
   - 检查 chromadb 版本兼容性
   - 确保 knowledge_base 目录有写权限

2. **MCP 工具搜索失败**
   - 检查网络连接
   - 验证 API 配额

3. **LLM 调用超时**
   - 增加 max_retries
   - 调整 timeout 参数

## 📝 更新日志

- **v1.0.0** - 初始版本
  - 完整的 6-step Agent 流程
  - 支持本地 RAG 和 MCP 工具
  - 流式输出支持

---

**更多信息**: 查看项目 README.md 和代码注释