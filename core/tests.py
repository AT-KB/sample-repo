from django.test import SimpleTestCase
from .analysis import analyze_stock_candlestick, predict_future_moves


class AnalysisTests(SimpleTestCase):
    def test_candlestick_chart_generation(self):
        chart, table = analyze_stock_candlestick("7203")
        self.assertIsNotNone(chart)
        self.assertIsNotNone(table)

    def test_prediction_generation(self):
        table = predict_future_moves("7203")
        self.assertIsNotNone(table)
