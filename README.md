# MyApp

This is a simple Django project containing a single application `core`.

## File layout

- `myapp/` – Django project settings and URLs.
- `core/` – App created with `python manage.py startapp core`.
- `manage.py` – Django management utility.
- `requirements.txt` – Python dependencies.
- `Procfile` – Process definition for deployment.
- `README.md` – This guide.

## Deploying with Railway

1. Install the [Railway CLI](https://railway.app/).
2. Run the following commands to create the project and add a Postgres database:

   ```bash
   railway init        # create Railway project
   railway add         # add Postgres plugin
   ```
3. In the Railway dashboard, add the environment variables `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, and `ALLOWED_HOSTS`.
4. When deploying to Railway or any other host, the service should supply a proper `DATABASE_URL`. If not provided, the value from the `.env` file will be used.
   Set `SECRET_KEY` to `d^2$4jbvh*ihfkdupc(p#6q_i6trs!$x&&19+i*fj3hfh9u&cr`.
5. Set `ALLOWED_HOSTS` to a comma-separated list of domain names, such as `example.com`.
6. When `DEBUG=True`, `localhost` and `127.0.0.1` are added automatically. If no hosts are configured after this, the application falls back to `*`.
7. If you plan to use [J-Quants](https://jpx-jquants.com/), sign up for a free account to obtain your API token and add it to the dashboard as `JQUANTS_TOKEN`. Otherwise, this variable can be omitted.

## Development

Example Git workflow:

```bash
git init
git add .
git commit -m "Initial commit"
```

For local development, create a `.env` file at the project root (next to `manage.py`).
This file is listed in `.gitignore`, so it will not be committed to the repository.
Add the following environment variables:

```bash
SECRET_KEY=d^2$4jbvh*ihfkdupc(p#6q_i6trs!$x&&19+i*fj3hfh9u&cr
DATABASE_URL=your-database-url
DEBUG=True
ALLOWED_HOSTS=*
JQUANTS_TOKEN=your-token  # optional
GEMINI_API_KEY=あなたのAPIキー
```

**Important:** Variable names must match exactly with no spaces.

| Correct Name | Common Mistakes |
|--------------|-----------------|
| `SECRET_KEY` | `SECRET KEY` |
| `DATABASE_URL` | `DATABASE URL` |
| `DEBUG` | `Debug` |
| `ALLOWED_HOSTS` | `ALLOWED HOSTS` |

Place the file in the root directory so Django can load these settings. `SECRET_KEY` is a random string for cryptographic signing, `DATABASE_URL` specifies your database connection, `DEBUG` turns debug mode on or off, and `ALLOWED_HOSTS` lists valid domain names. `JQUANTS_TOKEN` enables optional J-Quants features.

Required variables: `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`.
Optional variable: `JQUANTS_TOKEN`.

Install dependencies and run the server:

For local development, use Django's built-in development server. It's easy to use and automatically reloads when you change your code.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations (if any)
python manage.py migrate

# 3. Start the development server
python manage.py runserver
```
Your application will now be running at http://127.0.0.1:8000/.
IMPORTANT NOTE: The gunicorn command found in railway.json is for the production environment on Railway only. It will not work in your local environment because the $PORT variable is not set. Always use python manage.py runserver for local development.

## Running Tests

Install the dependencies and execute the test suite with `pytest`:

The test commands require the same environment variables defined in `.env`, so ensure they are present before running `pytest`.

```bash
pip install -r requirements.txt
pytest
```

## Charts and predictions

The application shows extra panels below the stock price chart:

- **MACD panel** – compares two moving averages to reveal momentum.
- **RSI panel** – highlights when the market may be overbought or oversold.
- **Prediction table** – lists the model's forecasts for several upcoming days.

These indicators rely on the `ta` package, which is already listed in
`requirements.txt`.

## 銘柄リストの更新
最新の銘柄リストを取得するには、以下のコマンドを実行してください。
これにより、`core/industry_ticker_map.py` が自動生成されます。

```bash
python scripts/generate_ticker_map.py
```

## Deploy to Railway

1. **Railway CLI をインストール**（ローカル環境で一度だけ）
   ```bash
   # npm
   npm install -g railway
   # macOS Homebrew
   brew tap railway/homebrew && brew install railway
   ```

2. **ログイン＆プロジェクト設定**
   ```bash
   railway login
   railway link       # 既存プロジェクトを紐付け
   # または
   railway init       # 新規プロジェクト作成
   ```

3. **デプロイ**
   ```bash
   railway up --detach
   ```

4. **環境変数の登録**
   ```bash
   railway variables set GEMINI_API_KEY=<あなたのキー>
   railway variables set JQUANTS_TOKEN=<あなたのトークン>
   ```
