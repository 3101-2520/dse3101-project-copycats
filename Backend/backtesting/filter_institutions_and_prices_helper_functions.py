import duckdb
import pandas as pd
import numpy as np
import os

# Create a connection
con = duckdb.connect()

def filter_form13f_for_top_institutions(folder_path: str, institution_list: list[str], form13f_output: str):
    """
    Filters 13F files by CIK and saves directly to a new parquet file 
    without loading everything into memory.
    """
    # Format the CIK list for the SQL IN clause
    cik_filter = ", ".join(f"'{c}'" for c in institution_list)
    
    # Define the query to filter and select columns
    query = f"""
        COPY (
            SELECT
                CIK,
                FILINGMANAGER_NAME,
                PERIODOFREPORT,
                FILING_DATE,
                TABLEVALUETOTAL,
                VALUE,
                CUSIP,
                ticker,
                name,      
                exchCode,
                equity_portfolio_total,
                equity_weight
            FROM read_parquet('{folder_path}/**/*.parquet', hive_partitioning = false)
            WHERE CIK IN ({cik_filter})
            AND exchCode IN ('US')
        )
        TO '{form13f_output}/final_form13f.parquet' (FORMAT PARQUET)
    """
    
    # Execute the copy command
    con.execute(query)
    print(f"Filtered holdings saved to {form13f_output}/final_form13f.parquet")


def filter_prices_for_top_institutions(prices_file: str, holdings_file: str, prices_output_dir: str):
    # 1. Clean the output path (Force forward slashes for DuckDB)
    # Ensure we are pointing to a FILE, not just a folder
    output_file_path = os.path.join(prices_output_dir, "final_prices.parquet").replace("\\", "/")
    
    # 2. Convert input paths to forward slashes to avoid Windows escape char issues
    clean_prices = str(prices_file).replace("\\", "/")
    clean_holdings = str(holdings_file).replace("\\", "/")

    query = f"""
        COPY (
            SELECT p.*
            FROM read_parquet('{clean_prices}') AS p
            WHERE p.ticker IN (
                SELECT DISTINCT ticker 
                FROM read_parquet('{clean_holdings}')
                WHERE ticker IS NOT NULL
            )
        )
        TO '{output_file_path}' (FORMAT PARQUET);
    """

    con.execute(query)
    print(f"Filtered price data saved to: {output_file_path}")



