"""
FastAPI - Response & Status Codes
==================================
HTTP状态码和响应设置

对比Spring:
- @ResponseStatus -> status_code
- @JsonIgnore -> response_model_exclude
"""

from fastapi import FastAPI, Response, status, HTTPException, Header
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from typing import Optional, List

app = FastAPI()

# ========== 1. 基础响应 ==========

@app.get("/")
def root():
    return {"message": "Hello"}

# ========== 2. 状态码 ==========

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(name: str):
    return {"id": 1, "name": name}

# ========== 3. 常见HTTP异常 ==========

@app.get("/user/{user_id}")
def get_user(user_id: int):
    if user_id <= 0:
        # 抛出HTTP异常
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )
    if user_id == 999:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "name": "Zhang San"}

# ========== 4. 自定义响应 ==========

@app.get("/json")
def json_response():
    return JSONResponse(
        content={"message": "Custom JSON"},
        status_code=200
    )

@app.get("/text")
def text_response():
    return PlainTextResponse("Hello as text!")

@app.get("/html")
def html_response():
    return HTMLResponse("""
        <html>
            <head><title>FastAPI</title></head>
            <body>
                <h1>Hello HTML!</h1>
            </body>
        </html>
    """)

# ========== 5. 设置响应头 ==========

@app.get("/headers")
def custom_headers(response: Response):
    response.headers["X-Custom-Header"] = "MyValue"
    response.headers["X-API-Version"] = "1.0"
    return {"message": "Check headers"}

# ========== 6. Cookie ==========

@app.get("/cookie")
def set_cookie(response: Response):
    response.set_cookie(key="session_id", value="abc123", httponly=True)
    return {"message": "Cookie set"}

@app.get("/get-cookie")
def get_cookie(session_id: str = Cookie(None)):
    return {"session_id": session_id}

# ========== 7. 请求头 ==========

@app.get("/headers-client")
def read_header(x_trace_id: str = Header(None)):
    return {"trace_id": x_trace_id}

# ========== 8. 响应模型 (类似Java的Jackson注解) ==========

from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    name: str
    # 排除敏感字段
    password: str = Field(default=None, exclude=True)

class UserIn(BaseModel):
    name: str
    email: str
    password: str  # 接收但不返回

# 设置response_model来过滤返回字段
@app.post("/users", response_model=UserOut)
def create_user(user: UserIn):
    # 假设保存到数据库
    return {"id": 1, **user.model_dump()}

# ========== 9. 分页响应 ==========

class PageResponse(BaseModel):
    page: int
    size: int
    total: int
    items: List[dict]

@app.get("/users-page", response_model=PageResponse)
def get_users_page(page: int = 1, size: int = 10):
    return {
        "page": page,
        "size": size,
        "total": 100,
        "items": [{"id": i, "name": f"User {i}"} for i in range(size)]
    }

print("""
=== 运行方式 ===
uvicorn 03_response:app --reload
""")
