"""
异常处理 & 常用模块 - Python vs Java
=====================================
关键区别：
- 所有异常继承自Exception
- 无需throws声明
- try...except...finally
- 抛出异常: raise Exception()
- 常用模块: requests, json, datetime, os, pathlib等
"""

# ========== 1. 异常处理 ==========

# Java: try { ... } catch (Exception e) { ... } finally { ... }
# Python: except ... as e:

try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"除零错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
else:
    print("没有异常时执行")
finally:
    print("总是执行")

# 常见异常类型
# - ZeroDivisionError
# - ValueError
# - TypeError
# - FileNotFoundError
# - IndexError
# - KeyError

# ========== 2. 抛出异常 ==========
# Java: throw new IllegalArgumentException("错误");
# Python: raise ValueError("错误")

def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

try:
    divide(10, 0)
except ValueError as e:
    print(f"捕获异常: {e}")

# ========== 3. 自定义异常 ==========

class MyException(Exception):
    """自定义异常"""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


try:
    raise MyException("出错了!", code=500)
except MyException as e:
    print(f"自定义异常: {e}, code: {e.code}")

# ========== 4. 文件操作 ==========
# Java需要FileReader/BufferedReader
# Python简洁得多

# 写入文件
with open("test.txt", "w", encoding="utf-8") as f:
    f.write("Hello Python!\n")
    f.write("第二行")

# 读取文件
with open("test.txt", "r", encoding="utf-8") as f:
    # 方式1: 一次性读取
    # content = f.read()

    # 方式2: 逐行读取
    for line in f:
        print(line.strip())

# ========== 5. JSON处理 ==========
import json

# Java需要Jackson/Gson
# Python内置json模块

data = {
    "name": "张三",
    "age": 25,
    "skills": ["Python", "Java", "AI"]
}

# 序列化
json_str = json.dumps(data, ensure_ascii=False, indent=2)
print(json_str)

# 反序列化
parsed = json.loads(json_str)
print(parsed["name"])

# ========== 6. 日期时间 ==========
from datetime import datetime, timedelta

now = datetime.now()
print(f"当前时间: {now}")
print(f"格式化: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# 时间计算
tomorrow = now + timedelta(days=1)
print(f"明天: {tomorrow}")

# 字符串转datetime
dt = datetime.strptime("2024-01-01", "%Y-%m-%d")
print(f"解析: {dt}")

# ========== 7. 系统操作 ==========
import os
import pathlib

# 当前目录
print(f"当前目录: {os.getcwd()}")

# 列出文件
for item in os.listdir("."):
    print(f"  {item}")

# 路径操作（推荐用pathlib）
p = pathlib.Path("test.txt")
print(f"是否存在: {p.exists()}")
print(f"是文件: {p.is_file()}")
print(f"父目录: {p.parent}")
print(f"文件名: {p.stem}")

# ========== 8. 列表/字典高级操作 ==========

# 列表
numbers = [1, 2, 3, 4, 5]

# map (类似Java stream().map())
squared = list(map(lambda x: x**2, numbers))
print(f"平方: {squared}")

# filter (类似Java stream().filter())
evens = list(filter(lambda x: x % 2 == 0, numbers))
print(f"偶数: {evens}")

# reduce (类似Java stream().reduce())
from functools import reduce
total = reduce(lambda x, y: x + y, numbers)
print(f"总和: {total}")

# all/any
print(f"全部>0: {all(x > 0 for x in numbers)}")
print(f"有偶数: {any(x % 2 == 0 for x in numbers)}")

# zip (合并多个列表)
names = ["a", "b", "c"]
scores = [90, 85, 95]
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# ========== 9. 随机数 & 数学 ==========
import random
import math

# 随机数
print(f"随机整数: {random.randint(1, 100)}")
print(f"随机浮点: {random.random()}")
print(f"随机选择: {random.choice(['a', 'b', 'c'])}")

# 数学
print(f"sqrt: {math.sqrt(16)}")
print(f"pi: {math.pi}")
print(f"e: {math.e}")
print(f"ceil: {math.ceil(3.2)}")
print(f"floor: {math.floor(3.8)}")

print("\n=== 异常和模块完成！===")
