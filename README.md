# SmartSession

SmartSession is a real-time classroom monitoring assessment system that leverages computer vision to analyze student engagement and focus. It provides immediate feedback to students and live telemetry to teachers, enabling a more interactive and responsive learning environment.

## Architectural Approach

The application is built on a **Client-Server architecture** utilizing **WebSockets** for low-latency, real-time communication.

### Core Components

1.  **Frontend (React + Vite)**:
    - **Student Portal**: Captures webcam video streams and sends frames to the server via WebSockets. It receives instant feedback on the student's state (e.g., Focused, Distracted).
    - **Teacher Dashboard**: Connects to the server to receive aggregated, real-time telemetry of all students in the session.
    - **Styling**: Built with **TailwindCSS** for a modern, responsive UI.

2.  **Backend (FastAPI)**:
    - **WebSocket Manager**: Handles multiple concurrent connections (Students and Teachers) and routes messages efficiently.
    - **Computer Vision Pipeline**: Uses **OpenCV** and **MediaPipe** to analyze incoming video frames for:
        - Face Detection
        - Gaze Estimation
        - Emotion/Engagement Scoring
    - **Logic**: Determines the student's state (Focused, Happy, Confused, Distracted) based on the analysis and braodcasts updates.

### Data Flow
1.  **Capture**: Browser captures video frame.
2.  **Transmission**: Frame sent as base64 string over WebSocket to `/ws/student/{id}`.
3.  **Processing**: Server decodes image -> MediaPipe checks landmarks -> Logic calculates "Engagement Score".
4.  **Feedback**: Server sends result back to the specific Student client.
5.  **Monitoring**: Server broadcasts the student's status object to all connected Teacher clients via `/ws/teacher/{class_id}`.

---

## Tech Stack

- **Backend**: Python 3.x, FastAPI, Uvicorn, WebSockets, OpenCV, MediaPipe, NumPy.
- **Frontend**: React, Vite, TailwindCSS, Lucide-React.

---

## How to Run

### Prerequisites
- Python 3.8+
- Node.js & npm

### 1. Backend Setup

Navigate to the root directory.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Start the Server:**

```bash
uvicorn app.api.main:app --reload
```
The backend will run at `http://127.0.0.1:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the `frontend` directory.

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will usually run at `http://127.0.0.1:5173`.

## Features

- **Real-time Engagement Tracking**: Detects if a student is looking away, confused, or happy.
- **Privacy-Focused**: Images are processed in memory and not stored.
- **Live Teacher Dashboard**: View grid of student statuses.
- **Instant Student Feedback**: Visual cues for students to improve focus.
