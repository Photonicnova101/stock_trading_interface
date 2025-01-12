// src/components/Logs.js
import React from "react";

function Logs({ logs }) {
  return (
    <div>
      <h3>Logs</h3>
      <div style={{ height: "200px", overflowY: "scroll", border: "1px solid #ccc" }}>
        {logs.map((log, index) => (
          <p key={index}>{log}</p>
        ))}
      </div>
    </div>
  );
}

export default Logs;
