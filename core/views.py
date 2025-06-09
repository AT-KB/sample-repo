from django.shortcuts import render
from .analysis import (
    analyze_stock,
    analyze_stock_candlestick,
    generate_stock_plot,
    predict_future_moves,
    predict_next_move,
    get_company_name,
)


def stock_analysis_view(request):
    chart_data = None
    table_html = None
    ticker = ""

    ticker = request.GET.get("ticker", "").strip()
    if ticker:
        chart_data, table_html, _ = analyze_stock(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "table_html": table_html,
    }
    return render(request, "core/stock_analysis.html", context)


def candlestick_analysis_view(request):
    ticker1 = request.GET.get("ticker1", "").strip()
    ticker2 = request.GET.get("ticker2", "").strip()

    def fetch_data(ticker: str):
        if not ticker:
            return {}
        chart_data, table_html, warning = analyze_stock_candlestick(ticker)
        prediction_table = None
        company_name = get_company_name(ticker)
        if warning is None:
            prediction_table, _ = predict_future_moves(ticker)
        return {
            "chart_data": chart_data,
            "table_html": table_html,
            "prediction_table": prediction_table,
            "warning": warning,
            "company_name": company_name,
        }

    data1 = fetch_data(ticker1)
    data2 = fetch_data(ticker2)

    context = {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "data1": data1,
        "data2": data2,
        "company1": data1.get("company_name"),
        "company2": data2.get("company_name"),
    }
    return render(request, "core/candlestick_analysis.html", context)


def analysis_view(request):
    chart_data = None
    prediction_table = None
    ticker = request.GET.get("ticker", "").strip()
    if ticker:
        chart_data = generate_stock_plot(ticker)
        prediction_table, _ = predict_future_moves(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "prediction_table": prediction_table,
    }
    return render(request, "core/analysis.html", context)
