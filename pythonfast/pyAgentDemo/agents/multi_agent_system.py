"""
多Agent系统 - Router、Subagents、Handoffs模式
基于docs2/router.txt, subagent.txt, Handoffs.txt
"""
from typing import Literal, Optional
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from typing import Annotated
from tools.weather_tools import get_weather, search_info
from config.settings import settings


# ============ Router模式 ============
class RouterState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    route: Optional[str]


class RouterAgent:
    """路由Agent - 根据查询类型分发到不同的专家Agent"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0
        )
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(RouterState)
        workflow.add_node("router", self._router_node)
        workflow.add_node("weather_expert", self._weather_expert)
        workflow.add_node("general_expert", self._general_expert)
        workflow.add_edge(START, "router")
        workflow.add_conditional_edges(
            "router",
            self._route_query,
            {"weather": "weather_expert", "general": "general_expert"}
        )
        workflow.add_edge("weather_expert", END)
        workflow.add_edge("general_expert", END)
        return workflow.compile(checkpointer=self.checkpointer)

    def _router_node(self, state: RouterState):
        query = state["messages"][-1].content
        prompt = f"分析查询，判断路由到哪个专家。查询: {query}\n可选: weather(天气) 或 general(一般)。只回答 'weather' 或 'general'。"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"route": response.content.strip().lower()}

    def _route_query(self, state: RouterState) -> Literal["weather", "general"]:
        return "weather" if "weather" in state.get("route", "") else "general"

    def _weather_expert(self, state: RouterState):
        query = state["messages"][-1].content
        # 提取城市名
        cities = ["北京", "上海", "深圳", "杭州"]
        city = next((c for c in cities if c in query), query)
        weather_info = get_weather.invoke({"city": city})
        return {"messages": [AIMessage(content=f"[天气专家] {weather_info}")]}

    def _general_expert(self, state: RouterState):
        response = self.llm.invoke(state["messages"])
        return {"messages": [response]}

    def chat(self, message: str, thread_id: str = "default"):
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        return result["messages"][-1].content


# ============ Subagents模式 ============
class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next: Optional[str]
    subagent_result: Optional[str]


class SupervisorAgent:
    """监督Agent - 使用子Agent作为工具"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0.7
        )
        self.weather_agent = create_react_agent(
            self.llm,
            tools=[get_weather],
            prompt="你是天气专家，专门处理天气查询。"
        )
        self.search_agent = create_react_agent(
            self.llm,
            tools=[search_info],
            prompt="你是搜索专家，专门处理信息搜索。"
        )
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(SupervisorState)
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("weather_subagent", self._weather_subagent)
        workflow.add_node("search_subagent", self._search_subagent)
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_subagent,
            {"weather": "weather_subagent", "search": "search_subagent", "end": END}
        )
        workflow.add_edge("weather_subagent", "supervisor")
        workflow.add_edge("search_subagent", "supervisor")
        return workflow.compile(checkpointer=self.checkpointer)

    def _supervisor_node(self, state: SupervisorState):
        query = state["messages"][-1].content
        if state.get("subagent_result"):
            result = state["subagent_result"]
            final = self.llm.invoke([
                SystemMessage(content=f"子Agent结果: {result}"),
                HumanMessage(content=f"基于以上结果回答: {query}")
            ])
            return {"messages": [final], "next": "end", "subagent_result": None}

        prompt = f"分析查询，决定调用哪个子Agent。查询: {query}\n可选: weather(天气) 或 search(搜索)。只回答 'weather' 或 'search'。"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"next": response.content.strip().lower()}

    def _route_to_subagent(self, state: SupervisorState) -> Literal["weather", "search", "end"]:
        next_agent = state.get("next", "end")
        if "weather" in next_agent:
            return "weather"
        elif "search" in next_agent:
            return "search"
        return "end"

    def _weather_subagent(self, state: SupervisorState):
        result = self.weather_agent.invoke({"messages": state["messages"]})
        return {"subagent_result": result["messages"][-1].content}

    def _search_subagent(self, state: SupervisorState):
        result = self.search_agent.invoke({"messages": state["messages"]})
        return {"subagent_result": result["messages"][-1].content}

    def chat(self, message: str, thread_id: str = "default"):
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        return result["messages"][-1].content


# ============ Handoffs模式 ============
class HandoffState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    department: Optional[str]
    handoff: Optional[str]


class HandoffAgent:
    """交接Agent - 状态驱动的Agent间切换"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0.7
        )
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(HandoffState)
        workflow.add_node("triage", self._triage_agent)
        workflow.add_node("sales", self._sales_agent)
        workflow.add_node("support", self._support_agent)
        workflow.add_edge(START, "triage")
        workflow.add_conditional_edges(
            "triage",
            self._route_from_triage,
            {"sales": "sales", "support": "support", "end": END}
        )
        workflow.add_conditional_edges(
            "sales",
            self._route_from_sales,
            {"support": "support", "end": END}
        )
        workflow.add_conditional_edges(
            "support",
            self._route_from_support,
            {"sales": "sales", "end": END}
        )
        return workflow.compile(checkpointer=self.checkpointer)

    def _triage_agent(self, state: HandoffState):
        query = state["messages"][-1].content
        prompt = f"你是客服分诊员。分析查询，判断转接部门。查询: {query}\n可选: sales(销售) 或 support(技术支持)。只回答 'sales' 或 'support'。"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        dept = response.content.strip().lower()
        return {"department": dept}

    def _route_from_triage(self, state: HandoffState) -> Literal["sales", "support", "end"]:
        dept = state.get("department", "")
        if "sales" in dept:
            return "sales"
        elif "support" in dept:
            return "support"
        return "end"

    def _sales_agent(self, state: HandoffState):
        query = state["messages"][0].content
        prompt = f"你是销售顾问。用户咨询: {query}\n如需技术支持请回复含'HANDOFF_TO_SUPPORT'，否则提供销售建议。"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        if "HANDOFF_TO_SUPPORT" in response.content:
            return {"handoff": "support", "messages": [AIMessage(content="[销售] 为您转接技术支持...")]}
        return {"handoff": "end", "messages": [AIMessage(content=f"[销售顾问] {response.content}")]}

    def _route_from_sales(self, state: HandoffState) -> Literal["support", "end"]:
        return "support" if state.get("handoff") == "support" else "end"

    def _support_agent(self, state: HandoffState):
        query = state["messages"][0].content
        prompt = f"你是技术支持工程师。用户问题: {query}\n如需购买产品请回复含'HANDOFF_TO_SALES'，否则提供技术支持。"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        if "HANDOFF_TO_SALES" in response.content:
            return {"handoff": "sales", "messages": [AIMessage(content="[技术支持] 为您转接销售部门...")]}
        return {"handoff": "end", "messages": [AIMessage(content=f"[技术支持] {response.content}")]}

    def _route_from_support(self, state: HandoffState) -> Literal["sales", "end"]:
        return "sales" if state.get("handoff") == "sales" else "end"

    def chat(self, message: str, thread_id: str = "default"):
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        return result["messages"][-1].content
