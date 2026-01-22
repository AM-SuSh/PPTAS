"""优化后的 PPT 扩展系统 Agent 实现"""

from typing import List, Dict, Any
import json
import requests
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, StructuredOutputParser, ResponseSchema
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from .models import (
    PageStructure,
    KnowledgeGap,
    ExpandedContent,
    CheckResult,
    KnowledgeUnit,
    GraphState,
)


# ==================== 配置管理 ====================
class LLMConfig:
    """LLM 配置"""
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def create_llm(self, temperature: float = 0.5) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            max_retries=3,
            temperature=temperature
        )


# ==================== 工具函数 ====================
def test_url_connectivity(url: str, timeout: int = 3) -> bool:
    """测试URL连通性"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False


# ==================== Step 0-A: 全局结构解析 Agent (简化版) ====================
class GlobalStructureAgent:
    """全局结构解析 Agent - 提取整体知识框架"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
    
    def run(self, state: GraphState) -> GraphState:
        """执行全局结构解析"""
        # 改进的 prompt: 更明确的要求
        template = """你是一个教育专家，需要分析这份PPT/PDF文档的整体结构和知识框架。

文档内容（共{total_pages}页）:
{ppt_texts}

请仔细分析整个文档，提取以下信息：

1. **主题**：整个文档的核心主题是什么？
2. **章节结构**：文档分为哪些主要章节？每个章节包含哪些页面？
3. **知识逻辑流程**：这些章节之间的知识逻辑关系是什么？

请以JSON格式输出，格式如下：
{{
  "main_topic": "文档的核心主题（必须填写，不能为空）",
  "chapters": [
    {{
      "title": "章节标题",
      "pages": [页码列表，例如[1,2,3]],
      "key_concepts": ["核心概念1", "核心概念2"]
    }}
  ],
  "knowledge_flow": "知识逻辑流程的简要描述（50字内）"
}}

重要要求：
- main_topic 必须填写，不能为空或"未知"
- 至少识别1-3个主要章节
- 只返回JSON，不要其他文字说明
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        # 改进：传递更多文本内容，但限制总长度
        ppt_texts = state["ppt_texts"]
        total_pages = len(ppt_texts)
        
        # 如果页数太多，只取前几页和后几页，以及中间几页的摘要
        if total_pages > 20:
            # 取前5页、后5页，中间每5页取1页
            selected_indices = list(range(min(5, total_pages)))
            for i in range(5, total_pages - 5, 5):
                selected_indices.append(i)
            selected_indices.extend(range(max(total_pages - 5, 5), total_pages))
            selected_texts = [ppt_texts[i] for i in selected_indices if i < len(ppt_texts)]
            ppt_summary = "\n\n".join([
                f"第{i+1}页:\n{text[:500]}" for i, text in enumerate(selected_texts)
            ])
            ppt_summary += f"\n\n[注：文档共{total_pages}页，此处显示了{len(selected_texts)}页的内容]"
        else:
            # 页数不多，传递所有内容，但每页限制长度
            ppt_summary = "\n\n".join([
                f"第{i+1}页:\n{text[:800]}" for i, text in enumerate(ppt_texts)
            ])
        
        print(f"📝 发送给LLM的文本长度: {len(ppt_summary)} 字符")
        response = chain.invoke({"ppt_texts": ppt_summary, "total_pages": total_pages})
        
        print(f"📥 LLM返回的原始内容: {response.content[:500]}...")
        
        try:
            # 尝试提取JSON（可能包含markdown代码块）
            content = response.content.strip()
            # 如果包含```json，提取其中的内容
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            
            result = json.loads(content)
            
            # 验证结果
            if not result.get("main_topic") or result.get("main_topic") == "未知":
                print("⚠️  LLM返回的主题为空或'未知'，尝试从内容推断...")
                # 尝试从第一页标题推断主题
                if ppt_texts and len(ppt_texts) > 0:
                    first_page = ppt_texts[0]
                    if "标题:" in first_page:
                        inferred_topic = first_page.split("标题:")[1].split("\n")[0].strip()
                        if inferred_topic:
                            result["main_topic"] = inferred_topic
                            print(f"✅ 从第一页标题推断主题: {inferred_topic}")
            
            print(f"✅ 解析成功: 主题={result.get('main_topic', '未知')}, 章节数={len(result.get('chapters', []))}")
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"   原始内容: {response.content[:500]}")
            # 尝试从内容推断基本信息
            result = {"main_topic": "未知", "chapters": [], "knowledge_flow": ""}
            if ppt_texts and len(ppt_texts) > 0:
                first_page = ppt_texts[0]
                if "标题:" in first_page:
                    inferred_topic = first_page.split("标题:")[1].split("\n")[0].strip()
                    if inferred_topic:
                        result["main_topic"] = inferred_topic
                        print(f"✅ 从第一页标题推断主题: {inferred_topic}")
        
        state["global_outline"] = result
        return state


# ==================== Step 0-B: 知识点划分 Agent (全局视角) ====================
class KnowledgeClusteringAgent:
    """知识点划分 Agent - 从全局PPT提取知识单元"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.2)
    
    def run(self, state: GraphState) -> GraphState:
        """执行知识点聚类 - 从全局视角"""
        # 改进的 prompt: 更明确的要求和更好的格式
        global_outline = state.get("global_outline", {})
        main_topic = global_outline.get("main_topic", "未知")
        
        template = """你是学习专家，需要从整个PPT/PDF文档中提取核心知识点。

文档主题: {main_topic}

文档结构:
{global_outline}

文档内容（共{total_pages}页）:
{ppt_texts}

任务: 从整个文档中提取核心知识点单元
要求:
1. 识别文档中最重要的核心概念（至少5个）
2. 每个知识点应该：
   - 有明确的名称
   - 标注涉及的页码
   - 说明为什么学生可能不理解
   - 指出需要补充什么内容

输出JSON数组，格式如下:
[
  {{
    "concept": "概念名称（必须填写）",
    "pages": [页码列表，例如[1,2,3]],
    "why_difficult": "为什么学生可能不理解（20字内）",
    "补充方向": "需要补充什么（例如:原理/示例/背景/公式推导）"
  }}
]

重要要求:
- 必须至少提取5个核心知识点
- concept字段不能为空
- pages字段必须是数字数组
- 只返回JSON数组，不要其他文字说明
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        # 改进：如果页数太多，使用摘要
        ppt_texts = state["ppt_texts"]
        total_pages = len(ppt_texts)
        
        if total_pages > 15:
            # 使用摘要：每页取前500字符
            ppt_summary = "\n\n".join([
                f"第{i+1}页:\n{text[:500]}..." for i, text in enumerate(ppt_texts)
            ])
        else:
            # 页数不多，传递完整内容
            ppt_summary = "\n\n".join([
                f"第{i+1}页:\n{text[:1000]}" for i, text in enumerate(ppt_texts)
            ])
        
        print(f"📝 发送给LLM的文本长度: {len(ppt_summary)} 字符")
        response = chain.invoke({
            "main_topic": main_topic,
            "global_outline": json.dumps(global_outline, ensure_ascii=False, indent=2),
            "ppt_texts": ppt_summary,
            "total_pages": total_pages
        })
        
        print(f"📥 LLM返回的原始内容: {response.content[:500]}...")
        
        try:
            # 尝试提取JSON
            content = response.content.strip()
            # 如果包含```json，提取其中的内容
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            
            concepts_data = json.loads(content)
            
            # 验证和过滤
            valid_concepts = []
            for concept in concepts_data:
                if concept.get("concept") and concept.get("concept").strip():
                    # 确保pages是列表
                    pages = concept.get("pages", [])
                    if not isinstance(pages, list):
                        pages = []
                    valid_concepts.append({
                        "concept": concept.get("concept", "").strip(),
                        "pages": pages,
                        "why_difficult": concept.get("why_difficult", ""),
                        "补充方向": concept.get("补充方向", "")
                    })
            
            print(f"✅ 解析成功: 提取到 {len(valid_concepts)} 个有效知识点")
            
            # 转换为 KnowledgeUnit 格式
            knowledge_units = []
            for i, concept in enumerate(valid_concepts[:15]):  # 最多15个
                pages = concept.get("pages", [])
                # 确保页码有效
                valid_pages = [p for p in pages if isinstance(p, int) and 0 < p <= total_pages]
                if not valid_pages:
                    # 如果没有有效页码，尝试从概念名称推断
                    # 这里可以添加更智能的推断逻辑
                    valid_pages = []
                
                knowledge_units.append(KnowledgeUnit(
                    unit_id=f"unit_{i+1}",
                    title=concept.get("concept", ""),
                    pages=valid_pages,
                    core_concepts=[concept.get("concept", "")],
                    raw_texts=[state["ppt_texts"][p-1] for p in valid_pages if 0 < p <= len(state["ppt_texts"])]
                ))
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"   原始内容: {response.content[:500]}")
            knowledge_units = []
        
        print(f"✅ 最终生成 {len(knowledge_units)} 个知识点单元")
        state["knowledge_units"] = knowledge_units
        return state


# ==================== Step 1: 结构语义理解 Agent (简化) ====================
class StructureUnderstandingAgent:
    """结构语义理解 Agent - 生成学生理解笔记"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.5)
    
    def run(self, state: GraphState) -> GraphState:
        """执行结构语义理解和笔记生成（基于全局上下文）"""
        # 检查是否有全局上下文
        has_global_context = state.get("global_outline") and state.get("knowledge_units")
        
        if has_global_context:
            # 有全局上下文时，使用增强的prompt
            template = """基于整个文档的全局分析结果，为学生生成结构化学习笔记(Markdown格式，300字内):

文档全局信息:
- 主题: {main_topic}
- 知识逻辑流程: {knowledge_flow}
- 当前页面在全局知识体系中的位置: {page_context}

当前页面内容: {raw_text}

笔记格式:
## [页面主题]

### 核心概念
- 概念1: 简要说明（结合全局知识框架）
- 概念2: 简要说明

### 关键要点
- 要点1
- 要点2

### 重点理解
[简洁的理解要点，说明在当前页面在整个文档知识体系中的位置]

要求:
- 结合全局知识框架，突出最重要的概念
- 说明当前页面与整体知识体系的关系
- 标注学生应该掌握的要点
- 适合快速复习
"""
            # 构建页面上下文信息
            page_id = state.get("current_page_id", 0)
            page_context = f"第{page_id}页"
            if state.get("global_outline", {}).get("chapters"):
                for chapter in state["global_outline"]["chapters"]:
                    if page_id in chapter.get("pages", []):
                        page_context = f"第{page_id}页，属于章节：{chapter.get('title', '')}"
                        break
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "main_topic": state.get("global_outline", {}).get("main_topic", "未知"),
                "knowledge_flow": state.get("global_outline", {}).get("knowledge_flow", ""),
                "page_context": page_context,
                "raw_text": state["raw_text"][:1000]
            })
        else:
            # 没有全局上下文时，使用原始prompt
            template = """根据以下内容，为学生生成结构化学习笔记(Markdown格式，300字内):

内容: {raw_text}

笔记格式:
## [页面主题]

### 核心概念
- 概念1: 简要说明
- 概念2: 简要说明

### 关键要点
- 要点1
- 要点2

### 重点理解
[简洁的理解要点]

要求:
- 突出最重要的概念
- 标注学生应该掌握的要点
- 适合快速复习
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            response = chain.invoke({"raw_text": state["raw_text"][:1000]})  # 限制输入长度
        
        # 生成学习笔记
        understanding_notes = response.content
        
        # 同时提取页面结构信息
        structure_template = """提取页面的结构化信息(JSON格式):

内容: {raw_text}

{{
  "title": "页面标题",
  "main_concepts": ["核心概念1", "核心概念2"],
  "key_points": ["要点1", "要点2"]
}}

仅返回JSON，不要其他内容。
"""
        structure_prompt = ChatPromptTemplate.from_template(structure_template)
        structure_chain = structure_prompt | self.llm
        
        structure_response = structure_chain.invoke({"raw_text": state["raw_text"][:800]})
        
        try:
            structure_data = json.loads(structure_response.content)
            page_structure = {
                "page_id": state.get("current_page_id", 0),
                "title": structure_data.get("title", ""),
                "main_concepts": structure_data.get("main_concepts", []),
                "key_points": structure_data.get("key_points", []),
                "relationships": {},
                "teaching_goal": ""
            }
        except:
            page_structure = {
                "page_id": 0, 
                "title": "", 
                "main_concepts": [], 
                "key_points": [], 
                "relationships": {}, 
                "teaching_goal": ""
            }
        
        state["page_structure"] = page_structure
        state["understanding_notes"] = understanding_notes
        return state


# ==================== Step 2: 知识缺口识别 Agent (针对学生) ====================
class GapIdentificationAgent:
    """知识缺口识别 Agent - 识别学生理解障碍"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.2)
    
    def _parse_partial_json(self, text: str) -> List[Dict]:
        """手动解析部分JSON，提取有效的对象（使用正则表达式）"""
        import re
        gaps = []
        
        if not text or not text.strip():
            return gaps
        
        # 移除markdown代码块标记
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*$', '', text)
        text = text.strip()
        
        # 方法1: 查找完整的JSON对象 { "concept": "...", "gap_type": "...", "priority": ... }
        # 支持多行和可能的截断，更宽松的模式
        pattern1 = r'\{\s*"concept"\s*:\s*"([^"]+)"\s*,\s*"gap_type"\s*:\s*"([^"]+)"\s*,\s*"priority"\s*:\s*(\d+)'
        
        matches = re.finditer(pattern1, text, re.DOTALL)
        for match in matches:
            try:
                concept = match.group(1).strip()
                gap_type = match.group(2).strip()
                priority = int(match.group(3))
                
                if concept and gap_type:
                    gaps.append({
                        "concept": concept,
                        "gap_type": gap_type,
                        "priority": max(1, min(5, priority))
                    })
            except Exception as e:
                continue
        
        # 方法2: 如果方法1没找到，尝试更宽松的模式（允许字段顺序不同）
        if not gaps:
            # 匹配 concept 和 gap_type，不要求顺序
            pattern2 = r'"concept"\s*:\s*"([^"]+)"[^}]*"gap_type"\s*:\s*"([^"]+)"[^}]*"priority"\s*:\s*(\d+)'
            matches = re.finditer(pattern2, text, re.DOTALL)
            for match in matches:
                try:
                    concept = match.group(1).strip()
                    gap_type = match.group(2).strip()
                    priority = int(match.group(3))
                    
                    if concept and gap_type:
                        gaps.append({
                            "concept": concept,
                            "gap_type": gap_type,
                            "priority": max(1, min(5, priority))
                        })
                except:
                    continue
        
        return gaps
    
    def run(self, state: GraphState) -> GraphState:
        """识别知识缺口（基于全局上下文）"""
        # 检查是否有全局上下文
        has_global_context = state.get("global_outline") and state.get("knowledge_units")
        
        if has_global_context:
            # 有全局上下文时，使用增强的prompt
            template = """你是教学助手,基于整个文档的全局分析结果,识别学生理解当前页面内容的障碍点。

文档全局信息:
- 主题: {main_topic}
- 知识逻辑流程: {knowledge_flow}
- 全局知识点单元: {knowledge_units}

当前页面内容: {raw_text}

任务: 结合全局知识框架,识别当前页面中学生可能缺少的知识
要求:
1. 参考全局知识点单元,识别当前页面涉及的概念
2. 考虑概念在整个文档知识体系中的位置
3. 识别学生可能缺少的背景知识或前置知识

识别(JSON数组,最多5个):
[
  {{
    "concept": "概念",
    "gap_type": "缺少什么(选一个: 直观解释/应用示例/背景知识/公式推导/前置知识)",
    "priority": 优先级1-5,
    "global_relation": "在全局知识框架中的位置(可选)"
  }}
]

原则:
- 结合全局知识框架，只标注真正影响理解的缺口
- 优先级高的是必须补充的
- 考虑概念在整个文档中的位置和关系
- 不要过度延伸
"""
            # 格式化全局知识点单元
            knowledge_units_str = ""
            if state.get("knowledge_units"):
                for unit in state["knowledge_units"][:10]:  # 最多显示10个
                    pages_str = ",".join(map(str, unit.pages))
                    concepts_str = ",".join(unit.core_concepts)
                    knowledge_units_str += f"- {unit.title} (页码: {pages_str}, 核心概念: {concepts_str})\n"
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            print(f"📤 调用LLM进行知识缺口识别...")
            try:
                response = chain.invoke({
                    "main_topic": state.get("global_outline", {}).get("main_topic", "未知"),
                    "knowledge_flow": state.get("global_outline", {}).get("knowledge_flow", ""),
                    "knowledge_units": knowledge_units_str or "无",
                    "raw_text": state["raw_text"][:800]
                })
            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                import traceback
                traceback.print_exc()
                state["knowledge_gaps"] = []
                return state
        else:
            # 没有全局上下文时，使用原始prompt
            template = """你是教学助手,识别学生理解这段内容的障碍点。

内容: {raw_text}

识别(JSON数组,最多5个):
[
  {{
    "concept": "概念",
    "gap_type": "缺少什么(选一个: 直观解释/应用示例/背景知识/公式推导)",
    "priority": 优先级1-5
  }}
]

原则:
- 只标注真正影响理解的缺口
- 优先级高的是必须补充的
- 不要过度延伸
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            print(f"📤 调用LLM进行知识缺口识别...")
            try:
                response = chain.invoke({"raw_text": state["raw_text"][:800]})
            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                import traceback
                traceback.print_exc()
                state["knowledge_gaps"] = []
                return state
        
        # 检查响应是否有效
        if not response:
            print(f"❌ LLM返回空响应对象")
            state["knowledge_gaps"] = []
            return state
        
        if not hasattr(response, 'content'):
            print(f"❌ LLM响应对象没有content属性")
            print(f"   响应对象类型: {type(response)}")
            print(f"   响应对象: {response}")
            state["knowledge_gaps"] = []
            return state
        
        try:
            # 尝试解析JSON，支持markdown代码块和截断的JSON
            response_text = response.content.strip() if response.content else ""
            original_text = response_text
            
            # 打印原始响应用于调试
            print(f"🔍 原始LLM响应长度: {len(response_text)} 字符")
            if len(response_text) == 0:
                print(f"❌ LLM响应为空！")
                print(f"   原始response.content类型: {type(response.content)}")
                print(f"   原始response.content值: {repr(response.content)}")
                state["knowledge_gaps"] = []
                return state
            
            # 移除可能的markdown代码块标记
            if response_text.startswith("```"):
                print(f"🔍 检测到markdown代码块，开始提取JSON...")
                # 使用更简单的方法：直接查找```json和```之间的内容
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    if end > start:
                        response_text = response_text[start:end].strip()
                        print(f"✅ 使用简单方法提取JSON，长度: {len(response_text)} 字符")
                    else:
                        # 如果没找到结束标记，尝试找到最后一个```
                        end = response_text.rfind("```")
                        if end > start:
                            response_text = response_text[start:end].strip()
                            print(f"✅ 使用简单方法提取JSON（未找到结束标记），长度: {len(response_text)} 字符")
                        else:
                            # 如果还是找不到，使用原始方法
                            print(f"⚠️  无法找到代码块结束标记，使用原始方法...")
                            lines = response_text.split("\n")
                            json_lines = []
                            in_code_block = False
                            for i, line in enumerate(lines):
                                line_stripped = line.strip()
                                if line_stripped.startswith("```"):
                                    in_code_block = not in_code_block
                                    print(f"   第{i+1}行: 代码块标记，in_code_block={in_code_block}")
                                    continue
                                if in_code_block:  # 修复：应该在代码块内时添加
                                    json_lines.append(line)
                                    if len(json_lines) <= 3:
                                        print(f"   第{i+1}行: 添加到JSON ({len(line)} 字符)")
                            response_text = "\n".join(json_lines).strip()
                elif "```" in response_text:
                    # 处理普通的```代码块
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    if end > start:
                        response_text = response_text[start:end].strip()
                        print(f"✅ 提取普通代码块内容，长度: {len(response_text)} 字符")
                    else:
                        end = response_text.rfind("```")
                        if end > start:
                            response_text = response_text[start:end].strip()
                            print(f"✅ 提取普通代码块内容（未找到结束标记），长度: {len(response_text)} 字符")
                
                print(f"🔍 提取后JSON长度: {len(response_text)} 字符")
                if len(response_text) == 0:
                    print(f"❌ 提取JSON后为空！")
                    print(f"   原始响应前500字符: {original_text[:500]}")
                    # 尝试使用正则表达式直接提取
                    import re
                    json_match = re.search(r'\[[\s\S]*?\]', original_text)
                    if json_match:
                        response_text = json_match.group(0)
                        print(f"✅ 使用正则表达式提取JSON数组，长度: {len(response_text)} 字符")
            
            print(f"🔍 LLM响应前300字符: {response_text[:300]}")
            
            # 尝试直接解析
            gaps_data = None
            try:
                gaps_data = json.loads(response_text)
                print(f"✅ JSON解析成功")
            except json.JSONDecodeError as e:
                # 如果解析失败，尝试修复常见的截断问题
                print(f"⚠️  JSON解析失败，错误位置: {e.pos}, 错误信息: {e.msg}")
                
                # 如果错误位置为0，可能是响应格式不对或为空
                if e.pos == 0:
                    print(f"⚠️  错误位置为0，可能是响应格式不对或为空")
                    print(f"🔍 完整响应内容:\n{response_text}")
                    
                    # 尝试使用正则表达式直接提取
                    gaps_data = self._parse_partial_json(response_text)
                    if gaps_data:
                        print(f"✅ 通过正则表达式提取了 {len(gaps_data)} 个对象")
                    else:
                        # 如果正则也失败，尝试查找JSON数组
                        import re
                        # 尝试找到 [ ... ] 模式
                        array_match = re.search(r'\[[\s\S]*?\]', response_text)
                        if array_match:
                            try:
                                gaps_data = json.loads(array_match.group(0))
                                print(f"✅ 从响应中提取JSON数组成功")
                            except:
                                gaps_data = []
                elif e.pos > 0:
                    # 如果JSON被截断，尝试找到最后一个完整的对象
                    print(f"⚠️  JSON被截断，尝试修复...")
                    truncated_text = response_text[:e.pos]
                    
                    # 找到最后一个完整的对象
                    last_brace = truncated_text.rfind('}')
                    if last_brace > 0:
                        # 找到这个对象所属的数组
                        before_brace = truncated_text[:last_brace]
                        last_bracket = before_brace.rfind('[')
                        if last_bracket >= 0:
                            # 尝试提取完整的数组
                            potential_json = truncated_text[last_bracket:last_brace+1] + ']'
                            try:
                                gaps_data = json.loads(potential_json)
                                print(f"✅ 成功修复截断的JSON，提取了 {len(gaps_data) if isinstance(gaps_data, list) else 1} 个对象")
                            except:
                                # 如果还是失败，尝试手动解析
                                gaps_data = self._parse_partial_json(truncated_text)
                                if gaps_data:
                                    print(f"✅ 通过正则表达式从截断文本中提取了 {len(gaps_data)} 个对象")
                        else:
                            gaps_data = self._parse_partial_json(truncated_text)
                            if gaps_data:
                                print(f"✅ 通过正则表达式从截断文本中提取了 {len(gaps_data)} 个对象")
                    else:
                        gaps_data = self._parse_partial_json(truncated_text)
                        if gaps_data:
                            print(f"✅ 通过正则表达式从截断文本中提取了 {len(gaps_data)} 个对象")
                else:
                    # 其他情况，尝试手动解析
                    gaps_data = self._parse_partial_json(response_text)
                    if gaps_data:
                        print(f"✅ 通过正则表达式提取了 {len(gaps_data)} 个对象")
            
            # 如果还是None，设为空列表
            if gaps_data is None:
                gaps_data = []
            
            # 确保是列表
            if not isinstance(gaps_data, list):
                gaps_data = [gaps_data] if gaps_data else []
            
            knowledge_gaps = []
            for g in gaps_data[:5]:  # 最多5个
                if not isinstance(g, dict):
                    continue
                    
                concept = g.get("concept", "").strip()
                gap_type = g.get("gap_type", "").strip()
                priority = g.get("priority", 3)
                
                # 验证数据有效性
                if concept and gap_type:
                    # 确保priority是数字且在1-5范围内
                    try:
                        priority = int(priority)
                        priority = max(1, min(5, priority))
                    except:
                        priority = 3
                    
                    knowledge_gaps.append(KnowledgeGap(
                        concept=concept,
                        gap_types=[gap_type],
                        priority=priority
                    ))
            
            print(f"✅ 成功识别 {len(knowledge_gaps)} 个知识缺口")
            if knowledge_gaps:
                for gap in knowledge_gaps:
                    print(f"   - {gap.concept} (优先级: {gap.priority}, 类型: {gap.gap_types[0]})")
        except Exception as e:
            print(f"⚠️  知识缺口识别JSON解析失败: {e}")
            print(f"   LLM原始响应前500字符: {response.content[:500]}")
            # 尝试手动解析
            try:
                gaps_data = self._parse_partial_json(response.content)
                knowledge_gaps = []
                for g in gaps_data[:5]:
                    if isinstance(g, dict) and g.get("concept") and g.get("gap_type"):
                        knowledge_gaps.append(KnowledgeGap(
                            concept=g["concept"].strip(),
                            gap_types=[g["gap_type"].strip()],
                            priority=max(1, min(5, int(g.get("priority", 3))))
                        ))
                if knowledge_gaps:
                    print(f"✅ 通过正则表达式提取了 {len(knowledge_gaps)} 个知识缺口")
                    for gap in knowledge_gaps:
                        print(f"   - {gap.concept} (优先级: {gap.priority}, 类型: {gap.gap_types[0]})")
                else:
                    print(f"⚠️  正则表达式解析未找到有效数据")
            except Exception as e2:
                print(f"⚠️  正则表达式解析也失败: {e2}")
                knowledge_gaps = []
        
        state["knowledge_gaps"] = knowledge_gaps
        return state


# ==================== Step 3: 定向知识扩展 Agent (精简) ====================
class KnowledgeExpansionAgent:
    """定向知识扩展 Agent - 生成补充说明"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.6)
    
    def run(self, state: GraphState) -> GraphState:
        """生成扩展内容"""
        expanded_contents = []
        
        # 按优先级排序,只处理前3个
        sorted_gaps = sorted(state["knowledge_gaps"], key=lambda x: x.priority, reverse=True)[:3]
        
        for gap in sorted_gaps:
            gap_type = gap.gap_types[0] if gap.gap_types else "解释"
            
            # 精简 prompt,明确要求
            template = """为学生补充说明(150字内,通俗易懂):

概念: {concept}
需要: {gap_type}
PPT原文: {raw_text}

补充说明:"""
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "concept": gap.concept,
                "gap_type": gap_type,
                "raw_text": state["raw_text"][:500]
            })
            
            expanded_contents.append(ExpandedContent(
                concept=gap.concept,
                gap_type=gap_type,
                content=response.content[:300],  # 限制长度
                sources=["AI生成"]
            ))
        
        state["expanded_content"] = expanded_contents
        return state


# ==================== Step 4: 外部检索增强 Agent (优化策略) ====================
class RetrievalAgent:
    """外部检索增强 Agent - 智能多源检索"""
    
    def __init__(self, llm_config: LLMConfig, vector_db_path: str = "./knowledge_base"):
        self.llm = llm_config.create_llm(temperature=0)
        self.embeddings = OpenAIEmbeddings(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url
        )
        self.vector_db_path = vector_db_path
        self.vectorstore = None
        
        # 多源检索配置
        self.sources = {
            "baidu_baike": {"url": "https://baike.baidu.com", "available": False},
            "wikipedia": {"url": "https://zh.wikipedia.org", "available": False},
            "arxiv": {"url": "https://arxiv.org", "available": False},
        }
        self._test_sources()
    
    def _test_sources(self):
        """测试外部源连通性"""
        for name, config in self.sources.items():
            config["available"] = test_url_connectivity(config["url"])
    
    def initialize_vectorstore(self, documents: List[Document] = None):
        """初始化向量数据库"""
        try:
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            if documents:
                self.vectorstore.add_documents(documents)
        except:
            if documents:
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.vector_db_path
                )
    
    def retrieve_local(self, query: str, k: int = 2) -> List[Document]:
        """本地 RAG 检索"""
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def retrieve_external(self, query: str) -> List[Document]:
        """外部检索 - 优先可用源"""
        docs = []
        
        # 只查询可用的源
        available_sources = [name for name, config in self.sources.items() if config["available"]]
        
        if not available_sources:
            return docs
        
        # 优先百度百科(中文友好)
        if "baidu_baike" in available_sources:
            # TODO: 实现百度百科API调用
            pass
        
        # 其次维基百科
        elif "wikipedia" in available_sources:
            # TODO: 实现维基百科API调用
            pass
        
        return docs
    
    def run(self, state: GraphState) -> GraphState:
        """执行检索增强"""
        retrieved_docs = []
        
        # 获取所有知识缺口（降低阈值，从priority >= 4改为 >= 3）
        gaps = state.get("knowledge_gaps", [])
        if not gaps:
            print("⚠️  没有知识缺口，跳过检索")
            state["retrieved_docs"] = []
            return state
        
        # 优先处理高优先级缺口（priority >= 4），如果没有则处理所有缺口
        high_priority_gaps = [g for g in gaps if hasattr(g, 'priority') and g.priority >= 4]
        gaps_to_search = high_priority_gaps if high_priority_gaps else gaps[:3]  # 最多3个
        
        print(f"🔍 为 {len(gaps_to_search)} 个知识缺口检索参考资料")
        
        # 合并查询,减少检索次数
        query = " ".join([gap.concept if hasattr(gap, 'concept') else gap.get("concept", "") for gap in gaps_to_search[:2]])
        
        if not query.strip():
            print("⚠️  查询为空，跳过检索")
            state["retrieved_docs"] = []
            return state
        
        # 1. 优先本地 RAG
        try:
            local_docs = self.retrieve_local(query, k=3)
            retrieved_docs.extend(local_docs)
            print(f"   📚 本地RAG找到 {len(local_docs)} 条")
        except Exception as e:
            print(f"   ⚠️  本地RAG检索失败: {e}")
        
        # 2. 检查外部源可用性
        available_external = any(s["available"] for s in self.sources.values())
        print(f"   🌐 外部源可用性: {available_external}")
        if available_external:
            for name, config in self.sources.items():
                if config["available"]:
                    print(f"      - {name}: ✅")
                else:
                    print(f"      - {name}: ❌")
        
        # 3. 仅当本地不足且有可用外部源时才检索
        if len(local_docs) < 2 and available_external:
            try:
                external_docs = self.retrieve_external(query)
                retrieved_docs.extend(external_docs)
                print(f"   🌐 外部检索找到 {len(external_docs)} 条")
            except Exception as e:
                print(f"   ⚠️  外部检索失败: {e}")
        elif not available_external:
            print(f"   ⚠️  所有外部源不可用，跳过外部检索")
        
        state["retrieved_docs"] = retrieved_docs[:5]  # 最多5条
        print(f"✅ 检索完成，共 {len(state['retrieved_docs'])} 条参考资料")
        return state


# ==================== Step 5: 内容一致性校验 Agent (防幻觉) ====================
class ConsistencyCheckAgent:
    """内容一致性校验 Agent - 防止幻觉"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0)
    
    def run(self, state: GraphState) -> GraphState:
        """执行一致性校验"""
        # 如果没有补充内容，跳过校验
        expanded_content = state.get("expanded_content", [])
        if not expanded_content:
            print("⚠️  没有补充内容，跳过一致性校验")
            state["check_result"] = CheckResult(status="pass", issues=[], suggestions=[])
            return state
        
        # 优化: 明确防幻觉要求
        template = """你是事实核查员,校验补充内容的准确性。

PPT原文: {raw_text}

补充内容: {expanded_content}

参考资料: {retrieved_docs}

严格校验(JSON):
{{
  "status": "pass或revise",
  "issues": ["问题列表"],
  "suggestions": ["改进建议"]
}}

原则:
1. 禁止编造PPT未提及的概念
2. 所有陈述必须有依据(PPT或参考资料)
3. 不确定的内容标记为"推测"
4. 发现矛盾必须revise
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        # 处理expanded_content可能是对象或字典
        expanded_text = "\n".join([
            f"{ec.concept if hasattr(ec, 'concept') else ec.get('concept', '')}: {ec.content if hasattr(ec, 'content') else ec.get('content', '')}" 
            for ec in expanded_content
        ])
        
        retrieved_docs = state.get("retrieved_docs", [])
        retrieved_text = "\n".join([
            f"[参考{i+1}] {doc.page_content[:150] if hasattr(doc, 'page_content') else str(doc)[:150]}"
            for i, doc in enumerate(retrieved_docs[:3])
        ]) if retrieved_docs else "无参考资料"
        
        response = chain.invoke({
            "raw_text": state["raw_text"][:600],
            "expanded_content": expanded_text or "无补充内容",
            "retrieved_docs": retrieved_text
        })
        
        try:
            # 尝试解析JSON，支持markdown代码块
            response_text = response.content.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if not in_code_block:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)
            
            result = json.loads(response_text)
            check_result = CheckResult(
                status=result.get("status", "pass"),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", [])
            )
        except:
            check_result = CheckResult(status="pass", issues=[], suggestions=[])
        
        state["check_result"] = check_result
        return state


# ==================== Step 6: 内容结构化整理 Agent (精简版) ====================
class StructuredOrganizationAgent:
    """内容结构化整理 Agent - 生成学习笔记"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.create_llm(temperature=0.5)
    
    def run(self, state: GraphState) -> GraphState:
        """整理最终笔记"""
        # 优化: 明确是学习笔记,不是完整文档
        template = """整理学习笔记(Markdown格式,300字内):

PPT原文:
{raw_text}

补充说明:
{expanded_content}

格式要求:
## [页面标题]

### 核心概念
- 概念1: 简要说明
- 概念2: 简要说明

### 补充理解
[补充内容,简洁易懂]

### 参考
[如有参考资料列出]

原则:
- 简洁,突出重点
- 不重复PPT原文
- 适合快速复习
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        expanded_text = "\n".join([
            f"**{ec.concept}**: {ec.content}" for ec in state["expanded_content"]
        ])
        
        response = chain.invoke({
            "raw_text": state["raw_text"][:500],
            "expanded_content": expanded_text or "无补充内容"
        })
        
        state["final_notes"] = response.content
        state["streaming_chunks"] = [response.content]
        return state