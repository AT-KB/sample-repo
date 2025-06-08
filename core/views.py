from django.shortcuts import render
from .analysis import analyze_stock, analyze_stock_candlestick


def stock_analysis_view(request):
    chart_data = None
    table_html = None
    ticker = ""

    ticker = request.GET.get("ticker", "").strip()
    if ticker:
        chart_data, table_html = analyze_stock(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "table_html": table_html,
    }
    return render(request, "core/stock_analysis.html", context)


def candlestick_analysis_view(request):
    chart_data = None
    table_html = None
    ticker = ""

    ticker = request.GET.get("ticker", "").strip()
    if ticker:
        chart_data, table_html = analyze_stock_candlestick(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "table_html": table_html,
    }
    return render(request, "core/candlestick_analysis.html", context)
