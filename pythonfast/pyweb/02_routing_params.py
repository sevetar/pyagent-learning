"""
FastAPI - Routing & Parameters
===============================
详细讲解各种参数传递方式

对比Spring MVC:
- @PathVariable   -> FastAPI路径参数
- @RequestParam   -> FastAPI查询参数
- @RequestBody   -> FastAPI Pydantic模型
"""

from fastapi import FastAPI, Path, Query, Body
from pydantic import BaseModel, Field

app = FastAPI()

# ========== 1. 路径参数 (Path Parameters) ==========
# 类似 @PathVariable

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

# 带限制的路径参数
@app.get("/users/{user_id}/posts/{post_id}")
def get_post(user_id: int, post_id: int):
    return {"user_id": user_id, "post_id": post_id}

# ========== 2. 查询参数 (Query Parameters) ==========
# 类似 @RequestParam

@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),  # 必填
    page: int = Query(1, ge=1),                        # 默认值，最小1
    size: int = Query(10, le=100)                      # 最大100
):
    return {"query": q, "page": page, "size": size}

# 可选查询参数
@app.get("/items")
def get_items(category: str | None = None):
    if category:
        return {"category": category, "items": ["item1", "item2"]}
    return {"items": ["item1", "item2", "item3"]}

# ========== 3. 请求体 (Request Body) ==========
# 类似 @RequestBody

# Pydantic模型 - 类似Java Bean
class User(BaseModel):
    name: str
    email: str
    age: int | None = None  # 可选字段

@app.post("/users")
def create_user(user: User):
    return {"message": "User created", "user": user}

# 多个请求体参数
class Item(BaseModel):
    name: str
    price: float

class Order(BaseModel):
    user: User
    items: list[Item]

@app.post("/orders")
def create_order(order: Order):
    return {"message": "Order created", "order": order}

# ========== 4. 混合参数 ==========
@app.put("/users/{user_id}")
def update_user(
    user_id: int = Path(..., description="User ID"),  # 路径参数
    user: User = Body(...),                            # 请求体
    debug: bool = Query(False)                          # 查询参数
):
    return {
        "user_id": user_id,
        "user": user,
        "debug": debug
    }

# ========== 5. Pydantic高级验证 ==========

class UserAdvanced(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)
    tags: list[str] = []

@app.post("/users-advanced")
def create_user_advanced(user: UserAdvanced):
    return user

# ========== 6. 枚举类型 ==========
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

@app.get("/role/{role}")
def get_role(role: UserRole):
    return {"role": role, "description": f"Role is {role.value}"}

print("""
=== 运行方式 ===
uvicorn 02_routing_params:app --reload

测试:
- GET /users/1
- GET /search?q=python&page=1&size=10
- POST /users  (body: {"name": "Zhang", "email": "zhang@test.com"})
""")
