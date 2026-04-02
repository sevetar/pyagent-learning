"""
FastAPI - Student Management System
====================================
综合实战项目 - 完整的学生管理系统

包含:
- RESTful API
- SQLite数据库
- JWT认证
- 完整CRUD
- 最佳实践
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# ============== 配置 ==============
SECRET_KEY = "secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 30

DATABASE_URL = "sqlite:///./student_system.db"

# ============== 数据库 ==============
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StudentDB(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    age = Column(Integer)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)

# ============== Pydantic模型 ==============

class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    score: Optional[int] = None

class Student(StudentBase):
    id: int
    score: int
    created_at: datetime

    class Config:
        from_attributes = True

# ============== 认证 ==============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 模拟用户
USERS = {
    "admin": {"username": "admin", "password": get_password_hash("admin123"), "role": "admin"},
    "user": {"username": "user", "password": get_password_hash("user123"), "role": "user"},
}

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username not in USERS:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return USERS[username]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# ============== 依赖 ==============

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============== API ==============

app = FastAPI(title="Student Management System", version="1.0.0")

# --- 认证 ---

@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form.username)
    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": form.username})
    return {"access_token": token, "token_type": "bearer"}

# --- 学生CRUD ---

@app.post("/students", response_model=Student, status_code=201)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if db.query(StudentDB).filter(StudentDB.email == student.email).first():
        raise HTTPException(status_code=400, detail="Email exists")
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
    return db.query(StudentDB).offset(skip).limit(limit).all()

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=Student)
def update_student(
    student_id: int,
    student: StudentUpdate,
    db: Session = Depends(get_current_user),
    current_user = Depends(get_current_user)
):
    db_student = db.query(StudentDB).get(student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in student.model_dump(exclude_unset=True).items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    db_student = db.query(StudentDB).get(student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(db_student)
    db.commit()
    return {"message": "Deleted"}

# --- 统计 ---

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(StudentDB).count()
    avg_score = db.query(StudentDB).all()
    avg = sum(s.score for s in avg_score) / total if total else 0
    return {"total": total, "average_score": round(avg, 2)}

print("""
========================================
   Student Management System
========================================

Run: uvicorn project_main:app --reload

Login:
  Username: admin
  Password: admin123

Endpoints:
  POST   /token              - Login
  GET    /students           - List students
  POST   /students           - Create student
  GET    /students/{id}      - Get student
  PUT    /students/{id}      - Update student
  DELETE /students/{id}      - Delete student (admin only)
  GET    /stats              - Statistics
""")
