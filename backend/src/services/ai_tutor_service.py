"""AI 助教对话服务"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # "user" | "assistant"
    content: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class AITutorService:
    """AI 助教服务 - 基于当前 PPT 页面的对话"""
    
    def __init__(self, llm_config):
        self.llm = llm_config.create_llm(temperature=0.7)
        self.llm_config = llm_config
        
        # 每个页面一个独立的对话历史
        self.conversations: Dict[int, List[ChatMessage]] = {}
        self.page_context: Dict[int, Dict[str, Any]] = {}
    
    def set_page_context(
        self,
        page_id: int,
        title: str,
        content: str,
        key_concepts: List[str],
        analysis: str
    ):
        """设置页面上下文
        
        Args:
            page_id: 页面 ID
            title: 页面标题
            content: 页面原始内容
            key_concepts: 关键概念列表
            analysis: 深度分析内容
        """
        self.page_context[page_id] = {
            "title": title,
            "content": content,
            "key_concepts": key_concepts,
            "analysis": analysis
        }
        
        # 初始化该页面的对话历史
        if page_id not in self.conversations:
            self.conversations[page_id] = []
    
    def get_assistant_greeting(self, page_id: int) -> str:
        """获取助教欢迎语"""
        context = self.page_context.get(page_id)
        if not context:
            return "你好！我是基于 PPT 的助教。请先提供页面信息。"
        
        return f"你好！我是基于当前 PPT 的助教。关于 \"{context['title']}\" 你有什么疑问吗？"
    
    def chat(self, page_id: int, user_message: str) -> str:
        """与用户进行对话
        
        Args:
            page_id: 页面 ID
            user_message: 用户消息
        
        Returns:
            助教回复
        """
        context = self.page_context.get(page_id)
        if not context:
            return "请先加载页面内容。"
        
        # 获取对话历史
        if page_id not in self.conversations:
            self.conversations[page_id] = []
        
        conversation_history = self.conversations[page_id]
        
        # 构建系统提示词
        system_message = self._build_system_prompt(context, conversation_history)
        
        # 构建完整的对话
        messages = [
            SystemMessagePromptTemplate.from_template(system_message).format()
        ]
        
        # 添加对话历史
        for msg in conversation_history[-6:]:  # 保留最近 6 条消息
            if msg.role == "user":
                messages.append(HumanMessagePromptTemplate.from_template("{text}").format(text=msg.content))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg.content))
        
        # 添加当前用户消息
        messages.append(HumanMessagePromptTemplate.from_template("{text}").format(text=user_message))
        
        # 调用 LLM
        response = self.llm.invoke(messages)
        assistant_message = response.content
        
        # 保存对话到历史
        conversation_history.append(ChatMessage(role="user", content=user_message))
        conversation_history.append(ChatMessage(role="assistant", content=assistant_message))
        
        return assistant_message
    
    def _build_system_prompt(self, context: Dict[str, Any], history: List[ChatMessage]) -> str:
        """构建系统提示词"""
        template = """你是一位资深的 AI 助教，基于以下 PPT 内容为学生解答问题。

【当前页面标题】: {title}

【页面原始内容】:
{content}

【关键概念】: {concepts}

【深度分析】:
{analysis}

【你的职责】:
1. 基于上述页面内容为学生答疑解惑
2. 用清晰、通俗的语言解释复杂概念
3. 提供相关的例子或应用场景
4. 引导学生进行深入思考
5. 如果问题超出当前页面范围，礼貌地指出并尝试关联到当前内容

【交互风格】:
- 友好、耐心、鼓励性
- 逐步引导而不是直接给出答案
- 鼓励学生提出更多问题
- 定期总结关键点

【注意事项】:
- 始终保持在当前页面的上下文中
- 不编造不确定的信息
- 如果不确定，请说 "这是个很好的问题，但超出了我的知识范围"
- 保持对话的连贯性，考虑之前的问答

现在开始回答学生的问题。
"""
        
        concepts_str = ", ".join(context.get("key_concepts", []))
        
        return template.format(
            title=context.get("title", ""),
            content=context.get("content", ""),
            concepts=concepts_str,
            analysis=context.get("analysis", "")
        )
    
    def clear_conversation(self, page_id: int):
        """清除特定页面的对话历史"""
        if page_id in self.conversations:
            self.conversations[page_id] = []
    
    def get_conversation_history(self, page_id: int) -> List[Dict[str, str]]:
        """获取对话历史"""
        if page_id not in self.conversations:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in self.conversations[page_id]
        ]
    
    def switch_page(self, old_page_id: int, new_page_id: int):
        """切换页面时的处理
        
        Args:
            old_page_id: 旧页面 ID
            new_page_id: 新页面 ID
        """
        # 清除旧页面的对话历史（可选：也可以保留）
        # self.clear_conversation(old_page_id)
        
        # 初始化新页面的对话历史
        if new_page_id not in self.conversations:
            self.conversations[new_page_id] = []
