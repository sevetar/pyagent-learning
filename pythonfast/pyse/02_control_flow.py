"""
控制流 - Python vs Java
========================
关键区别：
- if/elif/else: 无括号，用缩进
- for: 增强for循环风格（实际是迭代器）
- while: 一样，但支持else
- switch: Python没有，用if/elif或字典替代
"""

# ========== 1. 条件判断 ==========
# Java: if (a > b) { ... } else if (a > c) { ... } else { ... }
# Python: 去掉括号和花括号，用elif

age = 20

if age < 18:
    print("未成年")
elif age < 35:
    print("青年")
elif age < 60:
    print("中年")
else:
    print("老年")

# Pythonic: 条件表达式（三元运算符）
status = "成年人" if age >= 18 else "未成年"
print(f"status: {status}")

# ========== 2. 循环 - for ==========
# Java: for (int i = 0; i < 5; i++) { ... }
# Python: for i in range(5): ...

print("\n=== for循环 ===")

# range(5) = [0, 1, 2, 3, 4]
for i in range(5):
    print(f"i = {i}")

# range(1, 6) = [1, 2, 3, 4, 5]
for i in range(1, 6):
    print(f"i = {i}")

# range(0, 10, 2) = [0, 2, 4, 6, 8]
for i in range(0, 10, 2):
    print(f"偶数: {i}")

# 遍历列表（类似Java增强for）
fruits = ["苹果", "香蕉", "橙子"]
for fruit in fruits:
    print(f"水果: {fruit}")

# 遍历字典
user = {"name": "张三", "age": 25, "city": "北京"}
for key in user:
    print(f"{key} = {user[key]}")

# items()方法 - 同时获取key和value
for key, value in user.items():
    print(f"{key}: {value}")

# ========== 3. 循环 - while ==========
print("\n=== while循环 ===")

count = 0
while count < 3:
    print(f"count = {count}")
    count += 1

# Python特有: while...else（循环正常结束执行else）
count = 0
while count < 3:
    print(f"count = {count}")
    count += 1
else:
    print("循环正常结束！")

# ========== 4. 跳转语句 ==========
# break: 跳出循环 - 相同
# continue: 跳过本次循环 - 相同
# pass: 空语句（占位符）- Python特有

for i in range(5):
    if i == 2:
        continue  # 跳过2
    if i == 4:
        break     # 跳出循环
    print(i)
# 输出: 0, 1, 3

# pass: 占位符，用于空函数/类
def empty_function():
    pass  # TODO: 实现这个函数

class EmptyClass:
    pass  # 以后再添加内容

# ========== 5. 高级特性 - 列表推导式 ==========
# Python特有，Java没有
print("\n=== 列表推导式 ===")

# [表达式 for item in iterable if 条件]
squares = [x**2 for x in range(5)]  # [0, 1, 4, 9, 16]
print(f"squares: {squares}")

# 过滤
evens = [x for x in range(10) if x % 2 == 0]  # [0, 2, 4, 6, 8]
print(f"偶数: {evens}")

# 字典推导式
squares_dict = {x: x**2 for x in range(5)}
print(f"字典推导式: {squares_dict}")

print("\n=== 控制流完成！===")
