from django.shortcuts import render
from .analysis import analyze_stock


def stock_analysis_view(request):
    chart_data = None
    table_html = None
    ticker = ""

    if request.method == "POST":
        ticker = request.POST.get("ticker", "").strip()
        if ticker:
            chart_data, table_html = analyze_stock(ticker)

    context = {
        "ticker": ticker,
        "chart_data": chart_data,
        "table_html": table_html,
    }
    return render(request, "core/stock_analysis.html", context)
