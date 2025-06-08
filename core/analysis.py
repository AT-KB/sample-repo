import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
import base64


def analyze_stock(ticker: str):
    """Fetch data and return base64 chart image and HTML table."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="1y", interval="1d")
    if df.empty:
        return None, None

    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA25"] = df["Close"].rolling(window=25).mean()

    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df["Close"], label="Close")
    plt.plot(df.index, df["MA5"], label="MA5")
    plt.plot(df.index, df["MA25"], label="MA25")
    plt.legend()
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title(f"{ticker_symbol} Close Price")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    table_html = (
        df.tail(5)[["Close", "MA5", "MA25"]]
        .round(2)
        .to_html(classes="table table-striped")
    )

    return chart_data, table_html
