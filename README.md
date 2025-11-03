# 📊 Real-Time Quant Analytics Dashboard

A **real-time cryptocurrency analytics system** that streams live data from Binance WebSocket, stores it locally in SQLite (`ticks.db`), and visualizes live analytics using a **Streamlit dashboard**.  

This project performs pair-trading analysis between two symbols (default: `BTCUSDT` & `ETHUSDT`) with rolling correlation, hedge ratio estimation, and Z-score–based alerts.

---

## 🚀 Features

- **Live WebSocket Data Ingestion** (via Binance public streams)
- **Local Database Storage** in `SQLite`
- **Real-Time Streamlit Dashboard** for:
  - Price comparison with dual y-axes
  - Spread and Z-Score visualization
  - Rolling correlation plot
  - Live connectivity status (🟢🟠🔴)
- **Dynamic Alerts** when |Z-score| exceeds threshold
- **Downloadable CSV Analytics**
- **Auto-refresh every few seconds**
- **Single-command runnable setup**

---

## 🗂️ Project Structure

📁krushikreddy_EC22B1062-main/

├── app.py # Streamlit frontend dashboard

├── data_ingestor.py # Binance WebSocket data ingestion

├── analytics_engine.py # Analytics computation module 

├── run_all.py # Combined launcher (one-command start)

├── requirements.txt # Python dependencies

└── README.md # Project documentation

## ⚙️ Installation & Setup

🥇 1️⃣ Clone the Repository

    git clone https://github.com/krushikreddy18/krushikreddy_EC22B1062.git

    cd krushikreddy_EC22B1062

🧱 2️⃣ Create a Virtual Environment

    python -m venv venv

⚙️ 3️⃣ Activate It

 On Windows:

    venv\Scripts\activate

 On macOS/Linux:

    source venv/bin/activate


📦 4️⃣ Install Dependencies

    pip install -r requirements.txt

🚀 5️⃣ Run the App

Option 1 – Single Command (Recommended):

    python run_all.py

This launches both the data ingestion and the Streamlit dashboard together automatically.

Option 2 — Manual Two-Terminal Mode

Terminal 1:

    python data_ingestor.py

Terminal 2:

    streamlit run app.py

After a few seconds, the dashboard will be live at:

    http://localhost:8501


Methodology & Analytics Explanation
1️⃣ Data Ingestion

 Connects to Binance public WebSocket endpoints:
 
    wss://stream.binance.com:9443/ws/btcusdt@trade
   
    wss://stream.binance.com:9443/ws/ethusdt@trade
   
   Each tick (price + size + timestamp) is inserted into ticks.db.

2️⃣ Data Resampling

 The dashboard resamples tick data into fixed time intervals (1s, 1min, 5min) using:
 
    df.set_index("ts").resample(timeframe).agg({"price": "last", "size": "sum"})
    
 3️⃣ **Analytics Computations**

- **Hedge Ratio:** estimated via linear regression (`statsmodels.OLS`)

  `p₁ = α + β · p₂`  
  where `β` = hedge ratio.

- **Spread:**

  `Spread = p₁ − (β × p₂)`

- **Z-Score:**

  `zₜ = (Spreadₜ − μₜ) / σₜ`  
  computed over a rolling window.

- **Rolling Correlation:**  
  Correlation between two prices in a moving window.

4️⃣ Alerts

When |Z-score| > threshold (default = 2.0), an alert is triggered with direction (UP/DOWN).

5️⃣ Visualizations

Dual-axis Price Comparison Chart

Spread & Z-Score Plot

Rolling Correlation Chart

Alert Log Table

Download Analytics as .csv


⏱️ Timezone Support

All timestamps are localized to Indian Standard Time (IST) for readability:

pd.Timestamp.now(tz="Asia/Kolkata")

📦 Dependencies

Main libraries used:

streamlit

plotly

pandas

numpy

statsmodels

websockets

sqlite3 (standard library)

Full list in requirements.txt.
