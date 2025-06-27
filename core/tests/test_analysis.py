import os
from django.test import SimpleTestCase
from django.urls import reverse
from unittest.mock import patch
import sys
import types
from pathlib import Path
import pandas as pd

# --- テスト実行のためのDjango環境設定 ---
# このブロックは、pytestがDjango設定を正しく読み込むために重要です。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")
os.environ.setdefault("SECRET_KEY", "a-dummy-secret-key-for-testing")
os.environ.setdefault("DEBUG", "True")

import django
django.setup()

# core.viewsがインポートできるように、ダミーのモジュールを作成
sys.modules.setdefault(
    "core.industry_ticker_map",
    types.SimpleNamespace(INDUSTRY_TICKER_MAP={}),
)
# --- ここまで ---

from core.analysis import (
    analyze_stock,
    analyze_stock_candlestick,
    predict_future_moves,
    predict_next_move,
    _load_fundamentals,
    get_company_name,
    _load_and_format_financials
)


# --- テスト用のサンプルデータ ---
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
# --- ここまで ---


class AnalysisTests(SimpleTestCase):
    """core.analysisと関連するビューのテスト"""

    # --- analysis.pyの関数テスト ---

    @patch("core.analysis.yf.download", return_value=SAMPLE_DF.copy())
    def test_candlestick_chart_generation(self, mock_download):
        """チャートとテーブルが正常に生成されるか"""
        chart, table, warning = analyze_stock_candlestick("7203")
        self.assertIsNone(warning)
        self.assertTrue(chart.startswith("iVBOR"))
        self.assertIn("<table", table)

    @patch("core.analysis._load_fundamentals", return_value=SAMPLE_FUND.copy())
    @patch("core.analysis.yf.download", return_value=SAMPLE_DF.copy())
    def test_prediction_generation(self, mock_download, mock_fund):
        """予測テーブルが正常に生成されるか"""
        prediction_html, result_none = predict_future_moves("7203")
        self.assertIsNone(result_none)
        if prediction_html is not None:
            self.assertIn("<table", prediction_html)
            self.assertIn("Prediction", prediction_html)
            self.assertIn("期待リターン", prediction_html)

    # --- views.pyのテスト (URL経由) ---

    @patch("core.views._load_and_format_financials", return_value="")
    @patch("core.views.predict_future_moves", return_value=("<table></table>", None))
    @patch("core.views.analyze_stock_candlestick")
    def test_main_analysis_view_with_one_ticker(self, mock_analyze, mock_predict, mock_fin):
        """1つの銘柄でメイン分析ビューが正しく表示されるか"""
        mock_analyze.return_value = ("chart_data_string", "<table></table>", None)
        
        # 'main_analysis'という名前のURLを動的に生成し、クエリパラメータを追加
        url = reverse('main_analysis') + '?ticker1=7203'
        response = self.client.get(url, HTTP_HOST="localhost")
        
        self.assertEqual(response.status_code, 200)
        mock_analyze.assert_called_once_with("7203")
        self.assertIn("chart_data_string", response.content.decode())

    @patch("core.views._load_and_format_financials", return_value="")
    @patch("core.views.predict_future_moves", return_value=("<table></table>", None))
    @patch("core.views.analyze_stock_candlestick")
    def test_main_view_handles_two_tickers(self, mock_analyze, mock_predict, mock_fin):
        """2つの銘柄でメイン分析ビューが正しく表示されるか"""
        mock_analyze.return_value = ("chart_data_string", "<table></table>", None)
        
        url = reverse('main_analysis') + '?ticker1=7203&ticker2=6758'
        response = self.client.get(url, HTTP_HOST="localhost")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_analyze.call_count, 2)
        mock_analyze.assert_any_call("7203")
        mock_analyze.assert_any_call("6758")
        self.assertEqual(mock_predict.call_count, 2)

    @patch("core.views._load_and_format_financials")
    @patch("core.views.predict_future_moves", return_value=("<table></table>", None))
    @patch("core.views.analyze_stock_candlestick")
    def test_main_view_shows_quarter_and_annual_financials(self, mock_analyze, mock_predict, mock_fin):
        """四半期と通期の財務諸表が表示されるか"""
        mock_analyze.return_value = ("chart_data_string", "<table></table>", None)
        mock_fin.side_effect = [
            "<h3>Quarterly Financials</h3><table></table>",
            "<h3>Annual Financials</h3><table></table>",
        ]
        
        url = reverse('main_analysis') + '?ticker1=7203'
        response = self.client.get(url, HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Quarterly Financials", content)
        self.assertIn("Annual Financials", content)

    # --- (その他のテストは変更不要なため、省略またはそのまま維持) ---
    # 以下、必要に応じて元のテストコードを維持してください。
    # この例では主要なビューのテストに絞ってリファクタリングしています。
