"""
FastAPI - Authentication & JWT
================================
用户认证和授权

对比Spring Security:
- JWT Token  -> Session/Token
- @Protected -> @PreAuthorize
- OAuth2     -> OAuth2
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

# ========== 1. 安装依赖 ==========
"""
pip install python-jose passlib[bcrypt] cryptography
"""

# ========== 2. JWT配置 ==========
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ========== 3. 安全方案 ==========
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 模拟用户数据库
FAKE_USERS = {
    "zhangsan": {
        "username": "zhangsan",
        "password": "password123",
        "email": "zhang@test.com"
    }
}

# ========== 4. 数据模型 ==========

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: str

# ========== 5. JWT工具函数 ==========
from jose import JWTError, jwt

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

# ========== 6. 获取当前用户 ==========

def get_current_user(token_data: TokenData = Depends(verify_token)):
    user = FAKE_USERS.get(token_data.username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# ========== 7. API端点 ==========

app = FastAPI(title="Auth API")

# 登录获取Token
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2兼容的登录接口
    username: 用户名
    password: 密码
    """
    user = FAKE_USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# 需要认证的接口
@app.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# 受保护的路由
@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.username}!",
        "user": current_user
    }

# ========== 8. 角色权限示例 ==========

class UserRole(BaseModel):
    username: str
    role: str

FAKE_USERS_WITH_ROLE = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "user": {"username": "user", "password": "user123", "role": "user"},
}

def get_current_active_admin(current_user: User = Depends(get_current_user)):
    user = FAKE_USERS_WITH_ROLE.get(current_user.username)
    if user and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@app.get("/admin-only")
def admin_only(current_user: User = Depends(get_current_active_admin)):
    return {"message": "Admin access granted"}

print("""
=== 运行方式 ===
uvicorn 06_auth_jwt:app --reload

=== 测试 ===
# 登录获取token
curl -X POST "http://127.0.0.1:8000/token" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=zhangsan&password=password123"

# 使用token访问
curl -X GET "http://127.0.0.1:8000/users/me" \\
  -H "Authorization: Bearer YOUR_TOKEN"
""")
