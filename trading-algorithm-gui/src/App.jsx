import React, { useState } from "react";
import yahooStockPrices from "yahoo-stock-prices";

const App = () => {
  // State variables
  const [stockName, setStockName] = useState(""); // For the stock ticker input
  const [stockData, setStockData] = useState(null); // For the fetched stock data
  const [error, setError] = useState(""); // For error messages

  // Handle stock ticker input
  const handleInputChange = (e) => {
    setStockName(e.target.value.toUpperCase()); // Ensure ticker is uppercase
  };

  // Fetch stock data
  const fetchStockData = async (ticker) => {
    try {
      setError(""); // Clear previous error messages
      setStockData(null); // Clear previous stock data
      const price = await yahooStockPrices.getCurrentPrice(ticker); // Fetch the current stock price

      // (Optional) Fetch historical data as well
      const historicalPrices = await yahooStockPrices.getHistoricalPrices(
        0, // Start month (January = 0)
        1, // Start day
        2023, // Start year
        11, // End month (December = 11)
        31, // End day
        2023, // End year
        ticker, // Stock ticker
        "1d" // Interval (1 day)
      );

      setStockData({
        currentPrice: price,
        historicalPrices: historicalPrices,
      });
    } catch (err) {
      console.error("Error fetching stock data:", err);
      setError("Unable to fetch stock data. Please check the stock ticker.");
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!stockName) {
      setError("Please enter a valid stock ticker.");
      return;
    }
    fetchStockData(stockName);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Stock Market Data Fetcher</h1>

      {/* Input Section */}
      <form onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
        <label>
          Enter Stock Ticker:
          <input
            type="text"
            value={stockName}
            onChange={handleInputChange}
            placeholder="e.g., AAPL"
            style={{
              marginLeft: "10px",
              padding: "5px",
              fontSize: "16px",
            }}
          />
        </label>
        <button
          type="submit"
          style={{
            marginLeft: "10px",
            padding: "5px 10px",
            fontSize: "16px",
            cursor: "pointer",
          }}
        >
          Fetch Data
        </button>
      </form>

      {/* Error Message */}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* Stock Data Section */}
      {stockData ? (
        <div style={{ border: "1px solid #ccc", padding: "10px" }}>
          <h2>Stock Data for {stockName}</h2>
          <p>
            <strong>Current Price:</strong> ${stockData.currentPrice.toFixed(2)}
          </p>
          <h3>Historical Prices</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Open</th>
                <th>High</th>
                <th>Low</th>
                <th>Close</th>
              </tr>
            </thead>
            <tbody>
              {stockData.historicalPrices.map((price, index) => (
                <tr key={index}>
                  <td>{new Date(price.date * 1000).toLocaleDateString()}</td>
                  <td>${price.open.toFixed(2)}</td>
                  <td>${price.high.toFixed(2)}</td>
                  <td>${price.low.toFixed(2)}</td>
                  <td>${price.close.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>No stock data available. Please fetch data for a stock.</p>
      )}
    </div>
  );
};

export default App;


