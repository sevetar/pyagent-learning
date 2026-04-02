"""
多Agent系统演示 - 展示docs2/中的所有功能
包括：长期记忆、RAG、Router、Subagents、Handoffs
"""
import sys
import asyncio
from agents.memory_agent import MemoryAgent
from agents.rag_agent import RAGAgent
from agents.multi_agent_system import RouterAgent, SupervisorAgent, HandoffAgent


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def demo_memory_agent():
    """演示1: 长期记忆Agent"""
    print_section("演示1: 长期记忆Agent (InMemoryStore)")

    agent = MemoryAgent()

    # 第一次对话 - 告诉Agent一些信息
    print("用户: 我叫张三，我喜欢Python编程")
    response = agent.chat("我叫张三，我喜欢Python编程", user_id="user123")
    print(f"Agent: {response}\n")

    # 第二次对话 - 测试记忆
    print("用户: 你还记得我的名字吗？")
    response = agent.chat("你还记得我的名字吗？", user_id="user123")
    print(f"Agent: {response}\n")

    # 第三次对话 - 测试记忆
    print("用户: 我喜欢什么？")
    response = agent.chat("我喜欢什么？", user_id="user123")
    print(f"Agent: {response}\n")


def demo_rag_agent():
    """演示2: RAG检索增强生成Agent"""
    print_section("演示2: RAG检索增强生成Agent")

    agent = RAGAgent()

    # 添加知识库文档
    documents = [
        "LangChain是一个用于开发由语言模型驱动的应用程序的框架。",
        "LangGraph是LangChain的扩展，用于构建有状态的多Actor应用程序。",
        "InMemoryStore是LangChain提供的内存存储解决方案，适合开发和测试。"
    ]
    agent.add_documents(documents)
    print("已添加知识库文档\n")

    # 查询
    print("用户: LangGraph是什么？")
    response = agent.chat("LangGraph是什么？")
    print(f"Agent: {response}\n")

    print("用户: InMemoryStore的用途是什么？")
    response = agent.chat("InMemoryStore的用途是什么？")
    print(f"Agent: {response}\n")


def demo_router_agent():
    """演示3: Router路由Agent"""
    print_section("演示3: Router路由Agent")

    agent = RouterAgent()

    # 天气查询
    print("用户: 北京今天天气怎么样？")
    response = agent.chat("北京今天天气怎么样？")
    print(f"Agent: {response}\n")

    # 一般查询
    print("用户: 什么是人工智能？")
    response = agent.chat("什么是人工智能？")
    print(f"Agent: {response}\n")


def demo_supervisor_agent():
    """演示4: Supervisor监督Agent (Subagents模式)"""
    print_section("演示4: Supervisor监督Agent (Subagents模式)")

    agent = SupervisorAgent()

    # 天气查询
    print("用户: 上海的天气如何？")
    response = agent.chat("上海的天气如何？")
    print(f"Agent: {response}\n")

    # 搜索查询
    print("用户: 搜索LangChain的最新信息")
    response = agent.chat("搜索LangChain的最新信息")
    print(f"Agent: {response}\n")


def demo_handoff_agent():
    """演示5: Handoff交接Agent"""
    print_section("演示5: Handoff交接Agent")

    agent = HandoffAgent()

    # 销售咨询
    print("用户: 我想购买你们的产品")
    response = agent.chat("我想购买你们的产品")
    print(f"Agent: {response}\n")

    # 技术支持
    print("用户: 我的系统出现了错误")
    response = agent.chat("我的系统出现了错误")
    print(f"Agent: {response}\n")


def main():
    """主函数"""
    # 设置UTF-8编码
    sys.stdout.reconfigure(encoding='utf-8')

    print("\n" + "=" * 60)
    print("  多Agent系统演示 - docs2/功能集成")
    print("  包括: 长期记忆、RAG、Router、Subagents、Handoffs")
    print("=" * 60)

    try:
        # 演示1: 长期记忆
        demo_memory_agent()

        # 演示2: RAG
        demo_rag_agent()

        # 演示3: Router
        demo_router_agent()

        # 演示4: Supervisor (Subagents)
        demo_supervisor_agent()

        # 演示5: Handoff
        demo_handoff_agent()

        print_section("所有演示完成！")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
