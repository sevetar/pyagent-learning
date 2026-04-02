"""
FastAPI - WebSocket
===================
实时双向通信

对比Java:
- WebSocket   -> @ServerEndpoint
- AsyncIO     -> Servlet 3.1+
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import asyncio

app = FastAPI(title="WebSocket API")

# ========== 1. 连接管理器 ==========
# 类似Java的Session管理

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# ========== 2. WebSocket端点 ==========

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            # 处理消息
            await manager.send_personal_message(
                f"Server: You said '{data}'",
                websocket
            )
            # 广播给所有人
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} disconnected")

# ========== 3. 简单聊天示例 ==========

chat_rooms = {}

@app.websocket("/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in chat_rooms:
        chat_rooms[room_id] = []

    try:
        # 发送历史消息
        for msg in chat_rooms[room_id][-10:]:  # 最近10条
            await websocket.send_text(msg)

        while True:
            data = await websocket.receive_text()
            message = f"[Room {room_id}] {data}"
            chat_rooms[room_id].append(message)

            # 广播
            await websocket.send_text(message)
    except WebSocketDisconnect:
        await websocket.send_text("Disconnected")

# ========== 4. 前端示例 ==========

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
</head>
<body>
    <h1>WebSocket Test</h1>
    <input id="message" placeholder="Enter message">
    <button onclick="send()">Send</button>
    <div id="output"></div>

    <script>
        const ws = new WebSocket("ws://127.0.0.1:8000/ws/user1");

        ws.onmessage = function(event) {
            document.getElementById("output").innerHTML += event.data + "<br>";
        };

        function send() {
            const msg = document.getElementById("message").value;
            ws.send(msg);
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML)

print("""
=== 运行方式 ===
uvicorn 07_websocket:app --reload

=== 测试 ===
访问 http://127.0.0.1:8000/

或使用WebSocket客户端连接 ws://127.0.0.1:8000/ws/test
""")
