"""
函数 - Python vs Java
======================
关键区别：
- def关键字定义（无返回类型声明）
- 参数不需要类型声明
- 支持多返回值（实际返回tuple）
- 支持默认参数、*args、**kwargs
- 函数是一等公民（可以赋值、作为参数）
"""

# ========== 1. 基本函数定义 ==========
# Java: public static int add(int a, int b) { return a + b; }
# Python: 无需public static，无需返回类型

def add(a, b):
    return a + b

result = add(3, 5)
print(f"3 + 5 = {result}")

# 无返回值（实际返回None）
def greet_print(name):
    print(f"你好, {name}!")

greet_print("张三")  # None作为返回值被忽略

# ========== 2. 多返回值 ==========
# Java需要用数组或自定义类返回多个值
# Python直接返回tuple

def get_stats(numbers):
    total = sum(numbers)
    average = total / len(numbers)
    return total, average  # 实际返回 (total, average)

total, average = get_stats([1, 2, 3, 4, 5])
print(f"总和: {total}, 平均值: {average}")

# 也可以这样接收（得到tuple）
result = get_stats([1, 2, 3])
print(f"返回tuple: {result}")  # (6, 2.0)

# ========== 3. 默认参数 ==========
# 类似Java，但语法更简单

def greet(name, greeting="你好"):
    return f"{greeting}, {name}!"

print(greet("张三"))          # 你好, 张三!
print(greet("李四", "早上好"))  # 早上好, 李四!

# ========== 4. 可变参数 *args, **kwargs ==========
# *args: 接收任意数量的位置参数（tuple）
# **kwargs: 接收任意数量的关键字参数（dict）

def sum_all(*args):
    print(f"args类型: {type(args)}")  # <class 'tuple'>
    return sum(args)

print(f"求和: {sum_all(1, 2, 3, 4, 5)}")  # 15

def print_info(name, **kwargs):
    print(f"姓名: {name}")
    for key, value in kwargs.items():
        print(f"  {key}: {value}")

print_info("张三", age=25, city="北京", job="工程师")

# ========== 5. 函数作为参数/返回值 ==========
# Java需要接口/lambda
# Python直接传递函数

def apply_operation(a, b, operation):
    """operation是一个函数"""
    return operation(a, b)

def add_operation(x, y):
    return x + y

def multiply(x, y):
    return x * y

print(f"加法: {apply_operation(3, 5, add_operation)}")       # 8
print(f"乘法: {apply_operation(3, 5, multiply)}")  # 15

# 匿名函数 lambda（类似Java lambda）
result = apply_operation(3, 5, lambda x, y: x - y)
print(f"减法(lambda): {result}")  # -2

# ========== 6. 高级: 装饰器 ==========
# 类似于Java的AOP/拦截器

def timer(func):
    """装饰器: 计算函数执行时间"""
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 执行时间: {end - start:.4f}秒")
        return result
    return wrapper

@timer
def slow_function():
    import time
    time.sleep(0.5)  # 模拟耗时操作
    return "完成!"

print(slow_function())

# ========== 7. 类型提示 (Python 3.5+) ==========
# 类似于Java的类型声明，但只是提示，不强制

def greet_typed(name: str, times: int = 1) -> str:
    """带类型提示的函数"""
    return " ".join([f"你好, {name}!"] * times)

print(greet_typed("张三", 2))

# ========== 8. 变量作用域 ==========
# LEGB规则: Local -> Enclosing -> Global -> Built-in

global_var = "全局"

def outer():
    enclosing_var = "外部"

    def inner():
        local_var = "局部"
        print(global_var)   # 全局
        print(enclosing_var)  # 外部
        print(local_var)     # 局部

    inner()

outer()

print("\n=== 函数部分完成！===")
