"""
FastAPI - Middleware & Project Structure
=========================================
中间件和项目最佳实践
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from contextlib import asynccontextmanager

# ========== 1. 生命周期事件 ==========
# 类似Spring的 @PostConstruct 和 @PreDestroy

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("Application starting...")
    yield
    # 关闭时执行
    print("Application shutting down...")

app = FastAPI(lifespan=lifespan)

# ========== 2. CORS中间件 ==========
# 解决跨域问题，类似Java的CORS Filter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 3. 自定义中间件 ==========

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(TimingMiddleware)

# ========== 4. 日志中间件 ==========

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response

# ========== 5. 错误处理 ==========

from fastapi import Request, status
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# ========== 6. 项目结构最佳实践 ==========
"""
完整项目结构:

myproject/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI入口
│   ├── config.py         # 配置
│   ├── models/           # 数据模型
│   │   ├── __init__.py
│   │   └── student.py
│   ├── schemas/          # Pydantic模型
│   │   ├── __init__.py
│   │   └── student.py
│   ├── crud/            # 数据库操作
│   │   ├── __init__.py
│   │   └── student.py
│   ├── routers/         # 路由
│   │   ├── __init__.py
│   │   └── student.py
│   ├── services/        # 业务逻辑
│   │   └── student.py
│   └── database.py      # 数据库配置
├── tests/               # 测试
├── .env                 # 环境变量
├── requirements.txt
└── README.md
"""

# ========== 7. 主应用示例 ==========

# 模拟路由模块
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

# 注册路由
app.include_router(router)

@app.get("/")
def root():
    return {"message": "FastAPI with middleware", "docs": "/docs"}

print("""
=== 运行方式 ===
uvicorn 08_middleware_project:app --reload
""")
