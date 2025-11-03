import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import numpy as np
import time
import statsmodels.api as sm
from datetime import datetime
import os
# --- Auto-launch background data ingestion ---


# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="Live Quant Dashboard", layout="wide")
st.title("📊 Real-Time Quant Analytics Dashboard")

# ---------------------------
# Sidebar Controls
# ---------------------------
st.sidebar.header("⚙️ Settings")

DB_PATH = os.path.abspath("ticks.db")
symbol_1 = st.sidebar.text_input("Symbol 1", "btcusdt")
symbol_2 = st.sidebar.text_input("Symbol 2", "ethusdt")
timeframe = st.sidebar.selectbox("Resample Timeframe", ["1s", "1Min", "5Min"])
window = st.sidebar.slider("Rolling Window (points)", 10, 300, 60)
refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 1, 10, 3)
z_alert = st.sidebar.slider("Z-Score Alert Threshold", 1.0, 3.0, 2.0)

st.sidebar.markdown("---")
st.sidebar.info("The dashboard auto-refreshes every few seconds.\n"
                "If auto-refresh fails, use the 🔄 Refresh Now button.")

# ---------------------------
# Auto-Refresh (safe for all versions)
# ---------------------------
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=refresh_rate * 1000, key="data_refresh")
except Exception:
    refresh_btn = st.button("🔄 Refresh Now")
    if refresh_btn:
        st.rerun()

# ---------------------------
# Helper Functions
# ---------------------------
def load_ticks(limit=10000):
    """Always read fresh data from the database."""
    with sqlite3.connect(DB_PATH, isolation_level=None, timeout=10) as conn:
        df = pd.read_sql_query(
            f"SELECT * FROM ticks ORDER BY ts DESC LIMIT {limit}",
            conn
        )
    
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

    return df

def resample_data(df, symbol, timeframe):
    df = df[df["symbol"] == symbol]
    if df.empty:
        return pd.DataFrame()
    df = df.set_index("ts").resample(timeframe).agg({"price": "last", "size": "sum"}).dropna()
    df.index = df.index.round(timeframe)  # <-- ensures perfect alignment
    return df


def compute_analytics(df1, df2, window):
    df = pd.concat([df1["price"], df2["price"]], axis=1).dropna()
    if df.empty:
        return None, None, None, None, None
    df.columns = ["p1", "p2"]
    model = sm.OLS(df["p1"], sm.add_constant(df["p2"])).fit()
    hedge_ratio = model.params["p2"]
    spread = df["p1"] - hedge_ratio * df["p2"]
    zscore = (spread - spread.rolling(window).mean()) / spread.rolling(window).std()
    zscore = zscore.fillna(0)
    rolling_corr = df["p1"].rolling(window).corr(df["p2"])
    return df, spread, zscore, hedge_ratio, rolling_corr

# ---------------------------
# Load and Process Data
# ---------------------------
df = load_ticks()

if len(df) < 2:
    st.warning("Waiting for data...")
    st.stop()

df1 = resample_data(df, symbol_1, timeframe)
df2 = resample_data(df, symbol_2, timeframe)

if df1.empty or df2.empty:
    st.warning("Insufficient data for selected symbols.")
    st.stop()

df_pair, spread, zscore, hedge_ratio, rolling_corr = compute_analytics(df1, df2, window)
if df_pair is None:
    st.warning("Not enough overlapping data for analytics.")
    st.stop()

# ---------------------------
# ✅ Fixed Live Indicator (UTC-based)
# ---------------------------
latest_ts = df["ts"].max()

if pd.isna(latest_ts):
    st.warning("No valid timestamps found in DB.")
else:
    now_utc = pd.Timestamp.utcnow()
    seconds_since_last = (now_utc - latest_ts).total_seconds()

    if seconds_since_last < 30:
        st.success(f"🟢 Live: last tick {seconds_since_last:.0f} s ago (as of {latest_ts})")
    elif seconds_since_last < 300:
        st.warning(f"🟠 Slight delay: last tick {int(seconds_since_last)} s ago")
    else:
        st.error(f"🔴 Disconnected: last tick {int(seconds_since_last)} s ago")

# ---------------------------
# Dashboard Layout
# ---------------------------
# ---------------------------
# Dashboard Layout
# ---------------------------
st.subheader(f"Symbols: {symbol_1.upper()} vs {symbol_2.upper()}")
st.write(f"Hedge Ratio: **{hedge_ratio:.4f}**")

col1, col2 = st.columns(2)

# -----------------------------------
# 📈 Price Comparison (Dual Y-Axis)
# -----------------------------------
with col1:
    fig1 = go.Figure()

    # BTC/first symbol → left axis
    fig1.add_trace(go.Scatter(
        x=df_pair.index,
        y=df_pair["p1"],
        name=symbol_1.upper(),
        line=dict(color="orange"),
        yaxis="y1"
    ))

    # ETH/second symbol → right axis
    fig1.add_trace(go.Scatter(
        x=df_pair.index,
        y=df_pair["p2"],
        name=symbol_2.upper(),
        line=dict(color="cyan"),
        yaxis="y2"
    ))

    fig1.update_layout(
        title="Price Comparison (Dual Axis)",
        xaxis=dict(title="Time"),
        yaxis=dict(title=f"{symbol_1.upper()} Price", side="left"),
        yaxis2=dict(title=f"{symbol_2.upper()} Price", overlaying="y", side="right"),
        legend=dict(x=0, y=1.1, orientation="h"),
    )

    st.plotly_chart(fig1, width="stretch")

# -----------------------------------
# 📊 Spread & Z-Score (Dual Y-Axis)
# -----------------------------------
with col2:
    fig2 = go.Figure()

    # Spread → left axis
    fig2.add_trace(go.Scatter(
        x=spread.index,
        y=spread,
        name="Spread",
        line=dict(color="lightgreen"),
        yaxis="y1"
    ))

    # Z-Score → right axis
    fig2.add_trace(go.Scatter(
        x=zscore.index,
        y=zscore,
        name="Z-Score",
        line=dict(color="red", dash="dot"),
        yaxis="y2"
    ))

    fig2.update_layout(
        title="Spread & Z-Score (Dual Axis)",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Spread", side="left"),
        yaxis2=dict(title="Z-Score", overlaying="y", side="right"),
        legend=dict(x=0, y=1.1, orientation="h"),
    )

    st.plotly_chart(fig2, width="stretch")


# ---------------------------
# Rolling Correlation Plot
# ---------------------------
st.markdown("### 🔁 Rolling Correlation")

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr, name="Rolling Correlation", line=dict(color="yellow")))

# Add 0 baseline
fig3.add_hline(y=0, line=dict(color="gray", dash="dot"))

fig3.update_layout(
    xaxis_title="Time",
    yaxis_title="Correlation",
    yaxis_range=[-1, 1],
    title="Rolling Correlation (Updated)"
)

st.plotly_chart(fig3, width="stretch")

# ---------------------------
# Task 2 — Alert History
# ---------------------------
if "alerts" not in st.session_state:
    st.session_state["alerts"] = []

if not zscore.dropna().empty and abs(zscore.iloc[-1]) > z_alert:
    alert_data = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "zscore": round(float(zscore.iloc[-1]), 3),
        "symbol_1": symbol_1.upper(),
        "symbol_2": symbol_2.upper(),
        "direction": "UP" if zscore.iloc[-1] > 0 else "DOWN",
    }
    st.session_state["alerts"].append(alert_data)
    st.error(f"🚨 ALERT: |Z-Score| > {z_alert} ({zscore.iloc[-1]:.2f})")
else:
    st.success(
        f"✅ Normal Range: Z-Score = {zscore.iloc[-1]:.2f}"
        if not zscore.dropna().empty
        else "Waiting for z-score…"
    )

st.markdown("### 🚨 Recent Alerts")
if len(st.session_state["alerts"]) > 0:
    st.dataframe(pd.DataFrame(st.session_state["alerts"]).tail(5))
else:
    st.caption("No alerts triggered yet.")

# ---------------------------
# Download CSV (Bonus)
# ---------------------------
st.markdown("### 📥 Download Analytics")
analytics = pd.DataFrame({
    "time": df_pair.index,
    f"price_{symbol_1}": df_pair["p1"],
    f"price_{symbol_2}": df_pair["p2"],
    "spread": spread,
    "zscore": zscore,
    "rolling_corr": rolling_corr,
})
csv = analytics.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, file_name="analytics_output.csv", mime="text/csv")

st.caption(f"Last refresh: {time.strftime('%H:%M:%S')} | Auto-update every {refresh_rate}s")
