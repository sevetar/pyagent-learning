# FastAPI Web Development Tutorial

> Python lightweight web framework - Quick Start for Java developers

## Environment Setup

```bash
cd C:\Users\27959\Desktop\ai\pythonfast\pyweb

# Activate virtual environment
.venv\Scripts\activate  (Windows)
# or source .venv/bin/activate (Linux/Mac)

# Install dependencies
uv pip install fastapi uvicorn python-multipart pydantic
uv pip install python-jose[cryptography] passlib[bcrypt]
uv pip install sqlalchemy
```

## Learning Path

| File | Content | Java Equivalent |
|------|---------|----------------|
| `01_hello_world.py` | Quick start, routing | @RestController |
| `02_routing_params.py` | Path, query, body params | @PathVariable, @RequestParam |
| `03_response.py` | Response, status, headers | @ResponseBody |
| `04_crud_api.py` | RESTful CRUD | Spring Data REST |
| `05_database.py` | SQLite + SQLAlchemy | JPA/Hibernate |
| `06_auth_jwt.py` | JWT Authentication | Spring Security |
| `07_websocket.py` | WebSocket | @ServerEndpoint |
| `08_middleware_project.py` | Middleware, structure | Filter |
| `project_main.py` | Complete project | - |

## Quick Commands

```bash
# Run a single file
uvicorn 01_hello_world:app --reload

# Run the complete project
uvicorn project_main:app --reload

# Access API docs
http://127.0.0.1:8000/docs
```

## Java vs FastAPI Comparison

| Java (Spring Boot) | FastAPI |
|-------------------|---------|
| `@RestController` | `@app.get/post/put/delete` |
| `@PathVariable` | `user_id: int` (path param) |
| `@RequestParam` | `page: int = Query(1)` |
| `@RequestBody` | Pydantic Model |
| `@Service` | Plain functions |
| `@Repository` | SQLAlchemy queries |
| `ModelMapper` | Pydantic `.model_dump()` |
| `Spring Security` | OAuth2 + JWT |

## Key Features

- **Auto Docs**: `/docs` (Swagger) and `/redoc`
- **Type Hints**: Python type annotations
- **Pydantic**: Data validation
- **Async**: Built-in async support
- **Dependencies**: Dependency injection system

## Project Structure

```
pyweb/
├── 01_hello_world.py     # Tutorial files
├── 02_routing_params.py
├── ...
├── project_main.py       # Complete project
├── .venv/                # Virtual environment
└── student_system.db     # SQLite database (auto-created)
```

## Next Steps

1. Run each tutorial file
2. Test APIs at `/docs`
3. Build your own project
4. Learn: Frontend integration, Deployment (Docker, Nginx)
