from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import trading_algo  # Import your trading algorithm

# Define FastAPI app
app = FastAPI()

# Define request model
class StockRequest(BaseModel):
    stock_symbol: str

@app.post("/run-trading-algorithm/")
async def run_trading_algorithm_endpoint(request: StockDataRequest):
    try:
        # Call the run_trading_algorithm function from your trading_algo module
        # The stock_data is passed as a JSON string fetched from the React app
        trading_algo.run_trading_algorithm(request.stock_data)
        return {"message": "Trading algorithm executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))