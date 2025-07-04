"""core.analysis の関数テスト＆ビュー経由テスト"""
import os
import sys
import types
from pathlib import Path

import django
import pandas as pd
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from core.analysis import analyze_stock_candlestick, predict_future_moves

# --- Django 環境設定 (この後にコードは書かない) ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
os.environ.setdefault('SECRET_KEY', 'a-dummy-secret-key-for-testing')
os.environ.setdefault('DEBUG', 'True')
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'
os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1'
django.setup()
from core.models import Industry, Ticker

# ダミーの industry_ticker_map モジュール
sys.modules.setdefault(
    'core.industry_ticker_map',
    types.SimpleNamespace(INDUSTRY_TICKER_MAP={}),
)
# ダミーの gemini_analyzer モジュール
sys.modules.setdefault(
    'core.gemini_analyzer',
    types.SimpleNamespace(generate_analyst_report=lambda *a, **k: ""),
)

# --- テスト用サンプルデータ準備 ---
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_prices.csv"
SAMPLE_DF = pd.read_csv(FIXTURE_PATH, index_col="Date", parse_dates=True)
SAMPLE_FUND = pd.DataFrame(
    {"eps": 0.1, "pe": 15.0, "pb": 1.0},
    index=SAMPLE_DF.index,
)


from django.test import TestCase


class AnalysisTests(TestCase):
    """core.analysis 関数と main_analysis ビューのテスト"""

    @classmethod
    def setUpTestData(cls):
        industry = Industry.objects.create(name="dummy")
        Ticker.objects.create(code="7203", name="Toyota", industry=industry)
        Ticker.objects.create(code="6758", name="Sony", industry=industry)

    @patch("core.analysis.yf.download", return_value=SAMPLE_DF.copy())
    def test_candlestick_chart_generation(self, mock_download):
        chart, table, warning = analyze_stock_candlestick("7203")
        self.assertIsNone(warning)
        self.assertTrue(chart.startswith("iVBOR"))
        self.assertIn("<table", table)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("core.analysis.yf.download", return_value=SAMPLE_DF.copy())
    def test_prediction_generation(self, mock_download, mock_fund):
        html, none_val = predict_future_moves("7203")
        self.assertIsNone(none_val)
        if html:
            self.assertIn("<table", html)
            self.assertIn("予想方向", html)
            self.assertIn("期待リターン", html)

    @patch("core.views._load_and_format_financials", return_value="")
    @patch("core.views.predict_future_moves", return_value=("<table></table>", None))
    @patch("core.views.analyze_stock_candlestick")
    def test_main_analysis_view_with_one_ticker(
        self, mock_analyze, mock_predict, mock_fin
    ):
        mock_analyze.return_value = ("chart_data_string", "<table></table>", None)
        url = reverse("main_analysis") + "?ticker1=7203"
        response = self.client.get(url, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        mock_analyze.assert_called_once_with("7203")
        self.assertIn("chart_data_string", response.content.decode())

    @patch("core.views._load_and_format_financials", return_value="")
    @patch("core.views.predict_future_moves", return_value=("<table></table>", None))
    @patch("core.views.analyze_stock_candlestick")
    def test_main_view_handles_two_tickers(
        self, mock_analyze, mock_predict, mock_fin
    ):
        mock_analyze.return_value = ("chart_data_string", "<table></table>", None)
        url = reverse("main_analysis") + "?ticker1=7203&ticker2=6758"
        response = self.client.get(url, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_analyze.call_count, 2)
        mock_analyze.assert_any_call("7203")
        mock_analyze.assert_any_call("6758")
        self.assertEqual(mock_predict.call_count, 2)

    @patch("core.views._load_and_format_financials")
    @patch("core.views.predict_future_moves", return_value=("<table></table>", None))
    @patch("core.views.analyze_stock_candlestick")
    def test_main_view_shows_quarter_and_annual_financials(
        self, mock_analyze, mock_predict, mock_fin
    ):
        mock_analyze.return_value = ("chart_data_string", "<table></table>", None)
        mock_fin.side_effect = [
            "<h3>Quarterly Financials</h3><table></table>",
            "<h3>Annual Financials</h3><table></table>",
        ]
        url = reverse("main_analysis") + "?ticker1=7203"
        response = self.client.get(url, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Quarterly Financials", content)
        self.assertIn("Annual Financials", content)
