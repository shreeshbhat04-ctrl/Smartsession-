from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # student_id -> websocket
        self.active_students: Dict[str, WebSocket] = {}
        # student_id -> name (for peer list)
        self.student_names: Dict[str, str] = {}
        # list of teacher websockets
        self.active_teachers: List[WebSocket] = []
        # student_id -> list of teacher websockets watching them
        self.watching_sessions: Dict[str, List[WebSocket]] = {}
    # STUDENTS 
    async def connect_student(self, websocket: WebSocket, student_id: str, name: str = "Unknown"):
        await websocket.accept()
        self.active_students[student_id] = websocket
        self.student_names[student_id] = name
        await self.broadcast_peer_list()

    async def disconnect_student(self, student_id: str):
        self.active_students.pop(student_id, None)
        self.student_names.pop(student_id, None)
        self.watching_sessions.pop(student_id, None)
        await self.broadcast_peer_list()

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    # TEACHERS 
    async def connect_teacher(self, websocket: WebSocket):
        await websocket.accept()
        self.active_teachers.append(websocket)
    def disconnect_teacher(self, websocket: WebSocket):
        if websocket in self.active_teachers:
            self.active_teachers.remove(websocket)
    async def broadcast_to_teachers(self, message: dict):
        for ws in self.active_teachers[:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect_teacher(ws)

    # BROADCAST TO STUDENTS (New)
    async def broadcast_to_students(self, message: dict):
        for student_id, ws in list(self.active_students.items()):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect_student(student_id)

    async def broadcast_teacher_status(self, status: str):
        await self.broadcast_to_students({
            "type": "teacher_status",
            "status": status
        })

    async def forward_frame_to_teachers(self, student_id: str, frame_data: str):
        # Continuous broadcast to ALL teachers
        if self.active_teachers:
            message = {
                "type": "student_frame",
                "studentId": student_id,
                "image": frame_data
            }
            # Broadcast to all teachers
            for ws in self.active_teachers:
                try:
                    await ws.send_json(message)
                except:
                    pass # Handle disconnects gracefully elsewhere

    async def broadcast_peer_list(self):
        # Send list of names/IDs to all students
        # collecting names is tricky since we only store ID->WS
        # We might need to store names too. 
        # For now, send IDs.
        active_ids = list(self.active_students.keys())
        await self.broadcast_to_students({
            "type": "peer_update",
            "peers": active_ids
        })

manager = ConnectionManager()
