FROM python:3.11.10-slim
# Build-time SECRET_KEY arg for collectstatic
ARG SECRET_KEY="django-insecure-placeholder"
ENV SECRET_KEY=${SECRET_KEY}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "myapp.wsgi", "--bind", "0.0.0.0:8000", "--log-file", "-"]
