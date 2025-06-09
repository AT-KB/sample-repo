from django.shortcuts import render
from .analysis import (
    analyze_stock,
    analyze_stock_candlestick,
    generate_stock_plot,
    predict_next_move,
    predict_future_moves,
)


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
    prediction_table = None
    features_table = None
    warning = None
    ticker = ""

    ticker = request.GET.get("ticker", "").strip()
    if ticker:
        chart_data, table_html, warning = analyze_stock_candlestick(ticker)
        if warning is None:
            prediction_table, features_table = predict_future_moves(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "table_html": table_html,
        "prediction_table": prediction_table,
        "features_table": features_table,
        "warning": warning,
    }
    return render(request, "core/candlestick_analysis.html", context)


def analysis_view(request):
    chart_data = None
    prediction_table = None
    ticker = request.GET.get("ticker", "").strip()
    if ticker:
        chart_data = generate_stock_plot(ticker)
        prediction_table = predict_next_move(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "prediction_table": prediction_table,
    }
    return render(request, "core/analysis.html", context)
