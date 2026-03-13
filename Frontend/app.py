import streamlit as st
from components.new_backtest import new_backtest_button #for yenfay's code testing, DO NOT OVERWRITE PLEASE! 
import pandas as pd

st.set_page_config(
    page_title="dse3101 project",
    layout="wide"
)

st.title("Beginner Dashboard")

# new backtest
new_backtest_button()

# dummy data 
d = {"Rank": [1, 2, 3], 
     "Ticker": ["AAPL", "MSFT", "NVDA"],
     "Allocation": [10.5, 2.1, 3.4],
     "Recommended Allocation": ["12.5%", "11.0%", "5.0%"]}

dummy_data = pd.DataFrame(data=d, index=[1, 2, 3])

# Create columns for side by side view of table and cards (col 1) and top 20 (col 2)
col_left, col_right = st.columns([6, 4])

with col_left:
    st.header("Porfolio performance")
    ### ruiqian add your code here for the metrics ###
    # Placeholder for now
    st.line_chart([1,2,3,2,5])

with col_right:
    st.header("Top 20 Stocks by Institutional Holdings")
    st.table(data = dummy_data)