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
The JQUANTS API is no longer used, so no token is required.

## Development

Example Git workflow:

```bash
git init
git add .
git commit -m "Initial commit"
```

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
