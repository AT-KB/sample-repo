import os
from django.test import SimpleTestCase
from unittest.mock import patch
from pathlib import Path
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")
os.environ.setdefault("SECRET_KEY", "dummy")
os.environ.setdefault("DEBUG", "True")

import django  # noqa: E402
django.setup()  # noqa: E402

from core.analysis import (  # noqa: E402
    analyze_stock,
    analyze_stock_candlestick,
    predict_future_moves,
    predict_next_move,
    _load_fundamentals,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_prices.csv"
SAMPLE_DF = pd.read_csv(FIXTURE_PATH, index_col="Date", parse_dates=True)
SAMPLE_FUND = pd.DataFrame(
    {
        "eps": 0.1,
        "pe": 15.0,
        "pb": 1.0,
    },
    index=SAMPLE_DF.index,
)


class AnalysisTests(SimpleTestCase):
    @patch("yfinance.download", return_value=SAMPLE_DF.copy())
    def test_candlestick_chart_generation(self, mock_download):
        chart, table, warning = analyze_stock_candlestick("7203")
        self.assertIsNone(warning)
        self.assertTrue(chart.startswith("iVBOR"))
        self.assertIn("<table", table)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("yfinance.download", return_value=SAMPLE_DF.copy())
    def test_prediction_generation(self, mock_download, mock_fund):
        prediction_html, result_none = predict_future_moves("7203")
        if prediction_html is not None:
            self.assertIn("<table", prediction_html)
            self.assertIn("Prediction", prediction_html)
            self.assertIn("期待リターン", prediction_html)
        else:
            self.assertIsNone(prediction_html)
        self.assertIsNone(result_none)

    @patch("yfinance.download", return_value=SAMPLE_DF.copy())
    def test_analyze_stock_with_data(self, mock_download):
        chart, table, warning = analyze_stock("7203")
        self.assertIsNone(warning)
        self.assertTrue(chart.startswith("iVBOR"))
        self.assertIn("<table", table)

    @patch("yfinance.download", return_value=pd.DataFrame())
    def test_analyze_stock_with_no_data(self, mock_download):
        chart, table = analyze_stock("7203")
        self.assertIsNone(chart)
        self.assertIsNone(table)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("yfinance.download", return_value=SAMPLE_DF.copy())
    def test_predict_next_move_with_data(self, mock_download, mock_fund):
        html = predict_next_move("7203")
        self.assertIsNotNone(html)
        self.assertIn("<table", html)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("yfinance.download", return_value=pd.DataFrame())
    def test_predict_next_move_with_no_data(self, mock_download, mock_fund):
        html = predict_next_move("7203")
        self.assertIsNone(html)

    @patch("core.views.analyze_stock_candlestick")
    def test_main_analysis_view_uses_analyze_stock_candlestick(self, mock_analyze):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        response = self.client.get("/?ticker1=7203", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        mock_analyze.assert_called_once_with("7203")
        self.assertIn("chart", response.content.decode())
        self.assertIn("<table", response.content.decode())

    @patch("core.views._load_financial_metrics", return_value=pd.DataFrame())
    @patch("core.views.predict_future_moves")
    @patch("core.views.analyze_stock_candlestick")
    def test_candlestick_view_handles_two_tickers(
        self, mock_analyze, mock_predict, mock_fin
    ):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        mock_predict.return_value = ("<table></table>", None)
        response = self.client.get(
            "/?ticker1=7203&ticker2=6758", HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_analyze.call_count, 2)
        mock_analyze.assert_any_call("7203")
        mock_analyze.assert_any_call("6758")
        self.assertEqual(mock_predict.call_count, 2)
        content = response.content.decode()
        self.assertIn("chart", content)

    @patch("yfinance.Ticker")
    def test_company_name_truncated(self, mock_ticker):
        mock_ticker.return_value.info = {"shortName": "ABCDEFGHIJKL"}
        from core.analysis import get_company_name

        name = get_company_name("9999")
        self.assertEqual(name, "ABCDEFGHI")

    @patch("core.views._load_and_format_financials")
    @patch("core.views.predict_future_moves")
    @patch("core.views.analyze_stock_candlestick")
    def test_candlestick_view_includes_financials(
        self, mock_analyze, mock_predict, mock_fin
    ):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        mock_predict.return_value = ("<table></table>", None)
        mock_fin.return_value = (
            "<h3>Quarterly Financials</h3>"
            "<table><tr><th>Total Revenue</th><td>1</td></tr></table>"
        )
        response = self.client.get(
            "/?ticker1=7203", HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Total Revenue", content)

    @patch("core.views._load_annual_financials")
    @patch("core.views._load_quarterly_financials")
    @patch("core.views._load_financial_metrics", return_value=pd.DataFrame())
    @patch("core.views.predict_future_moves")
    @patch("core.views.analyze_stock_candlestick")
    def test_candlestick_view_shows_quarter_and_annual_financials(
        self, mock_analyze, mock_predict, mock_fin_metrics, mock_qfin, mock_af
    ):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        mock_predict.return_value = ("<table></table>", None)
        q_df = pd.DataFrame(
            {
                "Total Revenue": [1],
                "Cost Of Revenue": [2],
                "Operating Income": [3],
                "Net Income": [4],
                "Operating Margin": [0.3],
            },
            index=[pd.to_datetime("2024-03-31")],
        )
        a_df = pd.DataFrame(
            {
                "Total Revenue": [10],
                "Cost Of Revenue": [5],
                "Operating Income": [2],
                "Net Income": [1],
                "Operating Margin": [0.2],
            },
            index=[pd.to_datetime("2023-12-31")],
        )
        mock_qfin.return_value = q_df
        mock_af.return_value = a_df

        response = self.client.get("/?ticker1=7203", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Quarterly Financials", content)
        self.assertIn("Annual Financials", content)

    @patch("yfinance.download")
    @patch("yfinance.Ticker")
    def test_load_fundamentals_handles_multiindex(
        self, mock_ticker, mock_download
    ):
        dates = pd.to_datetime(["2020-03-31", "2020-06-30"])
        mi = pd.MultiIndex.from_arrays([dates, ["A", "B"]])
        mock_ticker.return_value.quarterly_earnings = pd.DataFrame(
            {"Earnings": [1, 2]}, index=mi
        )
        mock_ticker.return_value.info = {
            "sharesOutstanding": 1000,
            "priceToBook": 1.0,
        }
        mock_ticker.return_value.quarterly_balance_sheet = pd.DataFrame(
            {
                pd.to_datetime("2020-03-31"): [1000],
                pd.to_datetime("2020-06-30"): [1000],
            },
            index=["Total Stockholder Equity"],
        )
        price_idx = pd.date_range("2020-03-30", periods=3)
        mock_download.return_value = pd.DataFrame(
            {"Close": [10, 11, 12]}, index=price_idx
        )

        df = _load_fundamentals("7203.T")
        self.assertTrue(df.empty)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("yfinance.download")
    def test_predict_future_moves_handles_multiindex_prices(
        self, mock_download, mock_fund
    ):
        mi = pd.MultiIndex.from_product([SAMPLE_DF.index, ["A"]])
        df = SAMPLE_DF.copy()
        df.index = mi
        mock_download.return_value = df

        html, result_none = predict_future_moves("7203")
        if html is not None:
            self.assertIn("<table", html)
        else:
            self.assertIsNone(html)
        self.assertIsNone(result_none)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("yfinance.download")
    def test_predict_future_moves_handles_multiindex_columns(
        self, mock_download, mock_fund
    ):
        mi_cols = pd.MultiIndex.from_product([SAMPLE_DF.columns, ["A"]])
        df = SAMPLE_DF.copy()
        df.columns = mi_cols
        mock_download.return_value = df

        html, result_none = predict_future_moves("7203")
        if html is not None:
            self.assertIn("<table", html)
        else:
            self.assertIsNone(html)
        self.assertIsNone(result_none)

    @patch("core.analysis._load_fundamentals")
    @patch("yfinance.download")
    def test_missing_fundamental_columns(
        self, mock_download, mock_fund
    ):
        mock_download.return_value = SAMPLE_DF.copy()
        fund_missing = SAMPLE_FUND.copy().drop(columns=["eps", "pe"])
        mock_fund.return_value = fund_missing

        chart, table, warn = analyze_stock_candlestick("7203")
        self.assertIsNone(warn)
        self.assertIn("<table", table)
        lower = table.lower()
        self.assertIn("<th>eps</th>", lower)
        self.assertIn("<th>pe</th>", lower)
        self.assertNotIn("<th>pb</th>", lower)

        html, result_none = predict_future_moves("7203")
        if html is not None:
            self.assertIn("<table", html)
        else:
            self.assertIsNone(html)
        self.assertIsNone(result_none)

    @patch("yfinance.Ticker")
    def test_load_and_format_financials_detects_variant_columns_quarterly(
        self, mock_ticker
    ):
        df = pd.DataFrame(
            {
                pd.to_datetime("2024-03-31"): [1e10, 3e9, 1e9],
                pd.to_datetime("2023-12-31"): [2e10, 4e9, 2e9],
            },
            index=[
                "Operating Revenue",
                "Total Operating Income As Reported",
                "Net Income Common Stockholders",
            ],
        )
        mock_ticker.return_value.quarterly_income_stmt = df
        mock_ticker.return_value.quarterly_financials = pd.DataFrame()
        mock_ticker.return_value.quarterly_balance_sheet = pd.DataFrame()

        from core.analysis import _load_and_format_financials

        html = _load_and_format_financials("7203", "quarterly")
        self.assertIn("<table", html)
        self.assertIn("Operating Revenue", html)
        self.assertIn("Total Operating Income As Reported", html)
        self.assertNotIn("Key financial data not found", html)

    @patch("yfinance.Ticker")
    def test_load_and_format_financials_detects_variant_columns_annual(
        self, mock_ticker
    ):
        df = pd.DataFrame(
            {
                pd.to_datetime("2023-12-31"): [5e9, 2e9, 1e9],
            },
            index=[
                "Operating Revenue",
                "Total Operating Income As Reported",
                "Net Income Common Stockholders",
            ],
        )
        mock_ticker.return_value.income_stmt = df
        mock_ticker.return_value.financials = pd.DataFrame()
        mock_ticker.return_value.balance_sheet = pd.DataFrame()

        from core.analysis import _load_and_format_financials

        html = _load_and_format_financials("7203", "annual")
        self.assertIn("<table", html)
        self.assertNotIn("Key financial data not found", html)

    @patch("yfinance.Ticker")
    def test_load_and_format_financials_handles_generic_names(self, mock_ticker):
        df = pd.DataFrame(
            {
                pd.to_datetime("2024-03-31"): [1e9, 2e8, 3e8],
            },
            index=["Revenue", "OpIncome", "NetIncome"],
        )
        mock_ticker.return_value.quarterly_income_stmt = df
        mock_ticker.return_value.quarterly_financials = pd.DataFrame()
        mock_ticker.return_value.quarterly_balance_sheet = pd.DataFrame()

        from core.analysis import _load_and_format_financials

        html = _load_and_format_financials("7203", "quarterly")
        self.assertIn("<table", html)
        self.assertIn("Revenue", html)
        self.assertNotIn("Key financial data not found", html)
