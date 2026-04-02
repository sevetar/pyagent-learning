"""
长期记忆Agent - 使用InMemoryStore实现跨会话记忆
基于docs2/long-term memory.txt
"""
from typing import Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from config.settings import settings


class MemoryAgent:
    """带长期记忆的Agent"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0.7
        )
        self.checkpointer = MemorySaver()  # 短期记忆
        self.store = InMemoryStore()  # 长期记忆
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建带记忆的图"""
        workflow = StateGraph(MessagesState)

        workflow.add_node("agent", self._agent_node)
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)

        return workflow.compile(
            checkpointer=self.checkpointer,
            store=self.store
        )

    def _agent_node(self, state: MessagesState, config, *, store):
        """Agent节点 - 处理消息并访问长期记忆"""
        # 从config中获取用户ID和会话ID
        user_id = config.get("configurable", {}).get("user_id", "default")

        # 从store中读取用户的长期记忆
        namespace = ("memories", user_id)
        memories = store.search(namespace)

        # 构建系统提示，包含长期记忆
        memory_context = self._format_memories(memories)
        system_prompt = f"""你是一个有记忆的AI助手。

{memory_context}

请根据用户的历史记忆提供个性化的回复。"""

        # 调用LLM
        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        response = self.llm.invoke(messages)

        # 更新长期记忆（如果需要）
        self._update_memories(store, user_id, state["messages"][-1], response)

        return {"messages": [response]}

    def _format_memories(self, memories):
        """格式化记忆为文本"""
        if not memories:
            return "暂无历史记忆。"

        memory_texts = []
        for mem in memories:
            memory_texts.append(f"- {mem.value.get('content', '')}")

        return "用户的历史记忆：\n" + "\n".join(memory_texts)

    def _update_memories(self, store, user_id: str, user_msg, ai_msg):
        """更新长期记忆"""
        namespace = ("memories", user_id)

        # 提取关键信息（简化版，实际应该用LLM提取）
        user_content = user_msg.content if hasattr(user_msg, 'content') else str(user_msg)

        # 检查是否包含需要记住的信息
        memory_keywords = ["我叫", "我是", "我喜欢", "我的", "记住", "别忘了"]
        should_remember = any(keyword in user_content for keyword in memory_keywords)

        if should_remember:
            # 存储记忆
            memory_id = f"mem_{len(list(store.search(namespace)))}"
            store.put(
                namespace,
                memory_id,
                {"content": user_content, "timestamp": "now"}
            )

    def chat(self, message: str, user_id: str = "default", thread_id: str = "default"):
        """与Agent对话"""
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }

        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )

        return result["messages"][-1].content
