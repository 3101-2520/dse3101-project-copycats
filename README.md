# DSE3101 Investment Project

## Prerequisites

- Python 3.x with a virtual environment set up
- Kaggle account with API credentials
- OpenFIGI API key

---

## Getting Started

### 1. Set Working Directory

Ensure your current working directory is the project root:

```
dse3101investmentproject/
```

### 2. Set Up `.env` File

Create a `.env` file at the same level as this `README.md` with the following contents:

```dotenv
# App config
DEBUG=true               # true = development, false = production (for prof)

# Kaggle
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key

# OpenFIGI
OPENFIGI_API_KEY=your_openfigi_api_key
OPENFIGI_URL=https://api.openfigi.com/v3/mapping
```

> **Development phase:** set `DEBUG=true` — downloads latest dataset from Kaggle automatically on first run.
> 
> **Production phase (prof running):** set `DEBUG=false` — only downloads the raw zip files needed.

---

## Running the Pipeline

### Step 3 — Transform (Production only, for prof)

Processes raw data through the full pipeline:

```
13F_zip_files → 13F_clean_files → 13F_filtered_and_mapped_files → 13F_filtered_and_mapped_and_screened_files
```

**Run:**
```bash
python -m Backend.transform.batch_process_form13f
```

> **Stock price data:** TBC — Xander and Benson to confirm progress.

---

### Step 4 — Backtesting

#### 4a. Get Top N Institutions (Production only, for prof)

> TBC — Benson to confirm top 10, 20, and 30 institutions.

#### 4b. Get Top M Stocks (runs together with frontend)

Returns `portfolio_df` and `metrics_df` for the top M stocks.

**Run:**
```bash
python -m Backend.backtesting.batch_process_rank_stocks
```

**User inputs** (passed from frontend to backend):

| Parameter | Default | Description |
|---|---|---|
| `userinput_start_date` | `'2013-12-31'` | Backtest start date |
| `userinput_end_date` | `'2025-05-23'` | Backtest end date |
| `userinput_initial_capital` | `10_000` | Starting capital ($) |
| `userinput_topN` | `10` | Top N stocks to hold per quarter |
| `userinput_topN_institutions` | `10` | Top institutions to track (10, 20, or 30) |
| `userinput_lag` | `47` | Lag days (adjustable) |
| `userinput_cost_rate` | `0.001` | Transaction cost as fraction of traded value (0.1%) |

---

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
