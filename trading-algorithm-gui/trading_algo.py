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
import matplotlib.pyplot as plt

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- Pattern Detection Placeholders ---
def detect_rising_wedge(df):
    df['RisingWedgeSignal'] = 0
    if len(df) > 10:
        df.loc[df.index[::20], 'RisingWedgeSignal'] = 2  # Buy
        df.loc[df.index[10::20], 'RisingWedgeSignal'] = 1  # Sell
    return df

def detect_falling_wedge(df):
    df['FallingWedgeSignal'] = 0
    if len(df) > 10:
        df.loc[df.index[::25], 'FallingWedgeSignal'] = 2
        df.loc[df.index[12::25], 'FallingWedgeSignal'] = 1
    return df

def detect_cup_and_handle(df):
    df['CupHandleSignal'] = 0
    if len(df) > 10:
        df.loc[df.index[::30], 'CupHandleSignal'] = 2
        df.loc[df.index[15::30], 'CupHandleSignal'] = 1
    return df

# --- Pattern Strategy Classes ---
class RisingWedgeStrat(Strategy):
    def init(self):
        self.signal = self.data.df['RisingWedgeSignal']

    def next(self):
        if self.signal[-1] == 2 and not self.position:
            self.buy()
        elif self.signal[-1] == 1 and self.position:
            self.position.close()

class FallingWedgeStrat(Strategy):
    def init(self):
        self.signal = self.data.df['FallingWedgeSignal']

    def next(self):
        if self.signal[-1] == 2 and not self.position:
            self.buy()
        elif self.signal[-1] == 1 and self.position:
            self.position.close()

class CupHandleStrat(Strategy):
    def init(self):
        self.signal = self.data.df['CupHandleSignal']

    def next(self):
        if self.signal[-1] == 2 and not self.position:
            self.buy()
        elif self.signal[-1] == 1 and self.position:
            self.position.close()

# Define FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-netlify-app.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Models ---
class StockInput(BaseModel):
    stockKey: str
    strategy: str = "default"

@app.post("/run_trading_algorithm/")
async def run_trading_algorithm_endpoint(stock: StockInput):
    try:
        result = run_trading_algorithm(stock.stockKey, stock.strategy)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_candlestick_plot/")
async def run_candlestick_plot_endpoint(stock: StockInput):
    try:
        candlestick_image = plot_candlestick_with_signals(stock.stockKey, 0, 500)
        return {"candlestick_plot": candlestick_image}
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
    df.drop(columns=['Dividends', 'Stock Splits'], inplace=True, errors='ignore')
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
        self.signal1 = self.I(lambda: SIGNAL(self.data.df))

    def next(self):
        super().next()
        if self.signal1 == 2 and not self.position:
            current_close = self.data.Close[-1]
            sl = current_close - self.slperc * current_close
            tp = current_close + self.tpperc * current_close
            self.buy(size=self.mysize, sl=sl, tp=tp)
        elif self.signal1 == 1 and not self.position:
            current_close = self.data.Close[-1]
            sl = current_close + self.slperc * current_close
            tp = current_close - self.tpperc * current_close
            self.sell(size=self.mysize, sl=sl, tp=tp)

def fetch_stock_data(ticker, interval='1d', start_date=None, end_date=None):
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

def run_trading_algorithm(stockKey, strategy="default"):
    stock_data = fetch_stock_data(
        ticker=stockKey, 
        interval="1d", 
        start_date="2000-01-01", 
        end_date="2024-07-01"
    )
    stock_data.to_csv("stock_data.csv", index=False)
    df = read_csv_to_dataframe("stock_data.csv")

    if strategy == "rising_wedge":
        df = detect_rising_wedge(df)
        df = add_pointpos_column(df, "RisingWedgeSignal")
        strat_class = RisingWedgeStrat
    elif strategy == "falling_wedge":
        df = detect_falling_wedge(df)
        df = add_pointpos_column(df, "FallingWedgeSignal")
        strat_class = FallingWedgeStrat
    elif strategy == "cup_handle":
        df = detect_cup_and_handle(df)
        df = add_pointpos_column(df, "CupHandleSignal")
        strat_class = CupHandleStrat
    else:
        df = add_total_signal(df)
        df = add_pointpos_column(df, "TotalSignal")
        strat_class = MyStrat

    results = []
    bt = Backtest(df, strat_class, cash=5000, margin=1/5, commission=0.0002)
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
    return json.dumps(results_dict)

def plot_candlestick_with_signals(stockKey, start_index, num_rows):
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
    fig, ax = plt.subplots()
    ax.plot(df_subset.index, df_subset['Close'], label='Close Price')
    ax.scatter(df_subset.index, df_subset['pointpos'], color='purple', label='Entry Points')
    ax.set_title('Candlestick Plot with Signals')
    ax.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64