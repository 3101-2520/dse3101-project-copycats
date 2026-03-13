import streamlit as st

# create button
def new_backtest_button():
    col1, col2 = st.columns([7,1])
    with col2:
        if st.button("➕ New Backtest"):
            show_backtest_modal()

# floating add new backtest structure
@st.dialog("New Backtest")
def show_backtest_modal():

    st.subheader("Strategy")
    date = st.date_input("Date")
    ticker = st.text_input("Ticker")

    st.subheader("Portfolio Allocation")
    allocation = st.number_input("Allocation (%)", min_value=0.0, max_value=100.0)

    st.subheader("Allocation")
    starting_funds = st.number_input("Starting Funds", value=10000)
    margin = st.number_input("Margin Allocation per Trade (%)", value=10)
    max_positions = st.number_input("Max Open Positions", value=5)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Cancel"):
            st.rerun()

    with col2:
        if st.button("Run Backtest"):
            st.success("Backtest started!")
            st.rerun()


# original new backtest code 
def new_backtest_panel():
    if not st.session_state.get("show_backtest", False):
        return

    st.markdown("---")
    st.subheader("New Backtest")

    # Date input
    date = st.date_input("Date")

    st.markdown("##### Strategy")

    ticker = st.text_input("Ticker")

    st.markdown("##### Portfolio Allocation")

    col_rank, col_ticker, col_alloc, col_rec, col_change = st.columns([1,2,2,2,1])

    col_rank.write("Rank")
    col_ticker.write("Ticker")
    col_alloc.write("Allocation")
    col_rec.write("Recommended allocation")
    col_change.write("Change")

    allocations = []

    for i in range(3):

        c1, c2, c3, c4, c5 = st.columns([1,2,2,2,1])

        c1.write(i + 1)

        tick = c2.text_input(
            f"Ticker{i}",
            key=f"ticker{i}",
            label_visibility="collapsed"
        )

        alloc = c3.number_input(
            f"Alloc{i}",
            min_value=0.0,
            max_value=100.0,
            key=f"alloc{i}",
            label_visibility="collapsed"
        )

        c4.write("12.5%")  # placeholder
        c5.write("▲")

        allocations.append((tick, alloc))

    st.markdown("### Allocation")

    colA, colB = st.columns(2)

    with colA:
        starting_funds = st.number_input("Starting Funds", value=10000)

    with colB:
        margin = st.number_input("Margin Allocation per Trade (%)", value=10)

    max_positions = st.number_input("Max Open Positions", value=5)

    st.markdown(" ")

    col_cancel, col_run = st.columns([8,1])

    with col_cancel:
        if st.button("Cancel"):
            st.session_state.show_backtest = False

    with col_run:
        if st.button("Run Backtest"):
            

            st.success("Backtest running...")

            params = {
                "date": date,
                "ticker": ticker,
                "allocations": allocations,
                "starting_funds": starting_funds,
                "margin": margin,
                "max_positions": max_positions
            }

            st.write(params)

            return params