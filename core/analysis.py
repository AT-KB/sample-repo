import base64
from datetime import timedelta
from io import BytesIO

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import ta
import yfinance as yf
import numpy as np
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

INDUSTRY_TICKER_MAP = {
    "自動車": {"7203": "トヨタ自動車", "7203.T": "トヨタ自動車"},
    "電機": {"6758": "ソニーグループ", "6758.T": "ソニーグループ"},
    "金融": {"8591": "オリックス", "8591.T": "オリックス"},
    "海運": {
        "9101": "日本郵船",
        "9101.T": "日本郵船",
        "9104": "商船三井",
        "9104.T": "商船三井",
    },
}


def _get_first_non_empty(tkr: yf.Ticker, attrs: list[str]) -> pd.DataFrame:
    """Return the first non-empty DataFrame among ticker attributes."""
    for attr in attrs:
        df = getattr(tkr, attr, None)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return pd.DataFrame()


def _fetch_fin_stmt(tkr: yf.Ticker, attrs: list[str]) -> pd.DataFrame:
    """Return the first non-empty financial statement DataFrame."""
    for attr in attrs:
        df = getattr(tkr, attr, None)
        if isinstance(df, pd.DataFrame) and not df.empty:
            df = df.copy()
            if isinstance(df.index, pd.MultiIndex):
                df.index = df.index.get_level_values(0)
            return df
    return pd.DataFrame()


def _load_fundamentals(ticker_symbol: str) -> pd.DataFrame:
    """Return EPS, PE, PB data indexed by announcement date."""
    try:
        tkr = yf.Ticker(ticker_symbol)
        info = tkr.info
        eps_q = None
        if getattr(tkr, "quarterly_earnings", None) is not None:
            qe = tkr.quarterly_earnings
            if (
                isinstance(qe, pd.DataFrame)
                and not qe.empty
                and not isinstance(qe.index, pd.MultiIndex)
                and "Earnings" in qe
            ):
                eps_q = qe["Earnings"]
        if eps_q is None or eps_q.empty:
            trailing_eps = info.get("trailingEps")
            if trailing_eps is None:
                return pd.DataFrame()
            eps_q = pd.Series(
                trailing_eps / 4,
                index=[pd.to_datetime("today").normalize()],
            )

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

        qbs = tkr.quarterly_balance_sheet
        equity = None
        if isinstance(qbs, pd.DataFrame) and "Total Stockholder Equity" in qbs.index:
            equity = qbs.loc["Total Stockholder Equity"]
        shares = info.get("sharesOutstanding")
        if equity is not None and shares and shares > 0:
            book_value_per_share = equity / shares
            pb = price_on_announce / book_value_per_share.reindex(
                eps_q.index, method="ffill"
            )
        else:
            pb_value = info.get("priceToBook")
            pb = pd.Series(pb_value, index=eps_q.index)

        pe = pe.replace([np.inf, -np.inf], np.nan)
        pb = pb.replace([np.inf, -np.inf], np.nan)

        if pe.isna().all():
            trailing_pe = info.get("trailingPE")
            if trailing_pe is not None:
                pe = pd.Series(trailing_pe, index=eps_q.index)
            else:
                pe = pd.Series(np.nan, index=eps_q.index)

        if pb.isna().all():
            pb_info = info.get("priceToBook")
            if pb_info is not None:
                pb = pd.Series(pb_info, index=eps_q.index)
            else:
                pb = pd.Series(np.nan, index=eps_q.index)

        df_fund = pd.DataFrame({"eps": eps_q, "pe": pe, "pb": pb})
        df_fund.index = df_fund.index + timedelta(days=1)
        df_fund.index.name = "date"
        df_fund = df_fund.reset_index().set_index("date")

        df_fund.ffill(inplace=True)

        return df_fund
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


def _load_and_format_financials(ticker_symbol: str, period: str) -> str:
    """Return HTML table for quarterly or annual financials."""
    title = "Quarterly Financials" if period == "quarterly" else "Annual Financials"
    try:
        tkr = yf.Ticker(ticker_symbol)
        if period == "quarterly":
            attrs = [
                "quarterly_income_stmt",
                "quarterly_financials",
                "quarterly_balance_sheet",
            ]
            limit = 4
        else:
            attrs = ["income_stmt", "financials", "balance_sheet"]
            limit = 3

        df = _fetch_fin_stmt(tkr, attrs)
        if not isinstance(df, pd.DataFrame) or df.empty:
            return f"<h3>{title}</h3><p>Data not available.</p>"

        df = df.T

        revenue_candidates = ["Total Revenue", "Operating Revenue", "Revenue"]
        op_income_candidates = [
            "Operating Income",
            "Total Operating Income As Reported",
            "Operating Profit",
            "OpIncome",
        ]
        net_income_candidates = [
            "Net Income",
            "Net Income Common Stockholders",
            "NetIncome",
        ]

        detected_cols = []
        for candidates in [
            revenue_candidates,
            op_income_candidates,
            net_income_candidates,
        ]:
            for col in candidates:
                if col in df.columns:
                    detected_cols.append(col)
                    break

        if not detected_cols:
            return f"<h3>{title}</h3><p>Key financial data not found.</p>"

        df_display = df[detected_cols].head(limit)

        def fmt_value(val: float) -> str:
            if pd.isna(val):
                return "-"
            if abs(val) >= 1e9:
                return f"{val/1e9:,.0f}B"
            return f"{val/1e6:,.0f}M"

        for col in df_display.columns:
            df_display[col] = df_display[col].apply(fmt_value)

        return f"<h3>{title}</h3>" + df_display.to_html(classes="table table-striped")

    except Exception as e:
        return f"<h3>{title}</h3><p>Error loading data: {e}</p>"


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
        .to_html(classes="table table-striped", index=False)
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
        merge_cols = [c for c in ["eps", "pe"] if c in fund.columns]
        stock_data = stock_data.merge(
            fund[merge_cols], left_index=True, right_index=True, how="left"
        )
        for c in merge_cols:
            stock_data[c] = stock_data[c].ffill()
    else:
        stock_data["eps"] = None
        stock_data["pe"] = None

    if "eps" not in stock_data.columns:
        stock_data["eps"] = None
    if "pe" not in stock_data.columns:
        stock_data["pe"] = None

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

    tbl_cols = ["Close", "MACD", "RSI", "eps", "pe"]
    table_df = stock_data.tail(5)[tbl_cols].round(0)
    table_df = table_df.map(lambda x: "-" if pd.isna(x) else int(x))
    table_html = table_df.reset_index().rename(columns={"index": "date"}).to_html(
        classes="table table-striped", index=False
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
    ticker_symbol = f"{ticker}.T" if not ticker.endswith(".T") else ticker
    df = yf.download(ticker_symbol, period="2y", interval="1d", auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
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
    for col in ["eps", "pe", "pb"]:
        if col not in df.columns:
            df[col] = 0
    df.set_index("date", inplace=True)
    if fund.empty:
        df[["eps", "pe", "pb"]] = 0
        df[["eps", "pe", "pb"]].fillna(0, inplace=True)
    else:
        df[["eps", "pe", "pb"]] = df[["eps", "pe", "pb"]].ffill()

    # テクニカル指標の計算
    df["Return"] = df["Close"].pct_change()
    for i in range(1, 6):
        df[f"lag_{i}"] = df["Return"].shift(i)

    df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"]).rsi()
    macd_indicator = ta.trend.MACD(close=df["Close"])
    df["macd"] = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_diff"] = macd_indicator.macd_diff()
    stoch_indicator = ta.momentum.StochasticOscillator(
        high=df["High"], low=df["Low"], close=df["Close"]
    )
    df["stoch"] = stoch_indicator.stoch()
    df["stoch_signal"] = stoch_indicator.stoch_signal()
    df["atr"] = ta.volatility.AverageTrueRange(
        high=df["High"], low=df["Low"], close=df["Close"]
    ).average_true_range()

    # \u2605\u2605\u2605\u2605\u2605 ここからが最重要の修正点 \u2605\u2605\u2605\u2605\u2605

    # 1. 目的変数と将来リターンを先に計算し、欠損値をまとめて処理
    if horizons is None:
        horizons = [1, 7, 28]
    for h in horizons:
        df[f"target_{h}"] = (df["Close"].shift(-h) > df["Close"]).astype(int)
        df[f"future_return_{h}"] = df["Close"].pct_change(periods=h).shift(-h)

    # 2. 特徴量と目的変数が揃っている行だけを最終的な学習データとする
    feature_cols = [f"lag_{i}" for i in range(1, 6)] + [
        "eps",
        "pe",
        "pb",
        "rsi",
        "macd",
        "macd_signal",
        "macd_diff",
        "stoch",
        "stoch_signal",
        "atr",
    ]
    target_cols = [f"target_{h}" for h in horizons]
    return_cols = [f"future_return_{h}" for h in horizons]

    df_clean = df[feature_cols + target_cols + return_cols].dropna()

    X = df_clean[feature_cols]
    X.columns = [str(c) for c in X.columns]

    results = []
    tscv = TimeSeriesSplit(n_splits=5)

    for h in horizons:
        y_h = df_clean[f"target_{h}"]
        returns_h = df_clean[f"future_return_{h}"]

        if len(X) <= tscv.n_splits:
            continue

        model = None
        final_train_index = None
        for train_index, _ in tscv.split(X):
            model = LGBMClassifier(
                random_state=0,
                learning_rate=0.05,
                n_estimators=200,
                num_leaves=31,
                max_depth=-1,
                reg_alpha=0.1,
                reg_lambda=0.1,
                n_jobs=-1,
            )
            model.fit(X.iloc[train_index], y_h.iloc[train_index])
            final_train_index = train_index

        if model is None or final_train_index is None:
            continue

        prob_up = model.predict_proba(X.iloc[[-1]])[0, 1]
        prediction = "UP" if prob_up >= 0.5 else "DOWN"

        # 期待リターンの計算ロジックを再構築
        train_pred = model.predict(X.iloc[final_train_index])
        y_train = y_h.iloc[final_train_index]
        returns_train = returns_h.iloc[final_train_index]

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
                "上昇確率": round(prob_up * 100),
                "期待リターン": expected_return,
            }
        )

    if not results:
        return (None, None)

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
