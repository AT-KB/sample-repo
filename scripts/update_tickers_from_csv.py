import os
from pathlib import Path

import django
import pandas as pd
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")
django.setup()

from core.models import Industry, Ticker  # noqa: E402

# スクリプトファイルの場所を基点にプロジェクトルートの絶対パスを取得
BASE_DIR = Path(__file__).resolve().parent.parent

KEEP_MARKETS = {
    "プライム（内国株式）",
    "グロース（内国株式）",
    "スタンダード（内国株式）",
}


def main():
    print("Loading CSV data...")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df = df[df["市場・商品区分"].isin(KEEP_MARKETS)]
    df = df[df["33業種区分"].notna()]

    print("Updating database...")
    with transaction.atomic():
        Ticker.objects.all().delete()
        Industry.objects.all().delete()

        industry_names = sorted(df["33業種区分"].unique())
        industries = [Industry(name=name) for name in industry_names]
        Industry.objects.bulk_create(industries)
        industry_map = {ind.name: ind for ind in Industry.objects.all()}

        tickers = []
        for _, row in df.iterrows():
            ind = industry_map[row["33業種区分"]]
            code = str(row["コード"]).zfill(4)
            tickers.append(Ticker(code=code, name=row["銘柄名"], industry=ind))
        Ticker.objects.bulk_create(tickers)

    print("Generating industry_ticker_map.py...")
    industry_map = {}
    for industry in Industry.objects.all().order_by("name"):
        ticks = list(
            Ticker.objects.filter(industry=industry)
            .order_by("code")
            .values("code", "name")
        )
        industry_map[industry.name] = ticks

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "core", "industry_ticker_map.py"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("INDUSTRY_TICKER_MAP = {\n")
        for ind, ticks in industry_map.items():
            f.write(f"    {ind!r}: [\n")
            for t in ticks:
                f.write(
                    f"        {{'code': {t['code']!r}, 'name': {t['name']!r}}},\n"
                )
            f.write("    ],\n")
        f.write("}\n")
    print(f"Wrote {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
