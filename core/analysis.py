import io
import base64
import yfinance as yf
import pandas as pd
import mplfinance as mpf


def generate_stock_plot(ticker: str) -> str:
    """Fetch stock data and return a base64 candlestick plot."""
    df = yf.download(ticker, period="1y", interval="1d")[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)

    buf = io.BytesIO()
    mpf.plot(
        df,
        type="candle",
        mav=(5, 25, 75),
        volume=True,
        title=f"{ticker} Daily Candlestick and Volume",
        style="yahoo",
        figscale=1.2,
        savefig=buf
    )
    buf.seek(0)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return encoded
