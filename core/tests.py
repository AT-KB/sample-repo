from django.test import SimpleTestCase
from unittest.mock import patch
from pathlib import Path
import pandas as pd

from .analysis import analyze_stock_candlestick, predict_future_moves


FIXTURE_PATH = Path(__file__).parent / "tests" / "fixtures" / "sample_prices.csv"
SAMPLE_DF = pd.read_csv(FIXTURE_PATH, index_col="Date", parse_dates=True)


class AnalysisTests(SimpleTestCase):
    @patch("yfinance.download", return_value=SAMPLE_DF.copy())
    def test_candlestick_chart_generation(self, mock_download):
        chart, table = analyze_stock_candlestick("7203")
        self.assertTrue(chart.startswith("iVBOR"))
        self.assertIn("<table", table)

    @patch("yfinance.download", return_value=SAMPLE_DF.copy())
    def test_prediction_generation(self, mock_download):
        table = predict_future_moves("7203")
        self.assertIn("<table", table)
        self.assertIn("Prediction", table)
