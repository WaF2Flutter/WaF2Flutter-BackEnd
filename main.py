# Sample Waf2flutter Backend 
# Test BackEnd and WebSocket using for comunication between backend and frontend(Waf2Flutter)
# Creator mortza mansori

import asyncio
import json
import secrets
import psutil
import shutil
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

sessions = {}

@app.post("/login")
async def login(request: LoginRequest):
    if request.username == "test" and request.password == "test":
        session_id = secrets.token_hex(16)
        otp = secrets.randbelow(9999)
        sessions[session_id] = otp
        print(f"Generated OTP for session {session_id}: {otp}")
        return {"login_status": "pending", "id": session_id, "message": "OTP sent"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")


from fastapi import Body

@app.post("/verify_otp")
async def verify_otp(session_id: str = Body(...), otp: int = Body(...)):
    if session_id in sessions:
        expected_otp = sessions[session_id]
        if expected_otp == otp:
            del sessions[session_id]
            return {"login_status": "success", "message": "Login successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid OTP")
    else:
        raise HTTPException(status_code=404, detail="Session ID not found")

async def get_system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    total, used, free = shutil.disk_usage("/")
    cloud_usage_percentage = (used / total) * 100
    memory = psutil.virtual_memory()

    return {
        'cpu_usage': cpu_usage,
        'cloud_usage_total': f"{total / (1024.0 ** 3):.2f} GB",
        'cloud_usage_used': f"{used / (1024.0 ** 3):.2f} GB",
        'cloud_usage_percentage': cloud_usage_percentage,
        'memory_usage_total': f"{memory.total / (1024.0 ** 3):.2f} GB",
        'memory_usage_used': f"{memory.used / (1024.0 ** 3):.2f} GB",
        'memory_usage_percentage': memory.percent,
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        command = await websocket.receive_text()
        if command == "start_system_info":
            while True:
                system_info = await get_system_info()
                await websocket.send_text(json.dumps(system_info))
                await asyncio.sleep(5)
    except WebSocketDisconnect:
        print("WebSocket connection closed")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)

