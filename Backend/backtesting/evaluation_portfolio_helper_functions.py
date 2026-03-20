import yfinance as yf
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Get SPY data as benchmark for comparison, to evaluate our strategy performance against the overall market.
# ---------------------------------------------------------------------------
def load_spy(start_date, end_date):
    spy_raw = yf.download("SPY", start=start_date, end=end_date, auto_adjust=True)
    
    # yfinance returns MultiIndex columns like ("Close", "SPY") — flatten to single level
    spy_raw.columns = spy_raw.columns.get_level_values(0)
    
    spy = spy_raw[["Close"]].rename(columns={"Close": "spy_adj_close"})
    spy.index = pd.to_datetime(spy.index).date
    spy.index.name = "date"
    spy = spy.reset_index()

    spy["spy_daily_return"] = spy["spy_adj_close"].pct_change()
    spy["spy_cum_return"]   = (spy["spy_adj_close"] / spy["spy_adj_close"].iloc[0]) - 1

    return spy

# ---------------------------------------------------------------------------
# Get comparison data between portfolio and SPY
# ---------------------------------------------------------------------------
def get_comparison_df(portfolio_df, spy_df):
    comparison = pd.merge(
        portfolio_df, 
        spy_df[["date", "spy_adj_close", "spy_daily_return", "spy_cum_return"]], 
        on="date", 
        how="left")
    
    return comparison

# ---------------------------------------------------------------------------
# Compute performance metrics for a given strategy
# ---------------------------------------------------------------------------

def compute_metrics(returns: pd.Series, label: str, initial_capital: float,
                    portfolio_values: pd.Series, rf: float = 0.0, 
                    periods_per_year: int = 252) -> dict:

    total_days  = len(returns)
    ann_return  = (1 + returns).prod() ** (periods_per_year / total_days) - 1
    ann_vol     = returns.std() * np.sqrt(periods_per_year)
    sharpe      = (returns.mean() - rf) / returns.std() * np.sqrt(periods_per_year)

    downside    = returns[returns < rf]
    sortino     = (returns.mean() - rf) / downside.std() * np.sqrt(periods_per_year)

    rolling_max = portfolio_values.cummax()
    drawdown    = (portfolio_values - rolling_max) / rolling_max
    max_dd      = drawdown.min()

    ending_capital        = portfolio_values.iloc[-1]
    profit_to_drawdown    = ann_return / abs(max_dd)   # point 3 / point 4

    return {
        "label":                label,
        "starting_capital":     f"${initial_capital:,.2f}",
        "ending_capital":       f"${ending_capital:,.2f}",
        "ann_return":           f"{ann_return:.2%}",
        "ann_volatility":       f"{ann_vol:.2%}",
        "sharpe_ratio":         f"{sharpe:.2f}",
        "sortino_ratio":        f"{sortino:.2f}",
        "max_drawdown":         f"{max_dd:.2%}",
        "profit_to_drawdown":   f"{profit_to_drawdown:.2f}",
    }
