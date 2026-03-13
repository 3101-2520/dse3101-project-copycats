import streamlit as st
from components.new_backtest import new_backtest_button #for yenfay's code testing, DO NOT OVERWRITE PLEASE! 
from components.top_20 import top_20_table #for yenfay's code testing, DO NOT OVERWRITE PLEASE! 

# page set up and layout
st.set_page_config(
    page_title="dse3101 project",
    layout="wide"
)

st.title("Beginner Dashboard")
c1, c2, c3, c4 = st.columns([0.7, 0.12, 0.12, 0.11])

with c1: 
    st.write("")
    
with c2:
    from_date = st.date_input("From:", key="from_date")

with c3:
    to_date = st.date_input("To:", key="to_date")
    
with c4: 
    new_backtest_button()

col_left, col_right = st.columns([6, 4])

with col_left:
    st.header("Porfolio performance")
    ### ruiqian add your code here for the metrics ###
    # Placeholder for now
    st.line_chart([1,2,3,2,5])

with col_right:
    st.header("Top 20 Stocks by Institutional Holdings")
    top_20_table()