import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from backtesting import Strategy
from backtesting import Backtest

def load_json(json_data):  
    data = json.loads(json_data)
    df = pd.DataFrame(data)
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
    df['TotalSignal'] = df.progress_apply(lambda row: total_signal(df, row.name), axis=1)
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
        self.signal1 = self.I(SIGNAL)  # Assuming SIGNAL is a function that returns signals

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

def run_trading_algorithm(json):
    df = load_json(json)
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

    agg_returns = sum([r["Return [%]"] for r in results])
    num_trades = sum([r["# Trades"] for r in results])
    max_drawdown = min([r["Max. Drawdown [%]"] for r in results])
    avg_drawdown = sum([r["Avg. Drawdown [%]"] for r in results]) / len(results)

    win_rate = sum([r["Win Rate [%]"] for r in results]) / len(results)
    best_trade = max([r["Best Trade [%]"] for r in results])
    worst_trade = min([r["Worst Trade [%]"] for r in results])
    avg_trade = sum([r["Avg. Trade [%]"] for r in results]) / len(results)
    #max_trade_duration = max([r["Max. Trade Duration"] for r in results])
    #avg_trade_duration = sum([r["Avg. Trade Duration"] for r in results]) / len(results)

    #print(f"Maximum Trade Duration: {max_trade_duration} days")
    #print(f"Average Trade Duration: {avg_trade_duration:.2f} days")
    results = {
        "Aggregated Returns": f"{agg_returns:.2f}%",
        "Number of Trades": num_trades,
        "Maximum Drawdown": f"{max_drawdown:.2f}%",
        "Average Drawdown": f"{avg_drawdown:.2f}%",
        "Win Rate": f"{win_rate:.2f}%",
        "Best Trade": f"{best_trade:.2f}%",
        "Worst Trade": f"{worst_trade:.2f}%",
        "Average Trade": f"{avg_trade:.2f}%"
    }

    # Convert the dictionary to a JSON string
    return json.dumps(results)