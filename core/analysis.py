import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import mplfinance as mpf


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


def analyze_stock_candlestick(ticker: str):
    """Generate candlestick chart with volume and MA lines."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="6mo", interval="1d")
    if df.empty:
        return None, None

    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA25"] = df["Close"].rolling(window=25).mean()
    df["MA75"] = df["Close"].rolling(window=75).mean()

    plot_df = df[["Open", "High", "Low", "Close", "Volume"]].dropna().astype(float)

    fig, ax = mpf.plot(
        plot_df,
        type="candle",
        mav=(5, 25, 75),
        volume=True,
        title=f"{ticker_symbol} Daily Candlestick and Volume (MA:5,25,75)",
        style="yahoo",
        returnfig=True,
        figsize=(12, 8),
    )

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    table_html = (
        df.tail(5)[["Close", "MA5", "MA25", "MA75"]]
        .round(2)
        .to_html(classes="table table-striped")
    )

    return chart_data, table_html


def generate_stock_plot(ticker: str):
    """Return base64 encoded line plot for given ticker."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="3mo", interval="1d")
    if df.empty:
        return None

    df["MA20"] = df["Close"].rolling(window=20).mean()

    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df["Close"], label="Close")
    plt.plot(df.index, df["MA20"], label="MA20")
    plt.legend()
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def predict_next_move(ticker: str):
    """Simple ML model predicting next day's move (UP/DOWN)."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="2y", interval="1d")
    if len(df) < 30:
        return None

    df["Return"] = df["Close"].pct_change()
    for i in range(1, 6):
        df[f"lag_{i}"] = df["Return"].shift(i)
    df.dropna(inplace=True)

    X = df[[f"lag_{i}" for i in range(1, 6)]]
    y = (df["Return"] > 0).astype(int)

    split = int(len(df) * 0.7)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    from sklearn.linear_model import LogisticRegression

    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)

    latest_features = X.iloc[[-1]]
    prob = model.predict_proba(latest_features)[0, 1]
    prediction = "UP" if prob >= 0.5 else "DOWN"

    table = pd.DataFrame(
        {
            "Next Day": [df.index[-1] + pd.Timedelta(days=1)],
            "Prediction": [prediction],
            "Probability": [round(prob, 4)],
        }
    )
    return table.to_html(classes="table table-striped", index=False)
