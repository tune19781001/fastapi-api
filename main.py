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

# 日本株の株価・RSI・移動平均を取得（安定版）
@app.get("/stock")
def get_stock_data(symbol: str):
    try:
        data = yf.Ticker(symbol).history(period="30d")

        if data is None or data.empty:
            return {
                "symbol": symbol,
                "price": None,
                "volume": None,
                "rsi": None,
                "ma_5": None,
                "ma_25": None,
                "error": "データが取得できませんでした（シンボル確認）"
            }

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
            "ma_25": ma_25,
            "error": None
        }

    except Exception as e:
        return {
            "symbol": symbol,
            "price": None,
            "volume": None,
            "rsi": None,
            "ma_5": None,
            "ma_25": None,
            "error": str(e)
        }

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

# 為替レートに対する簡易コメントを返す関数
def get_forex_comment(rate):
    if rate is None:
        return "為替情報なし"

    if rate > 150:
        return "円安傾向（輸出関連に追い風）"
    elif rate < 145:
        return "円高傾向（輸入関連に追い風）"
    else:
        return "為替は中立圏"

# 株価・為替をまとめて取得する /judge エンドポイント
@app.get("/judge")
def judge(symbol: str = "7203.T"):
    try:
        base_url = "https://judge-api-lcr4.onrender.com"

        stock = requests.get(f"{base_url}/stock?symbol={symbol}").json()
        forex = requests.get(f"{base_url}/forex").json()

        return {
            "symbol": symbol,
            "price": stock.get("price"),
            "volume": stock.get("volume"),
            "rsi": stock.get("rsi"),
            "ma_5": stock.get("ma_5"),
            "ma_25": stock.get("ma_25"),
            "usd_jpy": forex.get("rate"),
            "exchange_comment": get_forex_comment(forex.get("rate")),
            "error": stock.get("error")
        }

    except Exception as e:
        return {"error": str(e)}
