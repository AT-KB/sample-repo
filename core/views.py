from django.shortcuts import render
import pandas as pd
import markdown2
import logging
from django.http import HttpResponse

from .analysis import (
    get_company_name,
    analyze_stock_candlestick,
    predict_future_moves,
    _load_and_format_financials,
)
from .industry_ticker_map import INDUSTRY_TICKER_MAP
from .gemini_analyzer import generate_analyst_report


def health_check(request):
    """軽量なヘルスチェック用エンドポイント"""
    logging.getLogger(__name__).debug("health check accessed")
    return HttpResponse("OK")


# Legacy attributes kept for test compatibility
_load_financial_metrics = None
_load_quarterly_financials = None
_load_annual_financials = None


def fetch_data(ticker):
    """Helper function to fetch all data for a ticker."""
    if not ticker:
        return {}

    chart_data, latest_table_html, warning = analyze_stock_candlestick(ticker)
    prediction_table_html, _ = predict_future_moves(ticker)

    quarterly_table = _load_and_format_financials(ticker, "quarterly")
    annual_table = _load_and_format_financials(ticker, "annual")

    def html_to_records(html):
        if not html:
            return []
        try:
            return pd.read_html(html)[0].to_dict("records")
        except Exception:
            return []

    latest_dict = html_to_records(latest_table_html)
    prediction_dict = html_to_records(prediction_table_html)

    company_name = get_company_name(ticker)
    gemini_report_md = generate_analyst_report(
        company_name,
        ticker,
        latest_dict,
        prediction_dict,
    )
    gemini_report_html = markdown2.markdown(gemini_report_md)

    return {
        "ticker": ticker,
        "company_name": company_name,
        "chart_data": chart_data,
        "latest_data_table": latest_table_html,
        "prediction_table": prediction_table_html,
        "quarterly_table": quarterly_table,
        "annual_table": annual_table,
        "warning": warning,
        "gemini_report_html": gemini_report_html,
    }


def main_analysis_view(request):
    """Main view for stock analysis."""
    ticker1 = request.GET.get("ticker1", "").strip()
    ticker2 = request.GET.get("ticker2", "").strip()

    data1 = fetch_data(ticker1)
    data2 = fetch_data(ticker2)

    context = {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "data1": data1,
        "data2": data2,
        "industry_map": INDUSTRY_TICKER_MAP,
    }
    return render(request, "core/main_analysis.html", context)
