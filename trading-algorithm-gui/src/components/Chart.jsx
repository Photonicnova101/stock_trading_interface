// src/components/Chart.js
import React from "react";
import { Line } from "react-chartjs-2";

function Chart({ data }) {
  const chartData = {
    labels: data.map((item) => item.time),
    datasets: [
      {
        label: "Stock Price",
        data: data.map((item) => item.price),
        borderColor: "blue",
        fill: false,
      },
    ],
  };

  return (
    <div>
      <Line data={chartData} />
    </div>
  );
}

export default Chart;
