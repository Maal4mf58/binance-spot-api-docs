python robo_trade.py
from binance.client import Client
import pandas as pd
import time

# Suas chaves da TESTNET
API_KEY = oDDgEoK6oOmhFG5vlvoppcWXuwpsUEQ7bUuA59kuw4TmLdBl9Fx3J7uoABg8DLjz

API_SECRET = Azbw09a01yApbnZagcBOQxXdL5gBg6xelen1Zjkxiyvwpzz7rN0j5VQCXo1qNQpk

client = Client(API_KEY, API_SECRET, testnet=True)

# Lista de pares que o robô vai operar
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# Função para pegar dados históricos
def get_data(symbol, interval="1h", lookback="1 day ago UTC"):
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=[
        "timestamp","open","high","low","close","volume","close_time",
        "quote_asset_volume","number_of_trades","taker_buy_base","taker_buy_quote","ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

# Estratégia simples: cruzamento de médias móveis
def strategy(df):
    df["MM_curta"] = df["close"].rolling(window=9).mean()
    df["MM_longa"] = df["close"].rolling(window=21).mean()
    if df["MM_curta"].iloc[-1] > df["MM_longa"].iloc[-1]:
        return "BUY"
    elif df["MM_curta"].iloc[-1] < df["MM_longa"].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"

# Execução da ordem com Stop Loss e Take Profit
def execute_order(signal, symbol, qty=0.001, stop_loss_pct=0.02, take_profit_pct=0.04):
    price = float(client.get_symbol_ticker(symbol=symbol)["price"])
    if signal == "BUY":
        order = client.order_market_buy(symbol=symbol, quantity=qty)
        print(f"[{symbol}] Ordem de COMPRA executada:", order)

        stop_price = round(price * (1 - stop_loss_pct), 2)
        take_profit_price = round(price * (1 + take_profit_pct), 2)

        client.create_oco_order(
            symbol=symbol,
            side="SELL",
            quantity=qty,
            price=str(take_profit_price),
            stopPrice=str(stop_price),
            stopLimitPrice=str(stop_price * 0.99),
            stopLimitTimeInForce="GTC"
        )
        print(f"[{symbol}] OCO SELL criado: Stop {stop_price}, TP {take_profit_price}")

    elif signal == "SELL":
        order = client.order_market_sell(symbol=symbol, quantity=qty)
        print(f"[{symbol}] Ordem de VENDA executada:", order)

        stop_price = round(price * (1 + stop_loss_pct), 2)
        take_profit_price = round(price * (1 - take_profit_pct), 2)

        client.create_oco_order(
            symbol=symbol,
            side="BUY",
            quantity=qty,
            price=str(take_profit_price),
            stopPrice=str(stop_price),
            stopLimitPrice=str(stop_price * 1.01),
            stopLimitTimeInForce="GTC"
        )
        print(f"[{symbol}] OCO BUY criado: Stop {stop_price}, TP {take_profit_price}")

# Loop principal
while True:
    for symbol in symbols:
        df = get_data(symbol)
        signal = strategy(df)
        print(f"[{symbol}] Sinal:", signal)
        if signal in ["BUY", "SELL"]:
            execute_order(signal, symbol)
    time.sleep(3600)  # espera 1 hora antes da próxima análise
