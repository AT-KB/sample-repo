from django.shortcuts import render
from .analysis import generate_stock_plot


def analysis_view(request):
    ticker = request.GET.get("ticker", "7203.T")  # default Toyota
    chart = None
    error = None
    if ticker:
        try:
            chart = generate_stock_plot(ticker)
        except Exception as exc:
            error = str(exc)
    return render(request, "core/analysis.html", {"chart": chart, "ticker": ticker, "error": error})
