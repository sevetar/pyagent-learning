# Python 基础速成教程

> 面向有Java基础的开发者

## 学习路径

| 文件 | 内容 | 对比Java |
|------|------|----------|
| `01_python_vs_java.py` | Python vs Java 快速对比 | - |
| `02_control_flow.py` | 条件判断、循环 | if/else, for, while |
| `03_functions.py` | 函数定义、参数、装饰器 | 方法、lambda |
| `04_oop.py` | 面向对象：类、继承、多态 | class, extends |
| `05_exception_modules.py` | 异常处理、常用模块 | try/catch |
| `06_virtualenv_pip.py` | 虚拟环境、包管理 | Maven/Gradle |
| `07_practice.py` | 综合练习 | - |

## 运行方式

```bash
# 运行单个文件
python 01_python_vs_java.py
python 02_control_flow.py
# ...

# 运行综合练习
python 07_practice.py
```

## Java vs Python 核心差异速查

```python
# Java: public static void main(String[] args)
# Python: 直接写

print("Hello")  # System.out.println

# 变量 - 无类型声明
name = "张三"  # String name = "张三"

# 容器
list_ = [1, 2, 3]      # ArrayList
dict_ = {"a": 1}      # HashMap
set_ = {1, 2, 3}      # HashSet

# 函数
def func(a, b=1):     # 方法，可选参数
    return a + b

# 类
class Person:
    def __init__(self, name):  # 构造函数
        self.name = name
```

## 建议学习顺序

1. 先运行 `01_python_vs_java.py` 理解基础语法
2. 看 `02_control_flow.py` 掌握控制流
3. 学 `03_functions.py` 理解函数
4. 学 `04_oop.py` 掌握面向对象
5. 学 `05_exception_modules.py` 了解常用库
6. 学 `06_virtualenv_pip.py` 掌握环境配置
7. 完成 `07_practice.py` 练习

## 后续学习

- **Python Web开发**: Flask / FastAPI
- **Python AI Agent**: langchain, openai, anthropic
- **异步编程**: asyncio, aiohttp
- **数据处理**: pandas, numpy
