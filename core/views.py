from django.shortcuts import render
from .analysis import (
    get_company_name,
    analyze_stock_candlestick,
    predict_future_moves,
    _load_and_format_financials,
)
from .gemini_analyzer import generate_analyst_report

# Legacy attributes kept for test compatibility
_load_financial_metrics = None
_load_quarterly_financials = None
_load_annual_financials = None


def fetch_data(ticker):
    """Helper function to fetch all data for a ticker."""
    if not ticker:
        return {}

    chart_data, latest_data_table, warning = analyze_stock_candlestick(ticker)
    prediction_table, _ = predict_future_moves(ticker)

    quarterly_table = _load_and_format_financials(ticker, "quarterly")
    annual_table = _load_and_format_financials(ticker, "annual")

    company_name = get_company_name(ticker)
    gemini_report = generate_analyst_report(
        company_name,
        ticker,
        latest_data_table or "",
        prediction_table or "",
    )

    return {
        "ticker": ticker,
        "company_name": company_name,
        "chart_data": chart_data,
        "latest_data_table": latest_data_table,
        "prediction_table": prediction_table,
        "quarterly_table": quarterly_table,
        "annual_table": annual_table,
        "warning": warning,
        "gemini_report": gemini_report,
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
    }
    return render(request, "core/main_analysis.html", context)
