"""工具定义模块

根据 LangChain 官方文档，工具允许模型通过调用函数与外部系统交互。
"""
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    # 这是一个模拟的天气工具，实际应用中应该调用真实的天气 API
    weather_data = {
        "北京": "晴天，温度 15-25°C",
        "上海": "多云，温度 18-28°C",
        "深圳": "阴天，温度 22-30°C",
        "杭州": "小雨，温度 16-24°C",
    }
    return weather_data.get(city, f"{city}的天气：晴朗，温度适宜")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4"

    Returns:
        计算结果
    """
    try:
        # 注意：在生产环境中应该使用更安全的方式来计算表达式
        result = eval(expression)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"


@tool
def get_current_time() -> str:
    """获取当前时间

    Returns:
        当前时间字符串
    """
    from datetime import datetime
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def search_info(query: str) -> str:
    """搜索信息

    Args:
        query: 搜索查询

    Returns:
        搜索结果
    """
    # 这是一个模拟的搜索工具，实际应用中应该调用真实的搜索 API
    search_results = {
        "langchain": "LangChain是一个用于开发由语言模型驱动的应用程序的框架。",
        "langgraph": "LangGraph是LangChain的扩展，用于构建有状态的多Actor应用程序。",
        "python": "Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。",
    }

    # 简单的关键词匹配
    query_lower = query.lower()
    for key, value in search_results.items():
        if key in query_lower:
            return f"搜索结果：{value}"

    return f"搜索 '{query}' 的结果：找到相关信息，这是一个很有趣的话题。"


# 导出所有工具
ALL_TOOLS = [get_weather, calculate, get_current_time, search_info]
