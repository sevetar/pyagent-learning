"""
FastAPI Quick Start
===================
FastAPI = Fast + Easy + Production-ready
类似Java的Spring Boot，但更简单

核心特点：
- 自动生成API文档 (Swagger UI)
- 类型提示支持
- 异步支持
- Pydantic数据验证
"""

# ========== 1. Hello World ==========
# 创建 main.py

from fastapi import FastAPI

app = FastAPI()  # 类似 Spring Boot 的 Application

@app.get("/")  # 类似 @RequestMapping
def root():
    return {"message": "Hello World!"}

# ========== 2. 运行方式 ==========
"""
# 方式1: uvicorn (推荐)
# 在 pyweb 目录执行:
uvicorn 01_hello_world:app --reload

# 或在 pythonfast 根目录执行:
uvicorn pyweb.01_hello_world:app --reload

# 方式2: 代码中运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# 访问文档:
# http://127.0.0.1:8000/docs      (Swagger UI)
# http://127.0.0.1:8000/redoc     (ReDoc)
"""

# ========== 3. 更多路由 ==========

@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI!"}

@app.get("/api/users")
def get_users():
    return {
        "users": [
            {"id": 1, "name": "Zhang San"},
            {"id": 2, "name": "Li Si"}
        ]
    }

# ========== 4. 路径参数 (Path Parameter) ==========
# 类似 Java: @GetMapping("/users/{id}")

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}

# ========== 5. 查询参数 (Query Parameter) ==========
# 类似 Java: @RequestParam

@app.get("/search")
def search(q: str = "default", page: int = 1, size: int = 10):
    return {
        "query": q,
        "page": page,
        "size": size,
        "results": [f"Result {i}" for i in range(size)]
    }

# ========== 6. 运行命令 ==========
print("""
=== 运行方式 ===
uvicorn 01_hello_world:app --reload

然后访问:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs  (API文档)
""")

