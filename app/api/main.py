from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import base64
import json
import time
from app.api.connection_manager import ConnectionManager
manager = ConnectionManager()
from app.core.monitor import StudentIntegrityMonitor as StudentMonitor
app = FastAPI()
#middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
monitor = StudentMonitor()
@app.get("/")
async def get():
    return {"status": "Smartsession is running"}
@app.websocket("/ws/student/{student_id}")
async def student_endpoint(websocket: WebSocket, student_id: str):
    await manager.connect_student(websocket, student_id)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            name = payload.get("name", "Unknown")
            if manager.student_names.get(student_id) != name:
                manager.student_names[student_id] = name
                await manager.broadcast_peer_list()
            if "image" not in payload:
                continue
            image_data = payload["image"].split(",")[1]
            await manager.forward_frame_to_teachers(student_id, image_data)

            image_bytes = base64.b64decode(image_data)
            
            # 3. Run Analysis
            result = monitor.analyze_frame(image_bytes)
            state = result["state"]

            if state in ["No Face", "Multiple Faces"]:
                normalized_state = "NOT_PRESENT"
            elif state == "Looking Away":
                normalized_state = "DISTRACTED"
            elif state == "Happy":
                normalized_state = "ENGAGED"
            else:
                normalized_state = state.upper()
            # SCORE DERIVATION 
            confusion_index = 0
            engagement_score = 0
            if state == "Confused":
                confusion_index = result.get("score", 0)
            elif state in ["Focused", "Happy"]:
                engagement_score = result.get("score", 0)
            elif state == "Looking Away":
                engagement_score = -1
            # 4. Send Feedback to Student
            await manager.send_personal_message(
                {"type": "feedback", "payload": result},
                websocket
            )
            # 5. Broadcast Telemetry to Teachers
            telemetry = {
                "type": "telemetry_update",
                "data": {
                    "studentId": student_id,
                    "name": name,
                    "state": normalized_state,
                    "raw_state": state,  
                    "confusion_index": confusion_index,
                    "engagement_score": engagement_score,
                    "gaze": result.get("gaze", "CENTER"),
                    "timestamp": time.time()
                }
            }
            await manager.broadcast_to_teachers(telemetry)
    except WebSocketDisconnect:
        await manager.disconnect_student(student_id)
        await manager.broadcast_to_teachers({
            "type": "telemetry_update",
            "data": {
                "studentId": student_id,
                "name": "Unknown",
                "state": "OFFLINE",
                "engagement_score": 0,
                "confusion_index": 0
            }
        })

@app.websocket("/ws/teacher/{class_id}")
async def teacher_endpoint(websocket: WebSocket, class_id: str):
    await manager.connect_teacher(websocket)
    await manager.broadcast_teacher_status("ONLINE")
    try:
        while True:
            # Teacher receives commands
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                pass
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect_teacher(websocket)
        await manager.broadcast_teacher_status("OFFLINE")
