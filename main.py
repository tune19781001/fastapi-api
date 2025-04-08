import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import ta

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 日本株の株価・RSI・移動平均を取得
@app.get("/stock")
def get_stock_data(symbol: str):
    try:
        data = yf.Ticker(symbol).history(period="30d")

        latest = data.iloc[-1]
        price = float(latest["Close"])
        volume = int(latest["Volume"])

        rsi_series = ta.momentum.RSIIndicator(close=data["Close"]).rsi()
        rsi = round(rsi_series.iloc[-1], 2)

        ma_5 = round(data["Close"].rolling(window=5).mean().iloc[-1], 2)
        ma_25 = round(data["Close"].rolling(window=25).mean().iloc[-1], 2)

        return {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "rsi": rsi,
            "ma_5": ma_5,
            "ma_25": ma_25
        }
    except Exception as e:
        return {"error": str(e)}

# 為替（USD→JPY）を取得
@app.get("/forex")
def get_usd_to_jpy():
    url = "https://v6.exchangerate-api.com/v6/087c34db065dd231d0b4e3db/pair/USD/JPY"
    response = requests.get(url)
    data = response.json()

    return {
        "base": data.get("base_code"),
        "target": data.get("target_code"),
        "rate": round(data.get("conversion_rate", 0), 3)
    }
