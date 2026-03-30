# DSE3101 Investment Project

## Prerequisites

- Python 3.x
- A virtual environment (optional but recommended)
- Kaggle account with API credentials
- OpenFIGI API key

---

## Getting Started

### 1. Set Working Directory

Ensure your current working directory is the project root:

```
dse3101investmentproject/
```

### 2. Configure the `.env` File

Create a `.env` file at the project root (same level as this `README.md`) with the following contents:

```dotenv
# App config
DEBUG=true               # true = development mode | false = production mode (for prof)

# Kaggle
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key

# OpenFIGI
OPENFIGI_API_KEY=your_openfigi_api_key
OPENFIGI_URL=https://api.openfigi.com/v3/mapping
```

> **`DEBUG=true` (Development):** Automatically downloads the latest dataset from Kaggle on first run.
>
> **`DEBUG=false` (Production):** Downloads only the raw zip files required for the pipeline.

---

## Running the Pipeline

### Step 3 — Transform

#### Production (`DEBUG=false`)

Processes raw data through the full transformation pipeline:

```
13F_zip_files → 13F_clean_files → 13F_filtered_and_mapped_files → 13F_filtered_and_mapped_and_screened_files
```

**Run:**

```bash
python -m Backend.transform.batch_process_form13f
```

> ⚠️ **[TBC]** Stock price data integration is pending confirmation from Xander and Benson.

---

#### Development (`DEBUG=true`)

Downloads all data from Kaggle and runs the pipeline locally.

**Steps:**

1. Set `DEBUG=true` in your `.env` file.
2. Run the transform module:
   ```bash
   python -m Backend.transform.batch_process_form13f
   ```
3. Verify that a `Datasets/` folder has been created containing the latest data files.

---

### Step 4 — Backtesting

#### 4a. Get Top N Institutions

> ⚠️ **[TBC]** Benson to confirm outputs for top 10, 20, and 30 institutions.

---

#### 4b. Get Top M Stocks

Returns `portfolio_df` and `metrics_df` for the top M stocks. This step runs in conjunction with the frontend.

**Run (for testing):**

```bash
python -m Backend.backtesting.batch_process_rank_stocks
```

**Frontend Integration:**

Import and call `main()` from `Backend.backtesting.batch_process_rank_stocks` in your frontend script, passing the user inputs as arguments:

```python
from Backend.backtesting.batch_process_rank_stocks import main

portfolio_df, metrics_df = main(
    userinput_start_date='2013-12-31',
    userinput_end_date='2025-05-23',
    userinput_initial_capital=10_000,
    userinput_topN=10,
    userinput_topN_institutions=10,
    userinput_lag=47,
    userinput_cost_rate=0.001,
)
```

**User Input Parameters:**

| Parameter                   | Default        | Description                                              |
|-----------------------------|----------------|----------------------------------------------------------|
| `userinput_start_date`      | `'2013-12-31'` | Backtest start date                                      |
| `userinput_end_date`        | `'2025-05-23'` | Backtest end date                                        |
| `userinput_initial_capital` | `10_000`       | Starting capital (USD)                                   |
| `userinput_topN`            | `10`           | Number of top stocks to hold per quarter                 |
| `userinput_topN_institutions` | `10`         | Number of top institutions to track (`10`, `20`, or `30`) |
| `userinput_lag`             | `47`           | Lag in days between filing date and portfolio rebalancing |
| `userinput_cost_rate`       | `0.001`        | Transaction cost as a fraction of traded value (0.1%)    |

## Project Structure

```
dse3101investmentproject/
├── .env                          ← secrets and config (never commit this)
├── .gitignore
├── README.md
├── config.py                     ← all paths and env variables
├── Datasets/
│   ├── 13F_zip_files/
│   ├── 13F_clean_files/
│   ├── 13F_filtered_and_mapped_files/
│   ├── 13F_filtered_and_mapped_and_screened_files/
│   ├── data_for_frontend/
│   ├── final_files/              ← tracked by Git LFS
│   │   ├── final_top10_form13f.parquet
│   │   └── final_top10_prices.parquet
│   ├── others/
│   └── stock_price_data/
├── Backend/
│   ├── transform/
│   │   ├── batch_process_form13f.py        ← main run function for transform of form13f data
│   │   └── download_data_from_kaggle.py    ← helper to download latest data from kaggle
│   └── backtesting/
│       └── batch_process_rank_stocks.py    ← main run function for backtesting of topN stocks (integration with frontend)
```
