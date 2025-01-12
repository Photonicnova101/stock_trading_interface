// src/components/ControlButtons.js
import React from "react";

function ControlButtons({ onStart, onStop, onReset }) {
  return (
    <div>
      <button onClick={onStart}>Start</button>
      <button onClick={onStop}>Stop</button>
      <button onClick={onReset}>Reset</button>
    </div>
  );
}

export default ControlButtons;
