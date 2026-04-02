from fastapi import FastAPI
from flowfix.api.routes import router

app = FastAPI(
    title="FlowFix AI Agent",
    description="FlowFix 协作调度平台 AI Agent + RAG 系统",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "FlowFix AI Agent API", "version": "0.1.0"}
