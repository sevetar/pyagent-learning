"""
面向对象编程 - Python vs Java
==============================
关键区别：
- class关键字，无大括号
- 构造函数是__init__（不是类名）
- 所有成员方法第一个参数是self（类似this）
- 无访问修饰符，用_和__表示protected/private
- 支持多重继承
- 不需要显式定义接口
"""

# ========== 1. 类定义 ==========
# Java: public class Person { private String name; public Person(String name) { this.name = name; } }
# Python:

class Person:
    """人类 - 文档字符串"""

    # 类属性（类似静态变量）
    species = "智人"

    # 构造函数
    def __init__(self, name: str, age: int = 0):
        # self类似this
        self.name = name
        self.age = age
        # 私有属性（以__开头，会被名称改编）
        self.__secret = "秘密"

    # 实例方法（类似Java普通方法）
    def say_hello(self):
        return f"你好，我是{self.name}，今年{self.age}岁"

    # 私有方法
    def __private_method(self):
        return "这是私有方法"

    # 类方法（类似静态方法，但会自动传入cls）
    @classmethod
    def create_baby(cls, name):
        """创建婴儿，默认age=0"""
        return cls(name, 0)

    # 静态方法（不依赖类或实例）
    @staticmethod
    def is_adult(age):
        return age >= 18


# 使用类
person = Person("张三", 25)
print(person.say_hello())
print(f"是否成年: {Person.is_adult(25)}")

# 创建婴儿
baby = Person.create_baby("小明")
print(f"婴儿: {baby.name}, 年龄: {baby.age}")

# ========== 2. 继承 ==========
# Java: class Student extends Person
# Python: class Student(Person)

class Student(Person):
    """学生类"""

    def __init__(self, name: str, age: int, student_id: str):
        # 调用父类构造函数
        super().__init__(name, age)
        self.student_id = student_id

    # 重写方法
    def say_hello(self):
        return f"我是学生{self.name}，学号{self.student_id}"

    # 新方法
    def study(self, subject: str):
        return f"{self.name}正在学习{subject}"


student = Student("李四", 20, "S001")
print(student.say_hello())  # 调用重写后的方法
print(student.study("Python"))
print(f"继承自Person: {isinstance(student, Person)}")

# ========== 3. 多继承 ==========
# Python支持多继承，Java不支持

class Teacher:
    def __init__(self, subject: str):
        self.subject = subject

    def teach(self):
        return f"教{self.subject}"


class TeachingAssistant(Student, Teacher):
    """助教：同时是学生和老师"""

    def __init__(self, name: str, age: int, student_id: str, subject: str):
        Student.__init__(self, name, age, student_id)
        Teacher.__init__(self, subject)


ta = TeachingAssistant("王五", 22, "TA001", "数学")
print(ta.say_hello())  # 继承自Student
print(ta.teach())       # 继承自Teacher
print(ta.study("Python"))  # 继承自Student

# ========== 4. 访问修饰符 ==========
# Python没有真正的private，用约定

class Person2:
    def __init__(self, name):
        self.name = name      # 公开
        self._protected = 1    # 约定protected
        self.__private = 2    # 名称改编(mangled)

p = Person2("张三")
print(p.name)        # 可以访问
print(p._protected)  # 可以访问，但不推荐
# print(p.__private) # 报错！实际上被改名为_PPerson2__private
print(p._Person2__private)  # 可以这样访问（不推荐）

# ========== 5. 属性 @property ==========
# 类似Java的getter/setter，但更Pythonic

class Person3:
    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        """getter"""
        return self.__name

    @name.setter
    def name(self, value):
        """setter"""
        if len(value) < 2:
            raise ValueError("名字至少2个字符")
        self.__name = value


p3 = Person3("张三")
print(p3.name)   # 调用getter
p3.name = "李四"  # 调用setter
# p3.name = "一"  # 抛出异常

# ========== 6. 特殊方法（魔法方法） ==========
# 类似Java的toString(), equals()等

class Person4:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        """类似Java的toString()"""
        return f"Person(name={self.name}, age={self.age})"

    def __repr__(self):
        """调试用，表示"""
        return f"Person4('{self.name}', {self.age})"

    def __eq__(self, other):
        """类似Java的equals()"""
        if isinstance(other, Person4):
            return self.name == other.name and self.age == other.age
        return False

    def __hash__(self):
        """用于set/dict"""
        return hash((self.name, self.age))

    def __len__(self):
        """让对象可被len()"""
        return self.age


p4 = Person4("张三", 25)
print(str(p4))          # Person(name=张三, age=25)
print(repr(p4))         # Person4('张三', 25)
print(p4 == Person4("张三", 25))  # True
print(len(p4))          # 25

# ========== 7. 抽象类 ==========
# 类似Java的abstract class

from abc import ABC, abstractmethod

class Animal(ABC):
    """抽象类"""

    @abstractmethod
    def speak(self):
        """抽象方法"""
        pass

    def sleep(self):
        """具体方法"""
        return "正在睡觉..."


class Dog(Animal):
    def speak(self):
        return "汪汪!"


# animal = Animal()  # 报错！不能实例化抽象类
dog = Dog()
print(dog.speak())
print(dog.sleep())

print("\n=== 面向对象完成！===")
