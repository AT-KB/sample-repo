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
3. In the Railway dashboard, add the environment variables `SECRET_KEY`, `DATABASE_URL`, and `DEBUG`.
4. Sign up for a free account at [J-Quants](https://jpx-jquants.com/) to obtain your API token. Add this token to the Railway dashboard as `JQUANTS_TOKEN`.

## Development

Example Git workflow:

```bash
git init
git add .
git commit -m "Initial commit"
```

For local development, create a `.env` file and define your environment variables:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
DEBUG=True
JQUANTS_TOKEN=your-token
```

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
