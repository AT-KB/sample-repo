import google.generativeai as genai
import os
import pandas as pd

# 環境変数からAPIキーを設定
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY is not set.")


def generate_analyst_report(
    ticker_name,
    ticker_code,
    latest_data_html,
    predictions_html,
):
    """Takes stock data and predictions, queries the Gemini API,
    and returns a formatted analysis report."""
    if not api_key:
        return (
            "Gemini API key is not configured. "
            "Please set the GEMINI_API_KEY environment variable."
        )

    # HTMLテーブルをシンプルなテキストに変換（簡易版）
    try:
        latest_data = pd.read_html(latest_data_html)[0].to_string()
        predictions = pd.read_html(predictions_html)[0].to_string()
    except Exception:
        latest_data = "N/A"
        predictions = "N/A"

    prompt = f"""
あなたはプロの証券アナリストです。テクニカル分析とファンダメンタルズ分析の両方に精通しており、客観的なデータに基づき、冷静かつ的確な投資判断を下すことを得意としています。
これから、私のアシスタントとして、特定の銘柄に関する分析レポートを作成してください。

### 分析対象銘柄
- 銘柄名: {ticker_name}
- 銘柄コード: {ticker_code}

### 【データ1】テクニカル指標とモデルによる予測
{latest_data}
{predictions}

### 【データ2】最新のファンダメンタルズ情報（Web検索）
- **指示:** あなた自身の能力（Webブラウジング機能）を使って、この銘柄の直近の決算発表の内容を調べてください。
- **調査項目:**
    - 最新の四半期の「売上高」「営業利益」は、市場コンセンサス予想と比較してどうでしたか？
    - 通期の業績見通しに変更はありましたか？
    - 経営陣が強調している、今後のビジネスの追い風や逆風は何ですか？

### 【あなたのタスク】総合分析レポートの作成
以下の構成でレポートを作成してください。

1. **サマリー（3行で要約）**
2. **テクニカル分析**
3. **ファンダメンタルズ分析**
4. **総合的な投資判断と戦略**
   - **推奨アクションプラン**（推奨買値、推奨売値、時間軸）

プロフェッショナルとして、客観的かつ論理的な分析を期待しています。
"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating report from Gemini: {e}"
