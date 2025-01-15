from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import trading_algo  # Import your trading algorithm
from fastapi.middleware.cors import CORSMiddleware


# Define FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bug-free-palm-tree-vr7pqxxw5qwhw5rw-3000.app.github.dev/"],  # Change this to specific domains if necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class StockDataRequest(BaseModel):
    json: dict

@app.post("/run_trading_algorithm/")
async def run_trading_algorithm_endpoint(request: StockDataRequest):
    try:
        # Call the run_trading_algorithm function from your trading_algo module
        # The stock_data is passed as a JSON string fetched from the React app
        trading_algo.run_trading_algorithm(request.json)
        return {"message": "Trading algorithm executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))