import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
#  Compute Analytics from raw tick data (resampling-based)
# ---------------------------------------------------------------------------

def compute_analytics(df: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    """
    Compute spread, z-score, and rolling correlation between BTCUSDT & ETHUSDT.
    Handles unsynchronized tick data by resampling to 1-second intervals.
    Args:
        df: DataFrame with columns [ts, symbol, price, size]
        window: rolling window size (in samples / seconds)
    Returns:
        analytics_df: DataFrame with columns [ts, price_btc, price_eth,
                                             spread, zscore, rolling_corr]
    """

    if df.empty:
        print("⚠️ Empty dataframe passed to compute_analytics().")
        return pd.DataFrame()

    # --- 1️⃣ Prepare time index ---
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    df = df.dropna(subset=["ts", "price"]).set_index("ts").sort_index()

    # --- 2️⃣ Split by symbol ---
    df_btc = df[df["symbol"].str.lower() == "btcusdt"]
    df_eth = df[df["symbol"].str.lower() == "ethusdt"]

    if df_btc.empty or df_eth.empty:
        print("⚠️ Missing BTC or ETH data for analytics.")
        return pd.DataFrame()

    # --- 3️⃣ Resample both to 1-second intervals (using last price each second) ---
    btc_1s = df_btc["price"].resample("1S").last().rename("price_btc")
    eth_1s = df_eth["price"].resample("1S").last().rename("price_eth")

    # Merge side-by-side and drop rows where either side is NaN
    merged = pd.concat([btc_1s, eth_1s], axis=1).dropna()

    if merged.empty:
        print("⚠️ No overlapping BTC/ETH timestamps after resampling.")
        return pd.DataFrame()

    # --- 4️⃣ Compute analytics ---
    merged["spread"] = merged["price_btc"] - merged["price_eth"]

    if len(merged) >= window:
        # Rolling z-score of spread
        mean_spread = merged["spread"].rolling(window).mean()
        std_spread = merged["spread"].rolling(window).std()
        merged["zscore"] = (merged["spread"] - mean_spread) / std_spread

        # Rolling correlation
        merged["rolling_corr"] = (
            merged["price_btc"].rolling(window).corr(merged["price_eth"])
        )
    else:
        merged["zscore"] = 0.0
        merged["rolling_corr"] = 0.0

    # --- 5️⃣ Clean up ---
    merged = merged.dropna().reset_index()  # reset to keep 'ts' as column
    merged.rename(columns={"ts": "time"}, inplace=True)

    return merged[["time", "price_btc", "price_eth", "spread", "zscore", "rolling_corr"]]


# ---------------------------------------------------------------------------
#  Optional standalone test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sqlite3

    conn = sqlite3.connect("ticks.db")
    df_ticks = pd.read_sql("SELECT * FROM ticks", conn)
    conn.close()

    analytics = compute_analytics(df_ticks, window=50)
    print(analytics.tail())

    analytics.to_csv("analytics_output.csv", index=False)
    print("✅ analytics_output.csv written successfully.")
