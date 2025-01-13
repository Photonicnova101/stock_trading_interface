import React, { useState } from "react";
import axios from "axios";

const App = () => {
  const [stockKeyword, setStockKeyword] = useState(""); // User input for stock keyword
  const [stockData, setStockData] = useState(null);    // To store fetched stock data
  const [error, setError] = useState("");              // Error messages
  const [isLoading, setIsLoading] = useState(false);   // Loading state
  const [algorithmResults, setAlgorithmResults] = useState(null);
  
  
  // Function to handle input change
  const handleInputChange = (e) => {
    setStockKeyword(e.target.value.trim().toUpperCase()); // Convert to uppercase for standardization
  };

  // Function to fetch stock data
  const fetchStockData = async (keyword) => {
    if (!keyword) {
      setError("Please enter a valid stock keyword.");
      return;
    }

    setIsLoading(true); // Start loading
    setError(""); // Clear previous errors
    setStockData(null); // Clear previous data

    const options = {
      method: 'GET',
      url: `https://yahoo-finance15.p.rapidapi.com/api/v1/markets/quote`,
      params: { 
        ticker: 'AAPL',
        type: 'STOCKS' 
      },
      headers: {
        "x-rapidapi-key": "05975bb442mshf9d23a87d81dd7fp1061eejsn73176106ee6d",
        "x-rapidapi-host": "yahoo-finance15.p.rapidapi.com", // Replace with your actual API key
      },
    }
    try {
      // Make the API call using Axios
      const response = await axios.request(options);
      console.log(response.data);
      // Update state with fetched data
      setStockData(response.data);
    } catch (err) {
      console.error(err);
      if (err.response) {
        console.error("Response Error:", err.response.data); // API-specific error
        console.error("Status Code:", err.response.status); // HTTP status code
      } else if (err.request) {
        console.error("No Response:", err.request); // No response received
      } else {
        console.error("Error Message:", err.message); // Other errors
      }
      setError("Unable to fetch stock data. Please try again later.");
    } finally {
      setIsLoading(false); // Stop loading
    }
  };

  //Getting algo results
  const fetchAlgorithmResults = async () => {
    try {
      // Clear previous error messages
      setError("");

      // Make an API call to the FastAPI backend
      const response = await axios.post("http://127.0.0.1:8000/run_trading_algorithm", {
        stock_symbol: stockKeyword, // Pass the stock symbol as JSON in the request body
      });

      // Save the results returned by the backend
      setAlgorithmResults(response.data.results);
    } catch (err) {
      // If the request fails, display an error message
      setError(err.response?.data?.detail || "An error occurred");
    }
  };



  // Form submission handler
  const handleSubmit = (e) => {
    e.preventDefault(); // Prevent page reload
    fetchStockData(stockKeyword); // Fetch stock data using the keyword
    fetchAlgorithmResults(stockKeyword)
  };
  
  return (
    <div style={{ padding: "20px" }}>
      <h1>Stock Data Fetcher</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter stock keyword (e.g., AAPL)"
          value={stockKeyword}
          onChange={handleInputChange}
        />
        <button type="submit">Search</button>
      </form>

      {/* Display loading indicator */}
      {isLoading && <p>Loading...</p>}

      {/* Display error messages */}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* Display fetched stock data */}
      {stockData && (
        <div>
          <h2>Stock Data</h2>
          <pre>{JSON.stringify(stockData, null, 2)}</pre>
          <h3>Results of trading strategy</h3>
          {/* Display results */}
      {algorithmResults && (
        <div>
          <h2>Results:</h2>
          <pre>{JSON.stringify(algorithmResults, null, 2)}</pre>
        </div>
      )}

      {/* Display error message */}
      {error && <div style={{ color: "red" }}>Error: {error}</div>}
        </div>
      )}
    </div>
  );
};

export default App;
