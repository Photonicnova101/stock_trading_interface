const express = require("express");
const cors = require("cors");
const yahooFinance = require("yahoo-finance2").default;

const app = express();
app.use(cors());

// Endpoint to fetch stock data
app.get("/api/stock/:ticker", async (req, res) => {
  const ticker = req.params.ticker;
  try {
    const data = await yahooFinance.quote(ticker); // Fetch data from Yahoo Finance
    res.json(data); // Send data to frontend
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch stock data" });
  }
});

const PORT = 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
