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
あなたは、ウォール街で20年の経験を持つ、トップクラスの証券アナリストです。あなたのレポートは、客観的なデータと鋭い洞察力で、機関投資家からも絶大な信頼を得ています。

これから、以下の銘柄について、プロフェッショナルな分析レポートを **Markdown形式** で作成してください。

### **分析対象銘柄**
- **銘柄名:** {ticker_name}
- **銘柄コード:** {ticker_code}

---

### **ステップ1：データ収集（あなたのWeb検索能力を使ってください）**

まず、以下の情報を信頼できる情報源（日経新聞、ブルームバーグ、企業のIRページ、EDINETなど）から徹底的に調査・収集してください。

1.  **最新の決算情報:**
    - 直近の四半期決算の発表日、売上高、営業利益、純利益。
    - 上記の数値が、市場コンセンサス予想に対してどうだったか（例: "売上は予想を+5%上振れ、利益は-2%下振れ"）。
2.  **業績見通し:**
    - 会社が発表している最新の通期業績見通し（売上高、営業利益）。
    - 直近でこの見通しに修正（上方/下方）はあったか。
3.  **バリュエーション指標:**
    - 現在のPER、PBR、配当利回り。
    - 同業他社（最低2社）のPER、PBRと比較して、割安か割高か。
4.  **アナリスト評価:**
    - 主要な証券会社のアナリストレーティングのコンセンサス（例: "強気: 5人, 中立: 3人, 弱気: 0人"）。
    - 目標株価の平均値。
5.  **カタリスト（株価材料）:**
    - **ポジティブ材料:** 経営陣が強調する成長戦略、新技術、市況の好転など。
    - **ネガティブ材料:** 懸念されているリスク、規制強化、市況の悪化など。

---

### **ステップ2：レポート作成（Markdown形式）**

上記の調査結果と、以下に示すテクニカル指標を統合し、以下の厳密なフォーマットでレポートを出力してください。

```markdown
# 銘柄分析レポート：{ticker_name} ({ticker_code})

## 1. 投資判断サマリー
| 総合評価 | 時間軸 | 推奨アクション |
|:---:|:---:|:---:|
| **（ここに「強気」「中立」「弱気」のいずれかを入れる）** | （短期/中期/長期） | （新規買い/ホールド/利益確定/損切り） |

**【結論（3行要約）】**
（ここに、なぜその投資判断に至ったのか、最も重要な根拠を3行で要約）

---

## 2. ファンダメンタルズ分析
| 項目 | 数値 | 評価 |
|:--- |:--- |:--- |
| PER | （調査結果） | （割安/適正/割高） |
| PBR | （調査結果） | （割安/適正/割高） |
| 配当利回り | （調査結果）% | （魅力的/平均的/低い）|
| 業績成長性 | （調査結果） | （強い/安定/懸念あり） |
| アナリスト評価 | （調査結果） | （ポジティブ/中立/ネガティブ） |

**【分析コメント】**
（上記の評価の根拠と、調査で判明したポジティブ/ネガティブ材料について、プロとして簡潔に解説）

---

## 3. テクニカル分析
**【入力データ】**
{latest_data}
{predictions}

**【分析コメント】**
（上記入力データに基づき、短期的なモメンタムと、自社モデルの予測傾向を解説。予測に矛盾があればそれも指摘）

---

## 4. 具体的な戦略プラン
- **エントリーポイント（推奨買値）:** （具体的な価格帯や、判断の根拠となるテクニカル指標を提示）
- **ターゲットプライス（利食い目安）:** （アナリストの目標株価や、フィボナッチ等から算出した具体的な価格を提示）
- **ストップロス（損切りライン）:** （直近の安値や、重要なサポートラインなど、具体的な価格を提示）

---
*免責事項: このレポートは情報提供を目的としており、投資を勧誘するものではありません。投資の最終判断はご自身の責任で行ってください。*
```
"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating report from Gemini: {e}"
