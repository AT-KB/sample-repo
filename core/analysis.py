import base64
from datetime import timedelta
from io import BytesIO

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import ta
import yfinance as yf
from lightgbm import LGBMClassifier
from sklearn.model_selection import TimeSeriesSplit

TICKER_NAMES = {
    "7203": "トヨタ自動車",
    "7203.T": "トヨタ自動車",
    "6758": "ソニーグループ",
    "6758.T": "ソニーグループ",
    "8591": "オリックス",
    "8591.T": "オリックス",
    "9101": "日本郵船",
    "9101.T": "日本郵船",
    "9104": "商船三井",
    "9104.T": "商船三井",
}


def _load_fundamentals(ticker_symbol: str) -> pd.DataFrame:
    """Return EPS, PE, PB data indexed by announcement date."""
    try:
        tkr = yf.Ticker(ticker_symbol)
        eps_q = tkr.quarterly_earnings["Earnings"]
        # マルチインデックスは扱わない
        if eps_q.empty or isinstance(eps_q.index, pd.MultiIndex):
            return pd.DataFrame()

        start_date = eps_q.index.min() - timedelta(days=2)
        end_date = eps_q.index.max() + timedelta(days=2)
        price_data = yf.download(
            ticker_symbol,
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=False,
        )
        if price_data.empty:
            return pd.DataFrame()

        price_on_announce = price_data["Close"].reindex(
            eps_q.index, method="ffill"
        )
        pe = price_on_announce / eps_q

        info = tkr.info
        equity = tkr.quarterly_balance_sheet.get("Total Stockholder Equity")
        shares = info.get("sharesOutstanding")
        if equity is not None and shares and shares > 0:
            book_value_per_share = equity / shares
            pb = price_on_announce / book_value_per_share.reindex(
                eps_q.index, method="ffill"
            )
        else:
            pb_value = info.get("priceToBook")
            pb = pd.Series(pb_value, index=eps_q.index)

        df_fund = pd.DataFrame({"eps": eps_q, "pe": pe, "pb": pb})
        df_fund.index = df_fund.index + timedelta(days=1)
        df_fund.ffill(inplace=True)
        df_fund.index.name = "date"
        df_fund = df_fund.reset_index().set_index("date")

        return df_fund
    except Exception:
        return pd.DataFrame()


def _load_financial_metrics(ticker_symbol: str) -> pd.DataFrame:
    """Return selected yearly financial metrics."""
    try:
        df = yf.Ticker(ticker_symbol).financials.T
        cols = [
            "Total Revenue",
            "Cost Of Revenue",
            "Selling General Administrative",
            "Operating Income",
            "Net Income",
        ]
        return df[cols]
    except Exception:
        return pd.DataFrame()


def get_company_name(ticker: str) -> str:
    """Return truncated company name if available."""
    ticker_symbol = f"{ticker}.T" if not ticker.endswith(".T") else ticker
    name = TICKER_NAMES.get(ticker) or TICKER_NAMES.get(ticker_symbol)
    if not name:
        try:
            info = yf.Ticker(ticker_symbol).info
            name = info.get("shortName") or info.get("longName") or ticker_symbol
        except Exception:
            name = ticker_symbol
    return str(name)[:9]


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

    close_series = stock_data["Close"].squeeze()
    stock_data["MACD"] = ta.trend.macd(close_series)
    stock_data["RSI"] = ta.momentum.rsi(close_series)

    fund = _load_fundamentals(ticker_symbol)
    if not fund.empty:
        stock_data = stock_data.merge(
            fund[["pe", "pb"]], left_index=True, right_index=True, how="left"
        )
        stock_data[["pe", "pb"]] = stock_data[["pe", "pb"]].ffill()
    else:
        stock_data["pe"] = None
        stock_data["pb"] = None

    plot_df = (
        stock_data[["Open", "High", "Low", "Close", "Volume"]]
        .dropna()
        .astype(float)
    )
    plot_df.dropna(inplace=True)

    apds = [
        mpf.make_addplot(stock_data["MACD"], panel=2, color="blue", ylabel="MACD"),
        mpf.make_addplot(stock_data["RSI"], panel=3, color="purple", ylabel="RSI"),
    ]

    try:
        fig, ax = mpf.plot(
            plot_df,
            type="candle",
            mav=(),
            volume=True,
            addplot=apds,
            title=f"{ticker_symbol} Daily Candlestick, MACD & RSI",
            style="yahoo",
            returnfig=True,
            figsize=(20, 12),
            panel_ratios=(3, 1, 1, 1),
        )
    except Exception:
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
        stock_data.tail(5)[["Close", "MACD", "RSI", "pe", "pb"]]
        .round(2)
        .fillna(0)
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

    fund = _load_fundamentals(ticker_symbol)
    if isinstance(df.index, pd.MultiIndex):
        df.index = df.index.get_level_values(0)
    if isinstance(fund.index, pd.MultiIndex):
        fund.index = fund.index.get_level_values(0)

    df.index = pd.to_datetime(df.index)
    fund.index = pd.to_datetime(fund.index)

    df.index.name = "date"
    fund.index.name = "date"
    df = df.reset_index()
    fund = fund.reset_index()
    df = df.merge(fund, how="left", on="date")
    df.set_index("date", inplace=True)
    if fund.empty:
        df[["eps", "pe", "pb"]] = df[["Close"]].pct_change() * 0
        df[["eps", "pe", "pb"]].fillna(0, inplace=True)
    else:
        df[["eps", "pe", "pb"]] = df[["eps", "pe", "pb"]].ffill()

    if horizons is None:
        horizons = [1, 7, 28]

    df["Return"] = df["Close"].pct_change()
    for i in range(1, 6):
        df[f"lag_{i}"] = df["Return"].shift(i)
    df.dropna(subset=["eps", "pe", "pb"], inplace=True)
    df.dropna(inplace=True)

    feature_cols = [f"lag_{i}" for i in range(1, 6)] + ["eps", "pe", "pb"]
    X = df[feature_cols].copy()
    X.columns = [str(c) for c in X.columns]
    results = []
    tscv = TimeSeriesSplit(n_splits=5)

    for h in horizons:
        df[f"target_{h}"] = (df["Close"].shift(-h) > df["Close"]).astype(int)
        df[f"future_return_{h}"] = df["Close"].shift(-h) / df["Close"] - 1
        y = df[f"target_{h}"]
        model = None
        returns_train = None
        train_index = None
        for train_index, _ in tscv.split(X):
            model = LGBMClassifier(random_state=0)
            model.fit(X.iloc[train_index], y.iloc[train_index])
            returns_train = df[f"future_return_{h}"].iloc[train_index]
        if model is None:
            continue
        prob_up = model.predict_proba(X.iloc[[-1]])[0, 1] * 100
        prediction = "UP" if prob_up >= 50 else "DOWN"

        train_pred = model.predict(X.iloc[train_index])
        up_mask = (train_pred == 1) & (y.iloc[train_index] == 1)
        down_mask = (train_pred == 0) & (y.iloc[train_index] == 0)
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

    table = pd.DataFrame(results)
    prob_col = "上昇確率"

    def color_scale(val: float) -> str:
        if val == 50:
            return ""
        if val > 50:
            alpha = min((val - 50) / 50, 1)
            return f"background-color: rgba(0, 255, 0, {alpha:.2f})"
        alpha = min((50 - val) / 50, 1)
        return f"background-color: rgba(255, 0, 0, {alpha:.2f})"

    styled_table = (
        table.style.applymap(color_scale, subset=[prob_col])
        .format({prob_col: "{:.0f}%", "期待リターン": lambda x: f"{x:+.2f}%"})
        .hide(axis="index")
        .set_table_attributes('class="table table-striped"')
    )

    return (
        styled_table.to_html(),
        None,
    )
