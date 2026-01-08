// pages/Login.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login({ setUserId }) {
  const [inputId, setInputId] = useState("");
  const navigate = useNavigate();

  const handleLogin = () => {
    const trimmed = inputId.trim();
    if (!trimmed) {
      alert("Please enter a valid User ID.");
      return;
    }

    localStorage.setItem("userId", trimmed);
    setUserId(trimmed);     
    navigate("/");  
  };

  return (
    <div className="container">
      <h2>Welcome to BookBuddy</h2>
      <label>User ID:</label>
      <input
        type="text"
        className="custom-input"
        value={inputId}
        onChange={(e) => setInputId(e.target.value)}
        placeholder="Enter your user ID"
      />
      <button className="custom-button" onClick={handleLogin}>
        Log In
      </button>
    </div>
  );
}
