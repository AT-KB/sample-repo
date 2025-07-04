import os
from io import BytesIO
import requests
import pandas as pd

URL = (
    "https://www.jpx.co.jp/markets/statistics-equities/"
    "misc/tvdivq0000001vg2-att/data_j.xls"
)

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "core", "industry_ticker_map.py"
)


def main():
    response = requests.get(URL)
    response.raise_for_status()

    df = pd.read_excel(BytesIO(response.content), sheet_name="Sheet1")
    df = df[["コード", "銘柄名", "33業種区分"]]
    df["コード"] = df["コード"].astype(str).str.zfill(4)

    industry_map = {}
    for _, row in df.iterrows():
        industry = row["33業種区分"]
        code = row["コード"]
        name = row["銘柄名"]
        industry_map.setdefault(industry, {})[code] = name

    out_path = os.path.abspath(OUTPUT_PATH)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("INDUSTRY_TICKER_MAP = {\n")
        for ind, tickers in sorted(industry_map.items()):
            f.write(f"    {ind!r}: {{\n")
            for code, name in sorted(tickers.items()):
                f.write(f"        {code!r}: {name!r},\n")
            f.write("    },\n")
        f.write("}\n")
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
