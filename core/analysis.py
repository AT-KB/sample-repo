import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import mplfinance as mpf
import ta

TICKER_NAMES = {
    "7203": "トヨタ自動車",
    "7203.T": "トヨタ自動車",
    "6758": "ソニーグループ",
    "6758.T": "ソニーグループ",
    "8591": "オリックス",
    "8591.T": "オリックス",
}


def get_company_name(ticker: str) -> str:
    """Return company name if available, otherwise the ticker itself."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith(".T") else ticker
    if ticker in TICKER_NAMES:
        return TICKER_NAMES[ticker]
    if ticker_symbol in TICKER_NAMES:
        return TICKER_NAMES[ticker_symbol]
    try:
        info = yf.Ticker(ticker_symbol).info
        return info.get("shortName") or info.get("longName") or ticker_symbol
    except Exception:
        return ticker_symbol


def analyze_stock(ticker: str):
    """Fetch data and return base64 chart image and HTML table."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="1y", interval="1d", auto_adjust=False)
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
        .round(0)
        .fillna(0)
        .astype(int)
        .to_html(classes="table table-striped")
    )

    return chart_data, table_html, None


def analyze_stock_candlestick(ticker: str):
    """Generate candlestick chart with volume, MACD, and RSI."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    try:
        stock_data = yf.download(
            ticker_symbol,
            period="6mo",
            interval="1d",
            auto_adjust=False,
        )
        stock_data.columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Adj Close",
            "Volume",
        ]
    except Exception:
        return None, None, "データ取得に失敗しました"
    if stock_data.empty:
        return None, None, "データ取得に失敗しました"

    stock_data["MA5"] = stock_data["Close"].rolling(window=5).mean()
    stock_data["MA25"] = stock_data["Close"].rolling(window=25).mean()
    stock_data["MA75"] = stock_data["Close"].rolling(window=75).mean()

    close_series = stock_data["Close"].squeeze()
    stock_data["MACD"] = ta.trend.macd(close_series)
    stock_data["MACD_signal"] = ta.trend.macd_signal(close_series)
    stock_data["RSI"] = ta.momentum.rsi(close_series)

    plot_df = (
        stock_data[["Open", "High", "Low", "Close", "Volume"]]
        .dropna()
        .astype(float)
    )
    plot_df.dropna(inplace=True)

    apds = [
        mpf.make_addplot(stock_data["MACD"], panel=2, color="blue", ylabel="MACD"),
        mpf.make_addplot(stock_data["MACD_signal"], panel=2, color="orange"),
        mpf.make_addplot(stock_data["RSI"], panel=3, color="purple", ylabel="RSI"),
    ]

    try:
        fig, ax = mpf.plot(
            plot_df,
            type="candle",
            mav=(5, 25, 75),
            volume=True,
            addplot=apds,
            title=f"{ticker_symbol} Daily Candlestick, MACD & RSI",
            style="yahoo",
            returnfig=True,
            figsize=(16, 10),
            panel_ratios=(3, 1, 1, 1),
        )
    except Exception as e:
        return None, None, "チャート生成に失敗しました"

    fig.subplots_adjust(hspace=0.15)
    for axis in fig.axes:
        ymin = axis.get_ylim()[0]
        axis.axhline(y=ymin, color="black", lw=0.5)

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    table_html = (
        stock_data.tail(5)[["Close", "MA5", "MA25", "MA75", "MACD", "MACD_signal", "RSI"]]
        .round(0)
        .fillna(0)
        .astype(int)
        .to_html(classes="table table-striped")
    )

    return chart_data, table_html, None


def generate_stock_plot(ticker: str):
    """Return base64 encoded line plot for given ticker."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="3mo", interval="1d", auto_adjust=False)
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
    """Convenience wrapper to get only the one-day prediction."""
    table_html, _ = predict_future_moves(ticker, horizons=[1])
    return table_html


def predict_future_moves(ticker: str, horizons=None):
    """Predict stock direction for multiple days ahead with expected return."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith('.T') else ticker
    df = yf.download(ticker_symbol, period="2y", interval="1d", auto_adjust=False)
    if len(df) < 30:
        return (None, None)

    if horizons is None:
        horizons = [1, 7, 28]

    df["Return"] = df["Close"].pct_change()
    for i in range(1, 6):
        df[f"lag_{i}"] = df["Return"].shift(i)
    df.dropna(inplace=True)

    X = df[[f"lag_{i}" for i in range(1, 6)]]
    results = []
    from sklearn.linear_model import LogisticRegression

    importance_model = None
    for h in horizons:
        df[f"target_{h}"] = (df["Close"].shift(-h) > df["Close"]).astype(int)
        df[f"future_return_{h}"] = df["Close"].shift(-h) / df["Close"] - 1
        y = df[f"target_{h}"]
        split = int(len(df) * 0.7)
        X_train = X[:split]
        y_train = y[:split]
        returns_train = df[f"future_return_{h}"][:split]
        model = LogisticRegression(max_iter=200, random_state=0)
        model.fit(X_train, y_train)
        prob_up = model.predict_proba(X.iloc[[-1]])[0, 1] * 100
        prediction = "UP" if prob_up >= 50 else "DOWN"

        train_pred = model.predict(X_train)
        up_mask = (train_pred == 1) & (y_train == 1)
        down_mask = (train_pred == 0) & (y_train == 0)
        up_return = returns_train[up_mask].mean()
        down_return = returns_train[down_mask].mean()
        expected_return = up_return if prediction == "UP" else down_return
        if pd.isna(expected_return):
            expected_return = 0.0

        results.append(
            {
                "予測日数": h,
                "Prediction": prediction,
                "上昇確率": round(prob_up),
                "期待リターン": round(expected_return * 100, 2),
            }
        )
        importance_model = model

    table = pd.DataFrame(results)
    prob_col = "上昇確率"

    def highlight(val: float) -> str:
        if val >= 70:
            return "background-color: lightgreen"
        elif val <= 30:
            return "background-color: lightcoral"
        return ""

    styled_table = (
        table.style.applymap(highlight, subset=[prob_col])
        .hide(axis="index")
        .set_table_attributes('class="table table-striped"')
    )

    coef = importance_model.coef_.flatten()
    importance_df = pd.DataFrame({"Feature": X.columns, "Importance": abs(coef)})
    importance_df.sort_values("Importance", ascending=False, inplace=True)

    return (
        styled_table.to_html(),
        importance_df.to_html(classes="table table-striped", index=False),
    )
