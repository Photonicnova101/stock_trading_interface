// src/App.js
import React, { useState } from "react";
import InputForm from "./components/InputForm.jsx";
import Chart from "./components/Chart.jsx";
import Logs from "./components/Logs.jsx";
import ControlButtons from "./components/ControlButtons.jsx";

function App() {
  const [chartData, setChartData] = useState([]);
  const [logs, setLogs] = useState([]);

  const handleRunAlgorithm = (params) => {
    const { stockSymbol, capital } = params;
    setLogs((prevLogs) => [...prevLogs, `Running algorithm for ${stockSymbol} with $${capital}`]);
    // Simulate live data update
    const newData = Array.from({ length: 10 }, (_, i) => ({
      time: `Day ${i + 1}`,
      price: Math.random() * 100 + 100,
    }));
    setChartData(newData);
  };

  const handleStart = () => setLogs((prevLogs) => [...prevLogs, "Algorithm started"]);
  const handleStop = () => setLogs((prevLogs) => [...prevLogs, "Algorithm stopped"]);
  const handleReset = () => {
    setChartData([]);
    setLogs([]);
  };

  return (
    <div>
      <h1>Trading Algorithm GUI</h1>
      <InputForm onSubmit={handleRunAlgorithm} />
      <ControlButtons onStart={handleStart} onStop={handleStop} onReset={handleReset} />
      <Chart data={chartData} />
      <Logs logs={logs} />
    </div>
  );
}

export default App;
