from django.shortcuts import render, get_object_or_404
import pandas as pd
import markdown2
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from .analysis import (
    get_company_name,
    analyze_stock_candlestick,
    predict_future_moves,
    _load_and_format_financials,
)
from collections import OrderedDict
from .models import Industry, Ticker
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

    industries = Industry.objects.all().prefetch_related("ticker_set").order_by("name")
    industry_map_data = OrderedDict()
    for industry in industries:
        tickers = industry.ticker_set.order_by("code").values("code", "name")
        industry_map_data[industry.name] = list(tickers)

    context = {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "data1": data1,
        "data2": data2,
        "industry_map": industry_map_data,
    }
    return render(request, "core/main_analysis.html", context)


class IndustryListAPIView(APIView):
    """Return all industries."""

    def get(self, request):
        industries = Industry.objects.all().values("id", "name")
        return Response(list(industries))


class IndustryTickerAPIView(APIView):
    """Return tickers for a specific industry."""

    def get(self, request, pk):
        industry = get_object_or_404(Industry, pk=pk)
        tickers = (
            Ticker.objects.filter(industry=industry)
            .values("code", "name")
            .order_by("code")
        )
        return Response(list(tickers))
