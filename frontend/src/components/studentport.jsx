import React, { useState, useEffect, useRef } from 'react';
import { Brain, AlertTriangle, CheckCircle } from 'lucide-react';

const WS_URL = "ws://localhost:8000/ws";

const StudentPortal = ({ studentId, name, onLogout }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const ws = useRef(null);
  const [status, setStatus] = useState("CONNECTING");
  const [feedback, setFeedback] = useState({ state: "NEUTRAL", message: "Initializing..." });
  const [peers, setPeers] = useState([]);
  const [teacherStatus, setTeacherStatus] = useState("OFFLINE");

  useEffect(() => {
    // 1. Initialize Webcam (Native API)
    const startWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: "user" }
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing webcam:", err);
        setFeedback({ state: "ERROR", message: "Camera access denied. Please allow camera permissions." });
      }
    };
    startWebcam();
    // 2. Initialize WebSocket
    try {
      ws.current = new WebSocket(`${WS_URL}/student/${studentId}`);
      ws.current.onopen = () => setStatus("CONNECTED");
      ws.current.onclose = () => setStatus("DISCONNECTED");
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "feedback") {
            setFeedback(data.payload);
          } else if (data.type === "peer_update") {
            setPeers(data.peers || []);
          } else if (data.type === "teacher_status") {
            setTeacherStatus(data.status);
          }
        } catch (e) {
          console.error("Parse error", e);
        }
      };
    } catch (e) {
      setStatus("CONNECTION ERROR");
    }
    // 3. The Analysis Loop (4 FPS)
    const interval = setInterval(() => {
      if (videoRef.current && canvasRef.current && ws.current && ws.current.readyState === WebSocket.OPEN) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        // Check if video is ready
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          // Draw video frame to hidden canvas
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          // Mirror the image horizontally so it feels natural to the user
          ctx.translate(canvas.width, 0);
          ctx.scale(-1, 1);
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          // Convert to Base64 String
          // Low quality (0.6) is sufficient for ML and reduces network lag
          const imageSrc = canvas.toDataURL('image/jpeg', 0.6);
          // Send to Backend
          ws.current.send(JSON.stringify({
            type: "frame",
            studentId: studentId,
            name: name,
            image: imageSrc,
            timestamp: Date.now()
          }));
        }
      }
    }, 250); // 250ms = 4 frames per second
    // Cleanup
    return () => {
      clearInterval(interval);
      if (ws.current) ws.current.close();
      // Stop all video tracks
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, [studentId, name]);
  // Dynamic UI Styling based on state
  const getBorderColor = () => {
    switch (feedback.state) {
      case "Happy": return "border-green-500 ring-4 ring-green-500/30 shadow-[0_0_50px_rgba(34,197,94,0.3)]";
      case "Looking Away": return "border-yellow-500 ring-4 ring-yellow-500/30 shadow-[0_0_50px_rgba(234,179,8,0.5)]";
      case "Distracted":
      case "No Face":
      case "Multiple Faces": return "border-red-600 ring-4 ring-red-600/30 shadow-[0_0_50px_rgba(220,38,38,0.5)]";
      default: return "border-gray-700"; // Focused/Neutral
    }
  };
  const getStatusIcon = () => {
    // Kept for internal logic if needed, but UI is removed
    return null;
  };
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col p-2 font-sans items-center">
      <div className="w-full max-w-6xl flex flex-col h-[90vh]">
        {/* Header Info */}
        <div className="mb-2 flex justify-between items-center bg-white p-2 rounded-lg shadow-sm border border-gray-200">
          <div>
            <h2 className="text-lg font-bold text-gray-800 tracking-tight">Student Session</h2>
            <p className="text-gray-500 text-xs">ID: {studentId} • {name}</p>
          </div>
          <button
            onClick={onLogout}
            className="px-3 py-1.5 bg-red-50 text-red-600 rounded-md text-xs font-medium hover:bg-red-100 transition-colors"
          >
            End Session
          </button>
        </div>

        <div className="flex flex-col lg:flex-row gap-2 h-full flex-1">
          {/* Main Content: Camera */}
          <div className="flex-1 flex flex-col gap-2">
            <div className={`relative bg-black rounded-xl overflow-hidden shadow-lg border-2 ${getBorderColor()} aspect-video`}>
              {/* Native Video Element */}
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover transform -scale-x-100" // CSS Mirroring
              />
              {/* Hidden Canvas */}
              <canvas ref={canvasRef} className="hidden" />

              {/* Status Badge */}
              <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md px-2 py-1 rounded-full text-white text-[10px] font-medium flex items-center gap-1.5 border border-white/10">
                <div className={`w-1.5 h-1.5 rounded-full ${status === "CONNECTED" ? "bg-green-400 animate-pulse" : "bg-red-500"}`} />
                {status}
              </div>
            </div>

            {/* Feedback Section REMOVED as per user request */}
          </div>

          {/* SIDEBAR - Peer & Teacher Status */}
          <div className="w-full lg:w-64 flex flex-col gap-2">
            {/* Teacher Status Card */}
            <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-200">
              <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-2">Instructor Status</div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${teacherStatus === "ONLINE" ? "bg-green-500 animate-pulse ring-2 ring-green-200" : "bg-red-400"}`} />
                <span className={`text-sm font-semibold ${teacherStatus === "ONLINE" ? "text-green-700" : "text-gray-500"}`}>
                  {teacherStatus === "ONLINE" ? "Online" : "Offline"}
                </span>
              </div>
            </div>

            {/* Peer List Card */}
            <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-200 flex-1 flex flex-col">
              <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-2 flex justify-between items-center">
                <span>Classmates</span>
                <span className="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full text-[10px]">{peers.length}</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                {peers.length === 0 ? (
                  <div className="text-gray-400 text-xs italic text-center py-4">No others</div>
                ) : (
                  peers.map((peerId) => (
                    <div key={peerId} className="flex items-center gap-2 p-2 rounded bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-100">
                      <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-[10px] font-bold border border-blue-200">
                        ST
                      </div>
                      <div className="text-xs text-gray-700 font-medium truncate">
                        {peerId === studentId ? "Me" : peerId}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default StudentPortal;
