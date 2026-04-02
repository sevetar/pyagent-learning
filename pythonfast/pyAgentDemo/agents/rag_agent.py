"""
RAG Agent - 检索增强生成
基于docs2/retrieval.txt
使用InMemoryStore作为向量存储
"""
from typing import List, Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from config.settings import settings


class RAGAgent:
    """检索增强生成Agent"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0.7
        )
        # 使用简单的文档存储作为后备方案
        self.documents = []  # 简单存储文档
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def add_documents(self, documents: List[str]):
        """添加文档到存储"""
        self.documents.extend(documents)

    def _build_graph(self):
        """构建RAG图 - 使用Agentic RAG模式"""
        workflow = StateGraph(MessagesState)

        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)

        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def _retrieve_node(self, state: MessagesState):
        """检索节点 - 使用简单的关键词匹配"""
        query = state["messages"][-1].content
        query_lower = query.lower()

        # 简单的关键词匹配
        relevant_docs = []
        for doc in self.documents:
            # 提取查询中的关键词
            keywords = query_lower.split()
            # 检查文档是否包含任何关键词
            if any(keyword in doc.lower() for keyword in keywords if len(keyword) > 2):
                relevant_docs.append(doc)

        # 如果没有找到相关文档，返回所有文档
        if not relevant_docs:
            relevant_docs = self.documents[:3]

        context = "\n\n".join(relevant_docs[:3])
        return {"retrieved_docs": context}

    def _grade_node(self, state: MessagesState):
        """评分节点 - 判断检索的文档是否相关"""
        query = state["messages"][-1].content
        docs = state.get("retrieved_docs", "")

        # 使用LLM评分
        grading_prompt = f"""判断以下文档是否与查询相关。

查询: {query}

文档:
{docs}

回答 'yes' 或 'no'。"""

        response = self.llm.invoke([HumanMessage(content=grading_prompt)])
        grade = "yes" in response.content.lower()

        return {"is_relevant": grade}

    def _generate_node(self, state: MessagesState):
        """生成节点 - 基于检索的文档生成回答"""
        query = state["messages"][-1].content
        docs = state.get("retrieved_docs", "")

        prompt = f"""基于以下文档回答问题。

文档:
{docs}

问题: {query}

请提供准确的回答。"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"messages": [response]}

    def _should_generate(self, state: MessagesState) -> Literal["generate", "retrieve"]:
        """判断是否应该生成回答"""
        is_relevant = state.get("is_relevant", False)
        return "generate" if is_relevant else "retrieve"

    def chat(self, message: str, thread_id: str = "default"):
        """与RAG Agent对话"""
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        return result["messages"][-1].content