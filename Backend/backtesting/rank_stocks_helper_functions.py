import duckdb
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# DuckDB connection (in-memory, shared across helpers via module-level con)
# ---------------------------------------------------------------------------
con = duckdb.connect()

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_holdings(file_path: str) -> pd.DataFrame:
    """
    Read all quarterly 13F parquet files from folder_path into a single DataFrame.
    Selects only the columns needed downstream.
    """
    df = con.execute(f"""
        SELECT
            CAST(CIK AS VARCHAR) AS CIK,
            CAST(FILINGMANAGER_NAME AS VARCHAR) AS FILINGMANAGER_NAME,
            CAST(PERIODOFREPORT AS DATE) AS PERIODOFREPORT,
            CAST(FILING_DATE AS DATE) AS FILING_DATE,
            CAST(TABLEVALUETOTAL AS DOUBLE) AS TABLEVALUETOTAL,
            CAST(VALUE AS BIGINT) AS VALUE,
            CAST(CUSIP AS VARCHAR) AS CUSIP,
            CAST(ticker AS VARCHAR) AS ticker,
            CAST(equity_portfolio_total AS BIGINT) AS equity_portfolio_total,
            CAST(equity_weight AS DOUBLE) AS equity_weight
        FROM read_parquet('{file_path}', hive_partitioning = false)
        ORDER BY CIK, PERIODOFREPORT
    """).df()
    return df


def load_prices(file_path: str) -> pd.DataFrame:
    """
    Read the consolidated stock-price parquet file.
    """
    df = con.execute(f"""
        SELECT
            CAST(date AS DATE)  AS date,
            CAST(ticker AS VARCHAR) AS ticker,
            CAST(adj_close AS DOUBLE) AS adj_close,
            CAST(open as DOUBLE) AS open,
            CAST((open * (adj_close / close)) AS DOUBLE) AS adj_open
        FROM read_parquet('{file_path}')
        ORDER BY ticker, date
    """).df()
    return df

# ---------------------------------------------------------------------------
# Filter dates based on user inputs of start and end date
# ---------------------------------------------------------------------------

def filter_dates(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Keep rows whose PERIODOFREPORT falls within [start_date, end_date]."""
    return con.execute(f"""
        SELECT *
        FROM df
        WHERE PERIODOFREPORT >= CAST('{start_date}' AS DATE)
          AND PERIODOFREPORT <= CAST('{end_date}' AS DATE)
    """).df()

# -----------------------------------------------------------------------------------------------
# Aggregation & ranking to get top 10 stocks per quarter by aggregated weight across institutions
# -----------------------------------------------------------------------------------------------

def aggregate_stock_weights(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sum equity_weight across institutions per (quarter, ticker).
    PERIODOFREPORT is the lag anchor (trade_date = PERIODOFREPORT + lag_days).
    """
    return con.execute("""
        SELECT
            PERIODOFREPORT,
            ticker,
            SUM(equity_weight) AS agg_weight
        FROM df
        GROUP BY PERIODOFREPORT, ticker
    """).df()


def rank_top10(df: pd.DataFrame) -> pd.DataFrame:
    """Rank stocks by agg_weight within each quarter; keep top 10."""
    return con.execute("""
        SELECT *
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY PERIODOFREPORT
                    ORDER BY agg_weight DESC
                ) AS rank
            FROM df
        )
        WHERE rank <= 10
        ORDER BY PERIODOFREPORT, rank
    """).df()

# -----------------------------------------------------------------------------------------------
# Get trade prices by applying filing lag logic and joining with price data
# Standard lag = 47 days. 45 days is the legal filing deadline, plus a buffer of 2 days for data availability and processing.
# -----------------------------------------------------------------------------------------------


def apply_filing_lag_and_get_trade_prices(df: pd.DataFrame, prices: pd.DataFrame, lag_days: int = 47) -> pd.DataFrame:
    """
    For each (quarter, ticker):
      1. Compute candidate_date = PERIODOFREPORT + lag_days.
      2. Find the NEXT available trading day on-or-after candidate_date
         (snap FORWARD if it falls on a weekend / public holiday).
      3. Attach that day's OPEN price as entry_price (trade executed at open)
         and adj_close for audit/reference.
 
    Snapping forward: you can only act on 13F info after the
    filing lag has elapsed, so you would never trade on a date before
    the information is available.
 
    Returns df augmented with:
        candidate_date  -- PERIODOFREPORT + lag_days (before snapping): When the information is available.
        trade_date      -- first trading day >= candidate_date: The actual first day the market is open to let u execute the trade
        entry_price     -- open* on trade_date: The price you bought / sell at 
        adj_close       -- for evaluation of portfolio performance
    """
    result = con.execute(f"""
        WITH lagged AS (
            SELECT
                *,
                CAST(PERIODOFREPORT AS DATE) + INTERVAL '{lag_days} days' AS candidate_date
            FROM df
        )
        SELECT
            l.PERIODOFREPORT,
            l.ticker,
            l.agg_weight,
            l.rank,
            l.candidate_date,
            p.date      AS trade_date,
            p.open AS entry_price,
            p.adj_close AS adj_close
        FROM lagged l
        JOIN prices p
          ON  p.ticker = l.ticker
          AND p.date  >= l.candidate_date
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY l.PERIODOFREPORT, l.ticker
            ORDER BY p.date ASC
        ) = 1
        ORDER BY l.PERIODOFREPORT, l.ticker
    """).df()
    return result

# -----------------------------------------------------------------------------------------------
# Extract price subset for only the tickers ever held in the backtest, to save memory in the backtest.
# -----------------------------------------------------------------------------------------------

def extract_price_subset(prices: pd.DataFrame, top10: pd.DataFrame) -> pd.DataFrame:
    """Filter prices to only the tickers ever held, saving memory in the backtest."""
    return con.execute("""
        SELECT p.*
        FROM prices p
        SEMI JOIN (SELECT DISTINCT ticker FROM top10) t
            ON p.ticker = t.ticker
        ORDER BY p.ticker, p.date
    """).df()


# ---------------------------------------------------------------------------
# Back-test  (equal-weight, quarterly rebalance, use smart rebalance to minimise unnecessary trading)
# ---------------------------------------------------------------------------
 
def run_backtest(top10: pd.DataFrame,
                 prices: pd.DataFrame,
                 initial_capital: float) -> pd.DataFrame:
    """
    Equal-weight quarterly rebalance back-test.
 
    Mechanics
    ---------
    * trade_date = PERIODOFREPORT + lag_days (snapped forward to next trading day).
    * Each quarter's holding period: [trade_date[q], trade_date[q+1]).
    * On trade_date[q] SMART rebalancing is executed at the OPEN price:
        - exits   (dropped from top-10): sell all shares at open
        - entries (new to top-10):       buy target_allocation / open_price shares
        - stayers (in both quarters):    trade only the DELTA needed to restore
                                         equal weight (price drift during the quarter
                                         means their weights are no longer equal)
        - This minimises turnover vs a full sell-and-rebuy every quarter.
        - Final share counts are identical to a full rebuy, but fewer shares trade.
    * Daily portfolio value uses ADJ_CLOSE for mark-to-market:
        - portfolio_value[date] = sum(shares[ticker] * adj_close[ticker][date])
        - adj_close is dividend/split-adjusted so returns are total return, not price return.
    * portfolio_value carried into next quarter = adj_close mark-to-market on the
      last trading day of the current holding period (day before next trade_date).
 
    Why open for execution, adj_close for valuation?
    -------------------------------------------------
    Open price reflects the realistic fill price when you place a market order at
    the start of the day after you've decided to rebalance. adj_close is the standard
    for performance measurement because it accounts for dividends and splits, giving
    a true economic return. Mixing them correctly means: execution cost uses open,
    ongoing P&L uses adj_close.
 
    Returns
    -------
    DataFrame with columns:
        date             -- daily price observation dates
        quarter          -- PERIODOFREPORT the row belongs to
        trade_date       -- the actual date we execute the trade and the rebalance for that quarter (PERIODOFREPORT + lag, snapped forward)
        holding_period   -- period we hold the stocks for that quarter (e.g. "2020-02-15 to 2020-05-14")
        tickers          -- list of top-10 tickers held in that quarter
        portfolio_value  -- end-of-day mark-to-market value (shares * adj_close)
        daily_return     -- pct change vs previous trading day (NaN on first row)
        cum_return       -- cumulative return from inception
        quarter_return   -- total return for that quarter (repeated for every day in quarter)
    """
 
    # ---- normalise date types to Python date for consistent comparisons ----
    top10 = top10.copy()
    top10["PERIODOFREPORT"] = pd.to_datetime(top10["PERIODOFREPORT"]).dt.date
    top10["trade_date"]     = pd.to_datetime(top10["trade_date"]).dt.date
 
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"]).dt.date
 
    # ---- sort quarters ------------------------------------------------
    quarters = sorted(top10["PERIODOFREPORT"].unique())
    if len(quarters) < 2:
        raise ValueError(
            f"Need at least 2 quarters to run a backtest. "
            f"Found quarters: {quarters}"
        )
 
    # ---- trade_date per quarter --------------------------------------
    trade_date_map: dict = (
        top10.groupby("PERIODOFREPORT")["trade_date"]
             .first()
             .to_dict()
    )
 
    # ---- tickers per quarter -----------------------------------------
    tickers_map: dict = (
        top10.groupby("PERIODOFREPORT")["ticker"]
             .apply(list)
             .to_dict()
    )

    # ---- trade_date label per quarter (for output column) ------------
    # Same values as trade_date_map but kept separate for clarity
    trade_date_label_map: dict = trade_date_map.copy()
 
    # ---- holding period per quarter ----------------------------------
    # holding_period = trade_date[q] to last trading day before trade_date[q+1]
    # Built after adj_close_wide so we can look up the last actual trading day.
    # Populated in the loop below once adj_close_wide is available.
    holding_period_map: dict = {}
 
    # ---- wide adj_close table for daily valuation --------------------
    # rows = trading dates, columns = tickers, values = adj_close
    adj_close_wide = (
        prices
        .pivot_table(index="date", columns="ticker", values="adj_close")
        .sort_index()
    )
    adj_close_wide = adj_close_wide.ffill()   # forward-fill any gaps
 
    # ---- wide open price table for rebalance execution ---------------
    # Only needed on trade_dates; we look up per-ticker open on demand
    open_wide = (
        prices
        .pivot_table(index="date", columns="ticker", values="open")
        .sort_index()
    )
 
    # ---- run quarter-by-quarter ---------------------------------------
    portfolio_value = initial_capital
    positions: dict[str, float] = {}   # ticker -> shares held (fixed within quarter)
    history: list[dict] = []
 
    for i in range(len(quarters) - 1):
        q_now   = quarters[i]
        q_next  = quarters[i + 1]
 
        period_start = trade_date_map[q_now]    # inclusive: rebalance + first valuation day
        period_end   = trade_date_map[q_next]   # exclusive: next rebalance date
 
        stocks_now = top10[top10["PERIODOFREPORT"] == q_now].set_index("ticker")
        q_tickers  = tickers_map[q_now]
 
        # holding period: trade_date[q] to last trading day before trade_date[q+1]
        last_trading_day = adj_close_wide.index[adj_close_wide.index < period_end][-1]
        holding_period_map[q_now] = f"{period_start} to {last_trading_day}"
 
        # ── Get open prices for this rebalance date ───────────────────
        open_row = open_wide.loc[period_start] if period_start in open_wide.index else None
        if open_row is None:
            # fallback to last available adj_close row if open is missing entirely
            open_row = adj_close_wide.loc[adj_close_wide.index <= period_start].iloc[-1]
 
        def get_open(ticker: str) -> float:
            """Return open price for ticker on rebalance date, or NaN if unavailable."""
            val = open_row.get(ticker, float("nan"))
            return float(val) if pd.notna(val) and val > 0 else float("nan")
 
        new_tickers  = set(stocks_now.index)
        prev_tickers = set(positions.keys())
 
        exits   = prev_tickers - new_tickers          # sell completely
        entries = new_tickers  - prev_tickers         # buy fresh
        stayers = prev_tickers & new_tickers          # adjust weight only
 
        # ── Step 1: mark total portfolio value to market at today's open ─
        # We need the total $ value to compute equal-weight target allocations.
        if positions:
            portfolio_value = sum(
                shares * get_open(tkr)
                for tkr, shares in positions.items()
                if not np.isnan(get_open(tkr))
            )
 
        # ── Step 2: smart rebalance — minimise unnecessary trading ────────
        #
        # Target: each of the 10 stocks gets exactly 1/len(portfolio) of portfolio_value.
        #
        # exits   → sell all shares (full liquidation)
        # entries → buy target_allocation / open_price shares (fresh position)
        # stayers → current_value = shares_held * open_price
        #           delta = target_allocation - current_value
        #           if delta > 0: buy  abs(delta) / open_price more shares
        #           if delta < 0: sell abs(delta) / open_price shares
        #           net trade is only the DIFFERENCE from target, not a full rebuy
        #
        # This is equivalent to a full sell-and-rebuy in terms of final positions,
        # but executes far fewer shares traded for stayers.
 
        n_stocks          = len(stocks_now)
        target_allocation = portfolio_value / n_stocks   # $ per stock
 
        new_positions: dict[str, float] = {}
 
        for ticker, srow in stocks_now.iterrows():
            open_price = srow["entry_price"]   # open on trade_date from apply_filing_lag
            if np.isnan(open_price) or open_price <= 0:
                continue   # skip if price unavailable
 
            if ticker in entries:
                # Fresh buy: allocate full target_allocation at open
                new_positions[ticker] = target_allocation / open_price
 
            elif ticker in stayers:
                # Already held: just update share count to hit target weight
                # current_value may be above or below target due to price drift
                # new_shares = target_allocation / open_price  (same formula, cleaner)
                # The difference (new_shares - old_shares) is the net trade executed
                new_positions[ticker] = target_allocation / open_price
 
        # exits are simply not carried into new_positions → effectively sold
 
        positions = new_positions
 
        # ── Step 3: daily mark-to-market using adj_close ───────────────
        mask = (adj_close_wide.index >= period_start) & (adj_close_wide.index < period_end)
        period_adj = adj_close_wide.loc[mask]
 
        held_tickers = [t for t in positions if t in period_adj.columns]
        shares_vec   = np.array([positions[t] for t in held_tickers])
 
        # Fast vectorised dot product: (n_days x n_tickers) @ (n_tickers,) = (n_days,)
        daily_values = period_adj[held_tickers].values @ shares_vec
 
        quarter_start_value = float(daily_values[0]) if len(daily_values) > 0 else portfolio_value
 
        for date, val in zip(period_adj.index, daily_values):
            history.append({
                "date":            date,
                "quarter":         q_now,
                "trade_date":      trade_date_label_map[q_now],
                "holding_period":  holding_period_map[q_now],
                "tickers":         q_tickers,
                "portfolio_value": float(val),
                "_q_start_val":    quarter_start_value,
            })
 
        # carry forward end-of-period adj_close value into next quarter
        portfolio_value = float(daily_values[-1]) if len(daily_values) > 0 else portfolio_value
 
    # ---- assemble output ----------------------------------------------
    result = pd.DataFrame(history)
    result = result.sort_values("date").reset_index(drop=True)
 
    # daily_return: pct change across consecutive trading days (crosses quarter boundaries)
    result["daily_return"] = result["portfolio_value"].pct_change()
 
    # cum_return: total return from inception
    result["cum_return"] = (result["portfolio_value"] / initial_capital) - 1
 
    # quarter_return: (last adj_close value of quarter / first adj_close value) - 1
    q_end = result.groupby("quarter")["portfolio_value"].last().rename("_q_end_val")
    result = result.join(q_end, on="quarter")
    result["quarter_return"] = (result["_q_end_val"] / result["_q_start_val"]) - 1
    result = result.drop(columns=["_q_start_val", "_q_end_val"])
 
    # reorder columns cleanly
    result = result[["date", "quarter", "trade_date", "holding_period", "tickers", "portfolio_value",
                     "daily_return", "cum_return", "quarter_return"]]
 
    return result