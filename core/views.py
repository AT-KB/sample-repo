from django.shortcuts import render
from .analysis import (
    analyze_stock_candlestick,
    predict_future_moves,
    get_company_name,
    _load_financial_metrics,
    _load_quarterly_financials,
    _load_annual_financials,
)


def main_analysis_view(request):
    ticker1 = request.GET.get("ticker1", "").strip()
    ticker2 = request.GET.get("ticker2", "").strip()

    def fetch_data(ticker: str):
        if not ticker:
            return {}
        chart_data, table_html, warning = analyze_stock_candlestick(ticker)
        prediction_table = None
        company_name = get_company_name(ticker)
        fund_table_html = None
        quarterly_fin_html = None
        annual_fin_html = None
        if warning is None:
            prediction_table, _ = predict_future_moves(ticker)
        fund_df = _load_financial_metrics(ticker)
        if not fund_df.empty:
            fund_table_html = fund_df.to_html(classes="table table-striped")
        q_df = _load_quarterly_financials(ticker)
        if not q_df.empty:
            quarterly_fin_html = q_df.to_html(classes="table table-striped")
        a_df = _load_annual_financials(ticker)
        if not a_df.empty:
            annual_fin_html = a_df.to_html(classes="table table-striped")
        return {
            "chart_data": chart_data,
            "table_html": table_html,
            "prediction_table": prediction_table,
            "warning": warning,
            "company_name": company_name,
            "fund_table_html": fund_table_html,
            "quarterly_table": quarterly_fin_html,
            "annual_table": annual_fin_html,
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
