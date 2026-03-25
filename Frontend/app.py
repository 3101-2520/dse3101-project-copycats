import streamlit as st
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
from components.new_backtest import new_backtest_button #for yenfay's code testing, DO NOT OVERWRITE PLEASE! 
from components.top_20 import top_20_table #for yenfay's code testing, DO NOT OVERWRITE PLEASE!
from datetime import date 
import math

# page set up and layout
st.set_page_config(
    page_title="dse3101 project",
    layout="wide"
)

# title and new backtest button layout
c_title, c_backtest = st.columns([8, 2], vertical_alignment="center")

with c_title:
    st.title("Beginner Dashboard")
    
# date layout
c1, c2, c3, c4 = st.columns([0.5, 0.2, 0.15, 0.15])
quarter_end_dates = [
    date(2025, 3, 31),
    date(2025, 6, 30),
    date(2025, 9, 30),
    date(2025, 12, 31),
]

with c1:
    st.write("")

with c2:
    fee_per_trade = new_backtest_button()

with c3:
    from_date = st.selectbox(
        "From:",
        options=quarter_end_dates,
        index=0,
        format_func=lambda d: d.strftime("%Y/%m/%d"),
        key="from_date"
    )

with c4:
    valid_to_dates = [d for d in quarter_end_dates if d >= from_date]

    to_date = st.selectbox(
        "To:",
        options=valid_to_dates,
        index=len(valid_to_dates) - 1,
        format_func=lambda d: d.strftime("%Y/%m/%d"),
        key="to_date"
    )

# ---------- metric helper functions ----------
def metric_bg(value):
    if value is None:
        return "#3b3f4a"   # grey
    if value > 0:
        return "#1f9d73"   # green
    if value < 0:
        return "#c63d2f"   # red
    return "#3b3f4a"


def format_metric(value, kind="number"):
    if value is None:
        return "--"
    if kind == "percent":
        return f"{value:.1f}%"
    return f"{value:.2f}"

def render_metric(label, value, kind="number"):
    bg = metric_bg(value)
    display = format_metric(value, kind)

    st.markdown(
        f"""
        <div style="
            background:{bg};
            border-radius:14px;
            padding:14px;
            height:80px;
            display:flex;
            flex-direction:column;
            justify-content:space-between;
            color:white;
        ">
            <div style="font-size:16px;font-weight:600;">{label}</div>
            <div style="font-size:16px;font-weight:700;">{display}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def normalize_series(series):
    base = series[0]
    return [x / base for x in series]

def log_transform(series):
    base = series[0]
    return [math.log(x / base) for x in series]
    
# configure left column for graph and right column for table
col_left, col_right = st.columns([6, 4])

with col_left:
    st.header("Porfolio performance")
    ### ruiqian add your code here for the metrics ###
    # Placeholder for now
    #st.line_chart([1,2,3,2,5])
    chart_c1, chart_c2, _ = st.columns([1, 1, 4])
    with chart_c1:
        use_log_scale = st.checkbox("Log scale", value=False)
    with chart_c2:
        show_benchmark = st.checkbox("Show SPY", value=True)

    portfolio_dates = [
        "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
        "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"
    ]

    portfolio_values = [
        100000, 120000, 115000, 140000,
        160000, 180000, 175000, 200000
    ]

    spy_values = [
        100000, 105000, 110000, 115000,
        120000, 130000, 135000, 140000
    ]

    # To integrate with backend, replace portfolio_dates and portfolio_values with backend output:
    # portfolio_dates = backend_output["dates"]
    # portfolio_values = backend_output["portfolio_values"]
    # spy_values = backend_output["spy_values"]
    
    if use_log_scale:
        portfolio_plot = log_transform(portfolio_values)
        spy_plot = log_transform(spy_values)

        y_axis_type = "value"   # IMPORTANT: NOT "log"
        
        y_axis_formatter = """
        function(value) {
            return (value * 100).toFixed(0) + '%';
        }
        """

        tooltip_formatter = """
        function(params) {
            let result = params[0].axisValue + '<br/>';
            for (let i = 0; i < params.length; i++) {
                let pct = (params[i].value * 100).toFixed(1);
                result += params[i].seriesName + ': ' + pct + '%<br/>';
            }
            return result;
        }
        """
    else:
        portfolio_plot = portfolio_values
        spy_plot = spy_values
        y_axis_type = "value"
        y_axis_min = None
        area_style = {}
        y_axis_formatter = """
        function(value) {
            return value.toLocaleString();
        }
        """
        tooltip_formatter = """
        function(params) {
            let result = params[0].axisValue + '<br/>';
            for (let i = 0; i < params.length; i++) {
                result += params[i].seriesName + ': ' + params[i].value.toLocaleString() + '<br/>';
            }
            return result;
        }
        """
    portfolio_area = {"opacity": 0.22}
    spy_area = {"opacity": 0.32}

    series = [
        {
            "name": "Portfolio",
            "type": "line",
            "smooth": False,
            "symbol": "circle",
            "symbolSize": 8,
            "data": portfolio_plot,
            "areaStyle": portfolio_area
        }
    ]

    if show_benchmark:
        series.append({
            "name": "SPY",
            "type": "line",
            "smooth": False,
            "symbol": "circle",
            "symbolSize": 7,
            "data": spy_plot,
            "areaStyle": spy_area
        })

    chart_option = {
        "title": {
            "text": "Portfolio Performance",
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis"
        },
        "legend": {
            "data": ["Portfolio", "SPY"],
            "top": 40
        },
        "grid": {
            "top": 80
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {},
                "dataView": {"readOnly": True},
                "restore": {},
                "dataZoom": {}
            }
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": portfolio_dates
        },
        "yAxis": {"type": "value"},
        "dataZoom": [
            {"type": "inside"},
            {"type": "slider"}
        ],
        "series": series
    }

    st_echarts(chart_option, height="450px")

    metrics = [
        ("CAGR", 46.7, "percent"),
        ("Sharpe Ratio", 1.13, "number"),
        ("Max Drawdown", -12.3, "percent"),
        ("Volatility", 17.8, "percent"),
        ("Total Return", None, "percent"),
        ("Alpha", None, "percent"),
        ("Beta", None, "number"),
        ("Win percentage", None, "percent"),
    ]
    ###To integrate with backend, replace metrics with code below and replacewith output from backend:
    ###metrics = [
    ###    ("CAGR", backend_output["cagr"], "percent"),
    ###    ("Sharpe Ratio", backend_output["sharpe_ratio"], "number"),
    ###    ("Max Drawdown", backend_output["max_drawdown"], "percent"),
    ###    ("Volatility", backend_output["volatility"], "percent"),
    ###    ("Total Return", backend_output["total_return"], "percent"),
    ###    ("Alpha", backend_output["alpha"], "percent"),
    ###    ("Beta", backend_output["beta"], "number"),
    ###    ("Win percentage", backend_output["win_percentage"], "percent"),
    ###]

    metric_row_1 = st.columns(4,gap="small")
    metric_row_2 = st.columns(4,gap="small")

    for col, metric in zip(metric_row_1, metrics[:4]):
        with col:
            render_metric(*metric)

    for col, metric in zip(metric_row_2, metrics[4:]):
        with col:
            render_metric(*metric)

with col_right:
    st.header("Top 10 Stocks by Institutional Holdings")
    top_20_table()