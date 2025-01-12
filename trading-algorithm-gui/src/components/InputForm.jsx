// src/components/InputForm.js
import React, { useState } from "react";

function InputForm({ onSubmit }) {
  const [stockSymbol, setStockSymbol] = useState("");
  const [capital, setCapital] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ stockSymbol, capital });
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Stock Symbol:
        <input
          type="text"
          value={stockSymbol}
          onChange={(e) => setStockSymbol(e.target.value)}
        />
      </label>
      <label>
        Capital ($):
        <input
          type="number"
          value={capital}
          onChange={(e) => setCapital(e.target.value)}
        />
      </label>
      <button type="submit">Run Algorithm</button>
    </form>
  );
}

export default InputForm;
