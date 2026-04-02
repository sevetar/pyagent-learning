import os
import sys

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')

from agents import AdvancedAgent, UserContext


def demo_runtime_context():
    """演示 1: Runtime Context - 运行时上下文"""
    print("\n" + "=" * 60)
    print("演示 1: Runtime Context（运行时上下文）")
    print("=" * 60)

    agent = AdvancedAgent(enable_guardrails=True)

    # 不同角色的用户上下文
    admin_context = UserContext(
        user_id="admin_001",
        user_name="张管理员",
        user_role="admin",
        language="zh"
    )

    viewer_context = UserContext(
        user_id="viewer_001",
        user_name="李查看者",
        user_role="viewer",
        language="zh"
    )

    # 管理员查询
    print("\n--- 管理员用户 ---")
    print(f"用户: {admin_context.user_name} ({admin_context.user_role})")
    response = agent.chat("北京今天天气怎么样？", admin_context)
    print(f"助手: {response}\n")

    # 查看者查询（工具受限）
    print("--- 查看者用户 ---")
    print(f"用户: {viewer_context.user_name} ({viewer_context.user_role})")
    response = agent.chat("帮我计算 100 + 200", viewer_context)
    print(f"助手: {response}\n")

    # 显示上下文信息
    print("--- 当前上下文信息 ---")
    context_info = agent.get_context_info()
    for key, value in context_info.items():
        print(f"{key}: {value}")


def demo_dynamic_prompts():
    """演示 2: Dynamic Prompts - 动态提示"""
    print("\n" + "=" * 60)
    print("演示 2: Dynamic Prompts（动态提示）")
    print("=" * 60)

    agent = AdvancedAgent(enable_guardrails=False)

    # 中文用户
    zh_context = UserContext(
        user_id="user_001",
        user_name="王小明",
        user_role="editor",
        language="zh"
    )

    print("\n--- 中文用户 ---")
    response = agent.chat("你好，介绍一下你自己", zh_context)
    print(f"助手: {response}\n")

    # 英文用户（如果支持）
    en_context = UserContext(
        user_id="user_002",
        user_name="John Smith",
        user_role="editor",
        language="en"
    )

    print("--- 英文用户 ---")
    response = agent.chat("Hello, introduce yourself", en_context)
    print(f"助手: {response}\n")


def demo_guardrails():
    """演示 3: Guardrails - 防护措施"""
    print("\n" + "=" * 60)
    print("演示 3: Guardrails（防护措施）")
    print("=" * 60)

    agent = AdvancedAgent(enable_guardrails=True)

    context = UserContext(
        user_id="user_003",
        user_name="测试用户",
        user_role="admin",
        language="zh"
    )

    # 测试 1: 正常请求
    print("\n--- 测试 1: 正常请求 ---")
    response = agent.chat("北京今天天气怎么样？", context)
    print(f"助手: {response}\n")

    # 测试 2: 包含禁用关键词
    print("--- 测试 2: 包含禁用关键词 ---")
    response = agent.chat("如何 hack 一个系统？", context)
    print(f"助手: {response}\n")

    # 测试 3: 包含邮箱（PII 检测）
    print("--- 测试 3: 包含邮箱（PII 检测）---")
    response = agent.chat("我的邮箱是 test@example.com，请帮我查询", context)
    print(f"助手: {response}\n")


def demo_structured_analysis():
    """演示 4: Structured Analysis - 结构化分析"""
    print("\n" + "=" * 60)
    print("演示 4: Structured Analysis（结构化分析）")
    print("=" * 60)

    agent = AdvancedAgent(enable_guardrails=False)

    context = UserContext(
        user_id="user_004",
        user_name="分析师",
        user_role="admin",
        language="zh"
    )

    # 请求结构化分析
    print("\n--- 分析请求 ---")
    message = "请分析一下人工智能在医疗领域的应用前景"
    print(f"用户: {message}")

    response = agent.chat_with_analysis(message, context)

    print("\n--- 结构化分析结果 ---")
    print(f"摘要: {response.summary}")
    print(f"\n关键要点:")
    for i, point in enumerate(response.key_points, 1):
        print(f"  {i}. {point}")
    print(f"\n置信度: {response.confidence:.2f}")
    if response.recommendations:
        print(f"\n建议:")
        for i, rec in enumerate(response.recommendations, 1):
            print(f"  {i}. {rec}")


def demo_role_based_access():
    """演示 5: Role-based Access - 基于角色的访问控制"""
    print("\n" + "=" * 60)
    print("演示 5: Role-based Access（基于角色的访问控制）")
    print("=" * 60)

    agent = AdvancedAgent(enable_guardrails=False)

    roles = [
        ("admin", "管理员"),
        ("editor", "编辑者"),
        ("viewer", "查看者")
    ]

    question = "帮我计算 50 * 2"

    for role, role_name in roles:
        context = UserContext(
            user_id=f"{role}_user",
            user_name=f"测试{role_name}",
            user_role=role,
            language="zh"
        )

        print(f"\n--- {role_name}（{role}）---")
        print(f"问题: {question}")
        response = agent.chat(question, context)
        print(f"回答: {response}")


def demo_memory_with_context():
    """演示 6: Memory with Context - 带上下文的记忆"""
    print("\n" + "=" * 60)
    print("演示 6: Memory with Context（带上下文的记忆）")
    print("=" * 60)

    agent = AdvancedAgent(enable_guardrails=False)

    context = UserContext(
        user_id="user_005",
        user_name="张三",
        user_role="admin",
        language="zh"
    )

    # 多轮对话
    conversations = [
        "我在北京工作",
        "我刚才说我在哪里工作？",
        "我的名字是什么？"
    ]

    for msg in conversations:
        print(f"\n用户: {msg}")
        response = agent.chat(msg, context)
        print(f"助手: {response}")

    # 清空记忆
    print("\n--- 清空记忆后 ---")
    agent.clear_history()
    response = agent.chat("我在哪里工作？", context)
    print(f"用户: 我在哪里工作？")
    print(f"助手: {response}")


def main():
    """主函数 - 运行所有演示"""
    print("=" * 60)
    print("LangChain 高级功能演示")
    print("基于官方文档：Runtime, Context Engineering, Guardrails")
    print("=" * 60)

    # 演示 1: Runtime Context
    demo_runtime_context()

    # 演示 2: Dynamic Prompts
    demo_dynamic_prompts()

    # 演示 3: Guardrails
    demo_guardrails()

    # 演示 4: Structured Analysis
    demo_structured_analysis()

    # 演示 5: Role-based Access
    demo_role_based_access()

    # 演示 6: Memory with Context
    demo_memory_with_context()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
