"""
Python基础综合练习
==================
练习1: 学生管理系统（CLI版）
练习2: 简单的计算器
"""

# ========== 练习1: 学生管理系统 ==========
"""
需求：
- 添加学生
- 删除学生
- 修改学生
- 查询学生
- 列出所有学生
- 保存到文件
"""

class Student:
    """学生类"""
    def __init__(self, student_id: str, name: str, age: int, score: float):
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score

    def __str__(self):
        return f"学号: {self.student_id}, 姓名: {self.name}, 年龄: {self.age}, 分数: {self.score}"

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "name": self.name,
            "age": self.age,
            "score": self.score
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["student_id"], data["name"], data["age"], data["score"])


class StudentManager:
    """学生管理器"""

    def __init__(self, filename="students.json"):
        self.filename = filename
        self.students = {}
        self.load()

    def add(self, student: Student):
        """添加学生"""
        if student.student_id in self.students:
            raise ValueError(f"学号 {student.student_id} 已存在")
        self.students[student.student_id] = student
        print(f"✓ 添加成功: {student.name}")

    def delete(self, student_id: str):
        """删除学生"""
        if student_id not in self.students:
            raise ValueError(f"学号 {student_id} 不存在")
        student = self.students.pop(student_id)
        print(f"✓ 删除成功: {student.name}")

    def update(self, student_id: str, name=None, age=None, score=None):
        """修改学生信息"""
        if student_id not in self.students:
            raise ValueError(f"学号 {student_id} 不存在")

        student = self.students[student_id]
        if name is not None:
            student.name = name
        if age is not None:
            student.age = age
        if score is not None:
            student.score = score
        print(f"✓ 修改成功: {student}")

    def get(self, student_id: str):
        """查询学生"""
        return self.students.get(student_id)

    def list_all(self):
        """列出所有学生"""
        if not self.students:
            print("暂无学生信息")
            return
        print("\n===== 学生列表 =====")
        for student in self.students.values():
            print(student)
        print(f"共 {len(self.students)} 人\n")

    def save(self):
        """保存到文件"""
        import json
        data = {sid: s.to_dict() for sid, s in self.students.items()}
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ 已保存到 {self.filename}")

    def load(self):
        """从文件加载"""
        import json
        import os
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sid, info in data.items():
                        self.students[sid] = Student.from_dict(info)
                print(f"✓ 已从 {self.filename} 加载")
            except Exception as e:
                print(f"加载失败: {e}")


def main():
    """主菜单"""
    manager = StudentManager()

    while True:
        print("""
===== 学生管理系统 =====
1. 添加学生
2. 删除学生
3. 修改学生
4. 查询学生
5. 列出所有学生
6. 保存
0. 退出
        """)
        choice = input("请选择: ").strip()

        try:
            if choice == "1":
                sid = input("学号: ").strip()
                name = input("姓名: ").strip()
                age = int(input("年龄: ").strip())
                score = float(input("分数: ").strip())
                manager.add(Student(sid, name, age, score))

            elif choice == "2":
                sid = input("学号: ").strip()
                manager.delete(sid)

            elif choice == "3":
                sid = input("学号: ").strip()
                name = input("新姓名(回车跳过): ").strip() or None
                age = input("新年龄(回车跳过): ").strip()
                age = int(age) if age else None
                score = input("新分数(回车跳过): ").strip()
                score = float(score) if score else None
                manager.update(sid, name, age, score)

            elif choice == "4":
                sid = input("学号: ").strip()
                student = manager.get(sid)
                if student:
                    print(student)
                else:
                    print("未找到该学生")

            elif choice == "5":
                manager.list_all()

            elif choice == "6":
                manager.save()

            elif choice == "0":
                print("退出系统")
                break

        except ValueError as e:
            print(f"错误: {e}")
        except Exception as e:
            print(f"系统错误: {e}")


# ========== 练习2: 简单计算器 ==========
"""
用lambda实现简单的计算器
"""

def calculator():
    """简单计算器"""
    operations = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b if b != 0 else "错误: 除数不能为零",
        "**": lambda a, b: a ** b,
        "%": lambda a, b: a % b
    }

    print("\n===== 简单计算器 =====")
    print("支持的运算: +, -, *, /, **, %")

    while True:
        expr = input("输入表达式 (如 3 + 5，输入 q 退出): ").strip()

        if expr.lower() == 'q':
            break

        try:
            # 简单解析
            parts = expr.split()
            if len(parts) != 3:
                print("格式错误，请输入如: 3 + 5")
                continue

            a, op, b = parts
            a, b = float(a), float(b)

            if op in operations:
                result = operations[op](a, b)
                print(f"结果: {result}")
            else:
                print(f"不支持的运算: {op}")

        except Exception as e:
            print(f"计算错误: {e}")


# 运行演示
if __name__ == "__main__":
    # 演示学生管理
    print("=== 学生管理系统演示 ===")

    # 创建管理器
    manager = StudentManager("demo_students.json")

    # 添加学生
    manager.add(Student("001", "张三", 20, 85.5))
    manager.add(Student("002", "李四", 21, 90.0))

    # 列出
    manager.list_all()

    # 修改
    manager.update("001", score=88.0)

    # 查询
    student = manager.get("001")
    print(f"查询001: {student}")

    # 删除
    manager.delete("002")
    manager.list_all()

    # 保存
    manager.save()

    # 运行计算器
    # calculator()

    print("\n=== 练习完成! ===")
