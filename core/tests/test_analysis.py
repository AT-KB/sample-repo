import os
from django.test import SimpleTestCase
from unittest.mock import patch
from pathlib import Path
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")
os.environ.setdefault("SECRET_KEY", "dummy")
os.environ.setdefault("DEBUG", "True")

import django
django.setup()

from core.analysis import (
    analyze_stock,
    analyze_stock_candlestick,
    predict_future_moves,
    predict_next_move,
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
        self.assertIn("<table", prediction_html)
        self.assertIn("Prediction", prediction_html)
        self.assertIn("期待リターン", prediction_html)
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

    @patch("core.views.analyze_stock")
    def test_stock_analysis_view_uses_analyze_stock(self, mock_analyze):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        response = self.client.get("/stock/?ticker=7203", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        mock_analyze.assert_called_once_with("7203")
        self.assertIn("chart", response.content.decode())
        self.assertIn("<table", response.content.decode())

    @patch("core.views._load_financial_metrics", return_value=pd.DataFrame())
    @patch("core.views.predict_future_moves")
    @patch("core.views.analyze_stock_candlestick")
    def test_candlestick_view_handles_two_tickers(self, mock_analyze, mock_predict, mock_fin):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        mock_predict.return_value = ("<table></table>", None)
        response = self.client.get(
            "/candlestick/?ticker1=7203&ticker2=6758", HTTP_HOST="localhost"
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

    @patch("core.views._load_financial_metrics")
    @patch("core.views.predict_future_moves")
    @patch("core.views.analyze_stock_candlestick")
    def test_candlestick_view_includes_financials(self, mock_analyze, mock_predict, mock_fin):
        mock_analyze.return_value = ("chart", "<table></table>", None)
        mock_predict.return_value = ("<table></table>", None)
        mock_fin.return_value = pd.DataFrame({
            "Total Revenue": [1],
            "Cost Of Revenue": [2],
            "Selling General Administrative": [3],
            "Operating Income": [4],
            "Net Income": [5],
        })
        response = self.client.get("/candlestick/?ticker1=7203", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Total Revenue", content)

