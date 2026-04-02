import os
import sys
import asyncio

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')

from agents import (
    EnhancedWeatherAgent,
    WeatherResponse,
    CalculationResponse,
    GeneralResponse,
)


def demo_basic_chat():
    """演示 1: 基础对话（带中间件）"""
    print("\n" + "=" * 60)
    print("演示 1: 基础对话 + 中间件")
    print("=" * 60)

    agent = EnhancedWeatherAgent(enable_middleware=True)

    questions = [
        "北京今天天气怎么样？",
        "帮我计算 100 + 200",
    ]

    for question in questions:
        print(f"\n用户: {question}")
        print("-" * 40)
        response = agent.chat(question)
        print(f"助手: {response}\n")


async def demo_streaming():
    """演示 2: 流式传输"""
    print("\n" + "=" * 60)
    print("演示 2: 流式传输 (Streaming)")
    print("=" * 60)

    agent = EnhancedWeatherAgent(enable_middleware=False)

    question = "请详细介绍一下人工智能的发展历史"
    print(f"\n用户: {question}")
    print("-" * 40)
    print("助手: ", end="", flush=True)

    async for chunk in agent.chat_stream(question):
        print(chunk, end="", flush=True)

    print("\n")


def demo_structured_output():
    """演示 3: 结构化输出"""
    print("\n" + "=" * 60)
    print("演示 3: 结构化输出 (Structured Output)")
    print("=" * 60)

    agent = EnhancedWeatherAgent(enable_middleware=False)

    # 天气查询的结构化输出
    print("\n--- 天气查询 ---")
    response = agent.chat_structured(
        "上海今天天气怎么样？",
        response_model=WeatherResponse
    )
    print(f"回答: {response.answer}")
    print(f"城市: {response.city}")
    print(f"天气信息: {response.weather_info}")
    print(f"建议: {response.suggestion}")

    # 计算的结构化输出
    print("\n--- 数学计算 ---")
    response = agent.chat_structured(
        "计算 (50 + 30) * 2",
        response_model=CalculationResponse
    )
    print(f"回答: {response.answer}")
    print(f"表达式: {response.expression}")
    print(f"结果: {response.result}")

    # 通用结构化输出
    print("\n--- 通用查询 ---")
    response = agent.chat_structured(
        "现在几点了？",
        response_model=GeneralResponse
    )
    print(f"回答: {response.answer}")
    print(f"使用的工具: {response.tool_used}")
    print(f"置信度: {response.confidence}")


def demo_memory():
    """演示 4: 短期记忆"""
    print("\n" + "=" * 60)
    print("演示 4: 短期记忆 (Short-term Memory)")
    print("=" * 60)

    agent = EnhancedWeatherAgent(enable_middleware=False)

    # 多轮对话测试记忆
    conversations = [
        "我叫张三，我在北京",
        "我刚才说我在哪里？",  # 测试记忆
        "我叫什么名字？",  # 测试记忆
    ]

    for msg in conversations:
        print(f"\n用户: {msg}")
        print("-" * 40)
        response = agent.chat(msg)
        print(f"助手: {response}")

    # 显示记忆摘要
    print("\n--- 记忆摘要 ---")
    memory_summary = agent.get_memory_summary()
    print(f"线程ID: {memory_summary['thread_id']}")
    print(f"消息数量: {memory_summary['message_count']}")

    # 清空记忆
    print("\n--- 清空记忆后 ---")
    agent.clear_history()
    response = agent.chat("我叫什么名字？")
    print(f"用户: 我叫什么名字？")
    print(f"助手: {response}")


def demo_custom_middleware():
    """演示 5: 自定义中间件"""
    print("\n" + "=" * 60)
    print("演示 5: 自定义中间件 (Custom Middleware)")
    print("=" * 60)

    # 自定义中间件：统计字数
    class WordCountMiddleware:
        def __init__(self):
            self.total_words = 0

        def before_invoke(self, context):
            word_count = len(context.user_message.split())
            print(f"[WordCount] 用户消息字数: {word_count}")

        def after_invoke(self, context, response):
            word_count = len(response.split())
            self.total_words += word_count
            print(f"[WordCount] 助手回复字数: {word_count}")
            print(f"[WordCount] 累计总字数: {self.total_words}")

    agent = EnhancedWeatherAgent(enable_middleware=False)
    agent.add_middleware(WordCountMiddleware())

    questions = [
        "你好",
        "北京天气怎么样？",
    ]

    for question in questions:
        print(f"\n用户: {question}")
        print("-" * 40)
        response = agent.chat(question)
        print(f"助手: {response}\n")


def main():
    """主函数 - 运行所有演示"""
    print("=" * 60)
    print("LangChain 增强功能演示")
    print("=" * 60)

    # 演示 1: 基础对话 + 中间件
    demo_basic_chat()

    # 演示 2: 流式传输
    print("\n正在运行流式传输演示...")
    asyncio.run(demo_streaming())

    # 演示 3: 结构化输出
    demo_structured_output()

    # 演示 4: 短期记忆
    demo_memory()

    # 演示 5: 自定义中间件
    demo_custom_middleware()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
