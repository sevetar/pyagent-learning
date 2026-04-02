"""
FastAPI - RESTful CRUD API
===========================
完整的学生管理系统API

REST规范:
- GET    /resources      获取列表
- GET    /resources/{id} 获取单个
- POST   /resources      创建
- PUT    /resources/{id} 完整更新
- PATCH  /resources/{id} 部分更新
- DELETE /resources/{id} 删除
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI(title="Student API", description="Student Management System")

# ========== 1. 数据模型 ==========

class Student(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=2)
    age: int = Field(..., ge=0, le=150)
    email: str
    created_at: Optional[datetime] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    email: Optional[str] = None

# ========== 2. 模拟数据库 (In-Memory) ==========
# 后续会讲真实数据库连接

students_db: dict[int, Student] = {}
next_id = 1

# ========== 3. CRUD 操作 ==========

# CREATE - 创建学生
@app.post("/students", status_code=status.HTTP_201_CREATED)
def create_student(student: Student):
    global next_id

    # 检查邮箱是否已存在
    for s in students_db.values():
        if s.email == student.email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

    student.id = next_id
    student.created_at = datetime.now()
    students_db[next_id] = student
    next_id += 1

    return student

# READ ALL - 获取所有学生
@app.get("/students")
def get_students(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    students = list(students_db.values())

    # 搜索过滤
    if search:
        students = [s for s in students if search.lower() in s.name.lower()]

    # 分页
    return students[skip:skip + limit]

# READ ONE - 获取单个学生
@app.get("/students/{student_id}")
def get_student(student_id: int):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    return students_db[student_id]

# UPDATE - 完整更新 (PUT)
@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")

    student.id = student_id
    student.created_at = students_db[student_id].created_at
    students_db[student_id] = student

    return student

# PATCH - 部分更新
@app.patch("/students/{student_id}")
def patch_student(student_id: int, student_update: StudentUpdate):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")

    student = students_db[student_id]

    # 只更新非None的字段
    update_data = student_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    students_db[student_id] = student
    return student

# DELETE - 删除
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")

    del students_db[student_id]
    return None  # 204 No Content

# ========== 4. 统计接口 ==========

@app.get("/students/stats")
def get_stats():
    total = len(students_db)
    avg_age = sum(s.age for s in students_db.values()) / total if total > 0 else 0

    return {
        "total": total,
        "average_age": round(avg_age, 2)
    }

print("""
=== 运行方式 ===
uvicorn 04_crud_api:app --reload

=== API文档 ===
访问 http://127.0.0.1:8000/docs

=== 测试 ===
# 创建学生
curl -X POST http://127.0.0.1:8000/students \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Zhang San", "age": 20, "email": "zhang@test.com"}'

# 获取所有
curl http://127.0.0.1:8000/students

# 获取单个
curl http://127.0.0.1:8000/students/1

# 更新
curl -X PUT http://127.0.0.1:8000/students/1 \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Li Si", "age": 21, "email": "li@test.com"}'

# 删除
curl -X DELETE http://127.0.0.1:8000/students/1
""")
