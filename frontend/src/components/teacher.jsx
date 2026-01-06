import React, { useState, useEffect, useRef } from 'react';
import { Monitor, Users } from 'lucide-react';
import "../styles/teacher.css";

const WS_URL = "ws://localhost:8000/ws";
const TeacherDashboard = ({ onLogout }) => {
  const ws = useRef(null);
  const [students, setStudents] = useState({}); // Dictionary: { studentId: { ...data } }

  useEffect(() => {
    // Connect to Teacher Channel (Class A)
    try {
      ws.current = new WebSocket(`${WS_URL}/teacher/CLASS_A`);
      ws.current.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "telemetry_update") {
            const sData = msg.data;
            // Handle Student Logging Off
            if (sData.state === "OFFLINE") {
              setStudents(prev => {
                const newState = { ...prev };
                delete newState[sData.studentId];
                return newState;
              });
            } else {
              // Update or Add Student
              setStudents(prev => ({ ...prev, [sData.studentId]: sData }));
            }
          }
        } catch (e) {
          console.error("Teacher msg parse error", e);
        }
      };
    } catch (e) {
      console.error("Connection failed", e);
    }
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);


  /* New Color Logic:
   * Happy -> Green
   * Distracted / No Face / Multiple Faces -> Red
   * Looking Away -> Yellow
   * Focused -> White/Default
   */
  const getCardStyle = (state) => {
    switch (state) {
      case "Looking Away": return "bg-yellow-50 border-yellow-200 ring-2 ring-yellow-100";
      case "Distracted":
      case "No Face":
      case "Multiple Faces": return "bg-red-50 border-red-200 ring-2 ring-red-100";
      case "Happy": return "bg-green-50 border-green-200 ring-1 ring-green-100";
      default: return "bg-white border-gray-200"; // Focused / Neutral
    }
  };

  const getBadgeStyle = (state) => {
    switch (state) {
      case "Looking Away": return "bg-yellow-100 text-yellow-700";
      case "Distracted":
      case "No Face":
      case "Multiple Faces": return "bg-red-100 text-red-700";
      case "Happy": return "bg-emerald-100 text-emerald-700";
      default: return "bg-gray-100 text-gray-700";
    }
  };



  return (
    <div className="min-h-screen bg-gray-50 p-6 md:p-10 font-sans dashboard-container">
      {/* Dashboard Header */}
      <header className="dashboard-header">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Monitor className="text-blue-600" size={32} />
            Dashboard
          </h1>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            Live Monitoring • {Object.keys(students).length} Students Active
          </p>
        </div>
        <button
          onClick={onLogout}
          className="px-6 py-2.5 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg font-medium text-gray-700 transition-colors shadow-sm"
        >
          End Class
        </button>
      </header>

      {/* Student Grid */}
      <div className="student-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Object.values(students).map((student) => (
          <div
            key={student.studentId}
            className={`rounded-xl border p-4 shadow-sm transition-all duration-300 ${getCardStyle(student.raw_state || student.state)}`}
          >
            {/* Status Card Content */}
            <div className="flex flex-col gap-4">
              {/* Card Header */}
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/50 border border-gray-200 flex items-center justify-center font-bold text-gray-700 text-sm shadow-sm">
                    {student.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 leading-tight">{student.name}</h3>
                    <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">ID: {student.studentId}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider shadow-sm border ${getBadgeStyle(student.raw_state || student.state)}`}>
                  {student.raw_state || student.state}
                </span>
              </div>

              {/* Large Status Text */}
              <div className="py-2 text-center">
                <div className="text-sm font-medium text-gray-500 mb-1">Current Status</div>
                <div className={`text-xl font-bold ${getBadgeStyle(student.raw_state || student.state).replace('bg-', 'text-').split(' ')[1]}`}>
                  {student.raw_state || student.state}
                </div>
              </div>

              {/* Metrics Bars */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-[10px] text-gray-600 mb-1">
                    <span>Engagement</span>
                    <span className="font-medium">{Math.round(student.engagement_score * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${student.engagement_score < 0.5 ? 'bg-red-500' : 'bg-blue-500'}`}
                      style={{ width: `${student.engagement_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>

            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {
        Object.keys(students).length === 0 && (
          <div className="student-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <Users size={64} className="mb-4 opacity-20" />
            <p className="text-lg font-medium text-gray-500">No students connected</p>
            <p className="text-sm">Ask students to join the session ID: CLASS_A</p>
          </div>
        )
      }
    </div>
  );
};
export default TeacherDashboard;
