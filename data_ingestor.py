import asyncio
import json
import websockets
import sqlite3
from datetime import datetime, timezone, timedelta

# Binance Futures WebSocket URL
BINANCE_URL = "wss://fstream.binance.com/ws/{}@trade"

# Symbols to track
SYMBOLS = ["btcusdt", "ethusdt"]

# SQLite DB setup
conn = sqlite3.connect("ticks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS ticks (
    ts TEXT,
    symbol TEXT,
    price REAL,
    size REAL
)
""")
conn.commit()


async def save_tick(symbol, tick):
    """Insert one tick into DB"""
    cursor.execute(
        "INSERT INTO ticks (ts, symbol, price, size) VALUES (?, ?, ?, ?)",
        (tick["ts"], symbol, tick["price"], tick["size"])
    )
    conn.commit()

IST = timezone(timedelta(hours=5, minutes=30))

def normalize(msg: dict):
    ts = datetime.fromtimestamp(msg.get("T", msg.get("E")) / 1000, tz=IST).isoformat()
    return {
        "ts": ts,
        "price": float(msg["p"]),
        "size": float(msg["q"]),
    }


async def stream_symbol(symbol):
    """Stream data for one symbol with auto-reconnect"""
    url = BINANCE_URL.format(symbol)
    while True:
        try:
            async with websockets.connect(url) as ws:
                print(f"✅ Connected to {symbol} stream.")
                async for message in ws:
                    data = json.loads(message)
                    if data.get("e") == "trade":
                        tick = normalize(data)
                        await save_tick(symbol, tick)
                        print(f"{symbol} | {tick['ts']} | {tick['price']} | {tick['size']}")
        except (websockets.ConnectionClosed, ConnectionResetError) as e:
            print(f"⚠️ Connection lost for {symbol}: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ Error in {symbol} stream: {e}. Restarting in 5s...")
            await asyncio.sleep(5)


async def main():
    """Run all symbol streams concurrently"""
    await asyncio.gather(*(stream_symbol(sym) for sym in SYMBOLS))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
        conn.close()
