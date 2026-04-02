import os
import sys

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')

from agents import WeatherAgent


def main():
    print("=" * 50)
    print("LangChain + DeepSeek Agent Demo")
    print("=" * 50)

    agent = WeatherAgent()

    # 多轮对话示例
    questions = [
        "北京今天天气怎么样？",
        "帮我计算 (100 + 200) * 3 的结果",
        "现在几点了？",
        "根据北京的天气，今天适合出门吗？",  # 测试记忆能力
    ]

    for question in questions:
        print(f"\n用户: {question}")
        print("-" * 30)
        response = agent.chat(question)
        print(f"助手: {response}")
        print()


if __name__ == "__main__":
    main()
