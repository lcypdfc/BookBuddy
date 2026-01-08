import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import MainApp from "./MainApp"; 

export default function App() {
  const [userId, setUserId] = useState(() => {
    return localStorage.getItem("userId") || "";
  });

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            userId ? (
              <MainApp userId={userId} setUserId={setUserId} />
            ) : (
              <Login setUserId={setUserId} />
            )
          }
        />
      </Routes>
    </Router>
  );
}
