import pandas as pd
import numpy as np
from datetime import timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sklearn.linear_model import LinearRegression


def _parse_interval_to_timedelta(interval: str) -> timedelta:
    """Convert Binance-style interval to timedelta (approximate)."""
    if interval.endswith('m'):
        minutes = int(interval[:-1])
        return timedelta(minutes=minutes)
    if interval.endswith('h'):
        hours = int(interval[:-1])
        return timedelta(hours=hours)
    if interval.endswith('d'):
        days = int(interval[:-1])
        return timedelta(days=days)
    # default daily
    return timedelta(days=1)


def run_backtest(candles: List[Dict[str, Any]], short_window: int = 10, long_window: int = 50,
                 initial_capital: float = 10000.0, commission_pct: float = 0.001,
                 slippage: float = 0.0005, forecast_days: int = 5, interval: str = '1d') -> Dict[str, Any]:
    """Run a simple SMA crossover backtest and linear-regression prediction.

    Args:
        candles: list of dicts with keys: timestamp (datetime), open, high, low, close, volume
    Returns:
        dict with candles, trades, equity, metrics, forecast_points
    """
    if not candles:
        return {
            'candles': [],
            'trades': [],
            'equity': [],
            'metrics': {},
            'forecast_points': [],
        }

    # Build DataFrame
    df = pd.DataFrame([{
        'timestamp': c['timestamp'],
        'open': float(c['open']),
        'high': float(c['high']),
        'low': float(c['low']),
        'close': float(c['close']),
        'volume': float(c.get('volume', 0)),
    } for c in candles])

    df = df.sort_values('timestamp').reset_index(drop=True)

    # Indicators
    df['SMA_Short'] = df['close'].rolling(window=short_window, min_periods=1).mean()
    df['SMA_Long'] = df['close'].rolling(window=long_window, min_periods=1).mean()

    balance = float(initial_capital)
    position = 0.0
    position_price = None
    trades = []
    equity = [balance] * len(df)

    for i in range(1, len(df)):
        prev_short = df.at[i - 1, 'SMA_Short']
        prev_long = df.at[i - 1, 'SMA_Long']
        cur_short = df.at[i, 'SMA_Short']
        cur_long = df.at[i, 'SMA_Long']
        price = df.at[i, 'close']

        # Buy signal
        if cur_short > cur_long and prev_short <= prev_long and position == 0:
            # buy with all balance
            size = (balance * (1 - commission_pct)) / (price * (1 + slippage))
            position = size
            position_price = price
            balance = 0.0
            trades.append({'type': 'BUY', 'timestamp': df.at[i, 'timestamp'].isoformat(), 'price': price, 'size': size})

        # Sell signal
        elif cur_short < cur_long and prev_short >= prev_long and position > 0:
            sell_price = price * (1 - slippage)
            proceeds = position * sell_price * (1 - commission_pct)
            pnl = proceeds - (position * position_price if position_price is not None else 0)
            trades.append({'type': 'SELL', 'timestamp': df.at[i, 'timestamp'].isoformat(), 'price': sell_price, 'size': position, 'pnl': pnl})
            balance = proceeds
            position = 0.0
            position_price = None

        # Update equity
        current_val = balance + (position * price)
        equity[i] = current_val

    # Finalize: if position still open, mark as value at last price
    final_equity = equity[-1]

    # Metrics
    total_return = ((final_equity - initial_capital) / initial_capital) * 100
    num_trades = sum(1 for t in trades if t['type'] == 'SELL')

    # Compute simple max drawdown
    equity_series = pd.Series(equity)
    roll_max = equity_series.cummax()
    drawdown = (equity_series - roll_max) / roll_max
    max_drawdown = float(drawdown.min() if not drawdown.empty else 0.0) * 100

    metrics = {
        'total_return_pct': float(total_return),
        'num_trades': int(num_trades),
        'max_drawdown_pct': float(max_drawdown),
    }

    # Forecast using linear regression on recent closes
    lookback = min(50, len(df))
    subset = df.tail(lookback).copy()
    subset['idx'] = np.arange(len(subset))
    X = subset[['idx']].values
    y = subset['close'].values
    lr = LinearRegression()
    lr.fit(X, y)

    future_idx = np.arange(len(subset), len(subset) + forecast_days).reshape(-1, 1)
    future_prices = lr.predict(future_idx)

    # construct future timestamps
    delta = _parse_interval_to_timedelta(interval)
    last_time = df['timestamp'].iloc[-1]
    forecast_points = []
    for i in range(forecast_days):
        ft = last_time + delta * (i + 1)
        price = float(future_prices[i])
        upper = price * 1.02
        lower = price * 0.98
        forecast_points.append({'date': ft.isoformat(), 'price': price, 'confidence_upper': upper, 'confidence_lower': lower})

    # Prepare output structures
    out_candles = [{
        'timestamp': r['timestamp'].isoformat(),
        'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close'], 'volume': r['volume']
    } for _, r in df.iterrows()]

    out_equity = [{'timestamp': df.at[i, 'timestamp'].isoformat(), 'equity': float(e)} for i, e in enumerate(equity)]

    return {
        'candles': out_candles,
        'trades': trades,
        'equity': out_equity,
        'metrics': metrics,
        'forecast_points': forecast_points,
    }
