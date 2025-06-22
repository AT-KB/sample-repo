import os
import pandas as pd
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY is not set.")


def generate_analyst_report(
    ticker_name: str,
    ticker_code: str,
    latest_data_dict: list[dict],
    predictions_dict: list[dict],
) -> str:
    """Generate a professional stock report using Gemini."""
    if not api_key or os.environ.get("PYTEST_CURRENT_TEST"):
        msg = "Gemini API key is not configured. "
        if api_key is None:
            msg += "Please set the GEMINI_API_KEY environment variable."
        else:
            msg += "(test mode)"
        return msg

    def df_to_text(data: list[dict]) -> str:
        if not data:
            return "(no data)"
        try:
            return pd.DataFrame(data).to_string(index=False)
        except Exception:
            return "(failed to parse data)"

    latest_text = df_to_text(latest_data_dict)
    predictions_text = df_to_text(predictions_dict)

    prompt = f"""
あなたは経験豊富な証券アナリストです。以下のデータに誤りがないか軽く確認した上で、
銘柄 {ticker_name} ({ticker_code}) の分析レポートを Markdown 形式で作成してください。

### テクニカルデータ
{latest_text}

### 予測データ
{predictions_text}
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:  # pragma: no cover - external API
        return f"Error generating report from Gemini: {e}"
