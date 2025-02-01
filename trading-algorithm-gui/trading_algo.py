import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from backtesting import Strategy
from backtesting import Backtest
import yfinance as yf
import io
import base64
import kaleido


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel# Import your trading algorithm
from fastapi.middleware.cors import CORSMiddleware

# Define FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class StockInput(BaseModel):
    stockKey: str

@app.post("/run_trading_algorithm/")
async def run_trading_algorithm_endpoint(stock: StockInput):
    try:
        # Call the run_trading_algorithm function from your trading_algo module
        # The stock_data is passed as a JSON string fetched from the React app
        result = run_trading_algorithm(stock.stockKey)
        candlestick_image = plot_candlestick_with_signals(stock.stockKey, 0, 100)
        return {"result": result, "candlestick_plot": candlestick_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def read_csv_to_dataframe(file_path):
    df = pd.read_csv(file_path)
    df.rename(columns={
    'Date': 'Gmt time',
    'Open': 'Open',
    'High': 'High',
    'Low': 'Low',
    'Close': 'Close',
    'Volume': 'Volume'
    }, inplace=True)
    
    df.drop(columns=['Dividends', 'Stock Splits'], inplace=True)
    df['Gmt time'] = pd.to_datetime(df['Gmt time'], errors='coerce', utc=True)
    df = df.dropna(subset=['Gmt time'])  # Remove rows with invalid datetimes
    df['Gmt time'] = df['Gmt time'].dt.strftime('%d.%m.%Y %H:%M:%S.000')
    
    df["Gmt time"] = df["Gmt time"].str.replace(".000", "")
    df['Gmt time'] = pd.to_datetime(df['Gmt time'], format='%d.%m.%Y %H:%M:%S')
    df = df[df.High != df.Low]
    df.set_index("Gmt time", inplace=True)

    return df

def total_signal(df, current_candle):
    current_pos = df.index.get_loc(current_candle)
    
    # Buy condition
    c1 = df['High'].iloc[current_pos] > df['High'].iloc[current_pos-1]
    c2 = df['High'].iloc[current_pos-1] > df['Low'].iloc[current_pos]
    c3 = df['Low'].iloc[current_pos] > df['High'].iloc[current_pos-2]
    c4 = df['High'].iloc[current_pos-2] > df['Low'].iloc[current_pos-1]
    c5 = df['Low'].iloc[current_pos-1] > df['High'].iloc[current_pos-3]
    c6 = df['High'].iloc[current_pos-3] > df['Low'].iloc[current_pos-2]
    c7 = df['Low'].iloc[current_pos-2] > df['Low'].iloc[current_pos-3]

    if c1 and c2 and c3 and c4 and c5 and c6 and c7:
        return 2

    # Symmetrical conditions for short (sell condition)
    c1 = df['Low'].iloc[current_pos] < df['Low'].iloc[current_pos-1]
    c2 = df['Low'].iloc[current_pos-1] < df['High'].iloc[current_pos]
    c3 = df['High'].iloc[current_pos] < df['Low'].iloc[current_pos-2]
    c4 = df['Low'].iloc[current_pos-2] < df['High'].iloc[current_pos-1]
    c5 = df['High'].iloc[current_pos-1] < df['Low'].iloc[current_pos-3]
    c6 = df['Low'].iloc[current_pos-3] < df['High'].iloc[current_pos-2]
    c7 = df['High'].iloc[current_pos-2] < df['High'].iloc[current_pos-3]

    if c1 and c2 and c3 and c4 and c5 and c6 and c7:
        return 1

    return 0

def add_total_signal(df):
    df['TotalSignal'] = df.apply(lambda row: total_signal(df, row.name), axis=1)
    return df

def add_pointpos_column(df, signal_column):
    """
    Adds a 'pointpos' column to the DataFrame to indicate the position of support and resistance points.
    
    Parameters:
    df (DataFrame): DataFrame containing the stock data with the specified SR column, 'Low', and 'High' columns.
    sr_column (str): The name of the column to consider for the SR (support/resistance) points.
    
    Returns:
    DataFrame: The original DataFrame with an additional 'pointpos' column.
    """
    def pointpos(row):
        if row[signal_column] == 2:
            return row['Low'] - 1e-4
        elif row[signal_column] == 1:
            return row['High'] + 1e-4
        else:
            return np.nan

    df['pointpos'] = df.apply(lambda row: pointpos(row), axis=1)
    return df

def SIGNAL(df):
    return df.TotalSignal

class MyStrat(Strategy):
    mysize = 0.1  # Trade size
    slperc = 0.04
    tpperc = 0.02

    def init(self):
        super().init()
        self.signal1 = self.I(lambda: SIGNAL(self.data.df))  # Assuming SIGNAL is a function that returns signals

    def next(self):
        super().next()
         
        if self.signal1 == 2 and not self.position:
            # Open a new long position with calculated SL and TP
            current_close = self.data.Close[-1]
            sl = current_close - self.slperc * current_close  # SL at 4% below the close price
            tp = current_close + self.tpperc * current_close  # TP at 2% above the close price
            self.buy(size=self.mysize, sl=sl, tp=tp)

        elif self.signal1 == 1 and not self.position:
            # Open a new short position, setting SL based on a strategy-specific requirement
            current_close = self.data.Close[-1]
            sl = current_close + self.slperc * current_close  # SL at 4% below the close price
            tp = current_close - self.tpperc * current_close  # TP at 2% above the close price
            self.sell(size=self.mysize, sl=sl, tp=tp)

def fetch_stock_data(ticker, interval='1d', start_date=None, end_date=None):
    """
    Fetch stock data for a specific ticker from Yahoo Finance.

    Args:
        ticker (str): Stock ticker symbol (e.g., "AAPL").
        interval (str): Data interval ('1m', '5m', '1h', etc.).
        start_date (str): Start date for fetching data (YYYY-MM-DD).
        end_date (str): End date for fetching data (YYYY-MM-DD).

    Returns:
        pd.DataFrame: DataFrame containing the stock data in OHLCV format.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(interval=interval, start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data.rename(columns={
        "Datetime": "Gmt time", 
        "Open": "Open", 
        "High": "High", 
        "Low": "Low", 
        "Close": "Close", 
        "Volume": "Volume"
    }, inplace=True)

    return data
    

def run_trading_algorithm(stockKey):
    stock_data = fetch_stock_data(
        ticker=stockKey, 
        interval="1d", 
        start_date="2000-01-01", 
        end_date="2024-07-01"
    )
    stock_data.to_csv("stock_data.csv", index=False)
    df = read_csv_to_dataframe("stock_data.csv")
    df = add_total_signal(df)
    df = add_pointpos_column(df, "TotalSignal")

    results = []

    bt = Backtest(df, MyStrat, cash=5000, margin=1/5, commission=0.0002)
    stats = bt.optimize(slperc=[i/100 for i in range(1, 8)],
                                tpperc=[i/100 for i in range(1, 8)],
                    maximize='Return [%]', max_tries=3000,
                        random_state=0,
                        return_heatmap=True)
    results.append(stats)

    detailed_stats = stats[0]
    
    
    agg_returns = detailed_stats["Return [%]"]
    num_trades = detailed_stats["# Trades"]
    max_drawdown = detailed_stats["Max. Drawdown [%]"]
    avg_drawdown = detailed_stats["Avg. Drawdown [%]"]
    win_rate = detailed_stats["Win Rate [%]"]
    best_trade = detailed_stats["Best Trade [%]"]
    worst_trade = detailed_stats["Worst Trade [%]"]
    avg_trade = detailed_stats["Avg. Trade [%]"]

    # Create a JSON-compatible results dictionary
    results_dict = {
        "Aggregated Returns": f"{agg_returns:.2f}%",
        "Number of Trades": num_trades,
        "Maximum Drawdown": f"{max_drawdown:.2f}%",
        "Average Drawdown": f"{avg_drawdown:.2f}%",
        "Win Rate": f"{win_rate:.2f}%",
        "Best Trade": f"{best_trade:.2f}%",
        "Worst Trade": f"{worst_trade:.2f}%",
        "Average Trade": f"{avg_trade:.2f}%",
    }
    
    # Convert the dictionary to a JSON string
    return json.dumps(results_dict)

def plot_candlestick_with_signals(stockKey, start_index, num_rows):
    """
    Plots a candlestick chart with signal points.
    
    Parameters:
    df (DataFrame): DataFrame containing the stock data with 'Open', 'High', 'Low', 'Close', and 'pointpos' columns.
    start_index (int): The starting index for the subset of data to plot.
    num_rows (int): The number of rows of data to plot.
    
    Returns:
    None
    """
    stock_data = fetch_stock_data(
        ticker=stockKey, 
        interval="1d", 
        start_date="2000-01-01", 
        end_date="2024-07-01"
    )
    stock_data.to_csv("stock_data.csv", index=False)
    df = read_csv_to_dataframe("stock_data.csv")
    df = add_total_signal(df)
    df = add_pointpos_column(df, "TotalSignal")

    df_subset = df[start_index:start_index + num_rows]
    
    fig = make_subplots(rows=1, cols=1)
    
    fig.add_trace(go.Candlestick(x=df_subset.index,
                                 open=df_subset['Open'],
                                 high=df_subset['High'],
                                 low=df_subset['Low'],
                                 close=df_subset['Close'],
                                 name='Candlesticks'),
                  row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df_subset.index, y=df_subset['pointpos'], mode="markers",
                            marker=dict(size=10, color="MediumPurple", symbol='circle'),
                            name="Entry Points"),
                  row=1, col=1)
    
    buf = io.BytesIO()
    fig.write_image(buf, format='png', engine='kaleido')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64