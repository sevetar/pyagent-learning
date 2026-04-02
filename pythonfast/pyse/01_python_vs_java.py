"""
Python vs Java 快速对比
========================
你有Java基础，学Python会很简单。核心区别：

| 特性       | Java                    | Python                    |
|-----------|------------------------|--------------------------|
| 类型       | 静态类型                | 动态类型                  |
| 编译       | 编译成字节码            | 解释执行                  |
| 语法       | 大括号、分号            | 缩进、无分号              |
| 面向对象   | 纯OOP                  | 多范式(OO+函数式)        |
| main方法  | 必须public static void main| 直接脚本执行          |

快速入门：
"""

# ========== 1. Hello World ==========
# Java: public class Hello { public static void main(String[] args) { System.out.println("Hello"); } }
# Python: 一行搞定

print("Hello World!")  # 无需分号，无需类包装

# ========== 2. 变量 - 不需要声明类型 ==========
# Java: int a = 1; String b = "hello";
# Python: 直接赋值，自动推断类型

name = "张三"           # str (字符串)
age = 25               # int (整数)
height = 1.75          # float (浮点数)
is_student = True      # bool (布尔值)

# 打印变量
print(f"姓名: {name}, 年龄: {age}, 身高: {height}, 是学生: {is_student}")

# ========== 3. 类型查看 ==========
print(type(name))      # <class 'str'>
print(type(age))       # <class 'int'>
print(type(height))    # <class 'float'>
print(type(is_student)) # <class 'bool'>

# ========== 4. 基础数据类型 ==========
# Python一切皆对象，没有int/double/char等基本类型之分
# int - 任意精度整数
big_num = 10**100  # 100次方，Java需要BigInteger
print(f"大数: {big_num}")

# float - 双精度浮点
pi = 3.14159

# str - 字符串（功能强大）
s = "Hello Python"
print(s.upper())      # HELLO PYTHON
print(s.replace("Python", "World"))  # Hello World

# list - 动态数组（类似ArrayList）
arr = [1, 2, 3, 4, 5]
arr.append(6)         # 添加
arr[0] = 0           # 修改

# dict - 哈希表（类似HashMap）
user = {"name": "张三", "age": 25}
print(user["name"])   # 张三
user["city"] = "北京" # 添加

# set - 集合（类似HashSet）
tags = {"python", "java", "ai"}
tags.add("langchain")

# tuple - 元组（不可变列表）
coord = (10, 20)     # 不可修改，类比final数组

print("\n=== 基础对比完成！运行这个文件试试 ===")
