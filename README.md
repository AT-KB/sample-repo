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

For local development, create a `.env` file and define your environment variables:

```bash
SECRET_KEY=d^2$4jbvh*ihfkdupc(p#6q_i6trs!$x&&19+i*fj3hfh9u&cr
DATABASE_URL=your-database-url
DEBUG=True
ALLOWED_HOSTS=*
JQUANTS_TOKEN=your-token  # optional
```

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
