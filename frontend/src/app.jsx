import React, { useState } from "react";
import { Activity, Users, Monitor } from "lucide-react";
import StudentPortal from "./components/studentport";
import TeacherDashboard from "./components/teacher";

export default function App() {
  const [role, setRole] = useState(null);
  const [userData, setUserData] = useState(null);
  const handleStudentLogin = () => {
    const randomId = Math.random().toString(36).substr(2, 5).toUpperCase();
    const randomName = "Student " + Math.floor(Math.random() * 100);
    setUserData({ id: randomId, name: randomName });
    setRole("student");
  };
  const handleTeacherLogin = () => {
    setRole("teacher");
  };
  if (role === "student") {
    return (
      <StudentPortal
        studentId={userData.id}
        name={userData.name}
        onLogout={() => setRole(null)}
      />
    );
  }
  if (role === "teacher") {
    return <TeacherDashboard onLogout={() => setRole(null)} />;
  }
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      {/* FIXES APPLIED:
        1. Removed 'h-[420px]' so the box fits content naturally.
        2. Increased padding to 'p-8' to push inner boxes away from the edge.
      */}
      <div className="w-[500px] h-[500px] flex flex-col border border-gray-300 bg-white p-12 rounded-xl mx-auto shadow-lg relative">

        {/* Top Section: Logo & Title */}
        <div className="flex-1 flex flex-col justify-center items-center">
          <div className="bg-blue-50 p-3 rounded-full mb-4">
            <Activity size={32} className="text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            SmartSession
          </h1>
          <p className="text-gray-500 font-medium">
            ML-Powered Proctoring Platform
          </p>
        </div>

        {/* Middle Section: Actions */}
        <div className="space-y-4 w-full mb-8">
          <button
            onClick={handleStudentLogin}
            className="w-full border-2 border-gray-100 hover:border-blue-100 bg-gray-50 hover:bg-blue-50 p-4 rounded-xl flex items-center gap-4 transition-all duration-200 group"
          >
            <div className="bg-white p-2 rounded-lg shadow-sm group-hover:scale-110 transition-transform">
              <Users size={24} className="text-blue-600" />
            </div>
            <div className="text-left">
              <div className="font-bold text-gray-800">Join as Student</div>
              <div className="text-xs text-gray-500">Share camera & analytics</div>
            </div>
          </button>

          <button
            onClick={handleTeacherLogin}
            className="w-full border-2 border-gray-100 hover:border-indigo-100 bg-gray-50 hover:bg-indigo-50 p-4 rounded-xl flex items-center gap-4 transition-all duration-200 group"
          >
            <div className="bg-white p-2 rounded-lg shadow-sm group-hover:scale-110 transition-transform">
              <Monitor size={24} className="text-indigo-600" />
            </div>
            <div className="text-left">
              <div className="font-bold text-gray-800">Teacher Dashboard</div>
              <div className="text-xs text-gray-500">Monitor class in real-time</div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="text-center text-[10px] uppercase tracking-widest text-gray-400 font-semibold">
          Smartsession Local Testing Mode
        </div>

      </div>
    </div>
  );
}