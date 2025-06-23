# ベースとなるOSとPythonのバージョンを指定
FROM python:3.11-slim

# システムライブラリを更新し、ビルドに必要なツールをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# ★★★★★ ここが最重要ポイント ★★★★★
# distutils問題とnumpyのバイナリ問題を回避するため、
# requirements.txtを先にコピーし、依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコード全体をコピー
COPY . .

# ポートを開放
EXPOSE 8080

# 起動コマンドを設定
# まず銘柄リストを生成し、次にgunicornを起動
CMD ["sh", "-c", "python scripts/generate_ticker_map.py && gunicorn myapp.wsgi --bind 0.0.0.0:8080"]
