"""
FastAPI - Database Integration
==============================
使用SQLAlchemy连接数据库

对比Java:
- SQLAlchemy    -> Hibernate/JPA
- Session       -> EntityManager
- Model         -> Entity
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ========== 1. 安装依赖 ==========
"""
pip install sqlalchemy sqlite3 (内置)
"""

# ========== 2. 配置数据库 ==========
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# 数据库URL (SQLite)
DATABASE_URL = "sqlite:///./students.db"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite需要
)

# 创建SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base (类似JPA的@Entity)
Base = declarative_base()

# ========== 3. 定义模型 (类似Java Entity) ==========

class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)

# 创建表
Base.metadata.create_all(bind=engine)

# ========== 4. Pydantic模型 ==========

class Student(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # 允许从ORM模型创建

# ========== 5. 依赖注入 - 获取DB Session ==========
# 类似Java的 @PersistenceContext

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== 6. CRUD API ==========

app = FastAPI(title="Student API with Database")

@app.post("/students", response_model=Student, status_code=201)
def create_student(student: Student, db: Session = Depends(get_db)):
    # 检查邮箱是否存在
    db_student = db.query(StudentDB).filter(StudentDB.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already exists")

    # 创建记录
    db_student = StudentDB(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    return db_student

@app.get("/students", response_model=List[Student])
def get_students(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    students = db.query(StudentDB).offset(skip).limit(limit).all()
    return students

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=Student)
def update_student(
    student_id: int,
    student: Student,
    db: Session = Depends(get_db)
):
    db_student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 更新字段
    for key, value in student.model_dump().items():
        setattr(db_student, key, value)

    db.commit()
    db.refresh(db_student)
    return db_student

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(db_student)
    db.commit()
    return {"message": "Deleted"}

print("""
=== 运行方式 ===
uvicorn 05_database:app --reload

=== 数据库 ===
SQLite数据库文件: students.db (自动创建)
""")
