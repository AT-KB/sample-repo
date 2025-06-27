import os
import django
from django.test import Client, SimpleTestCase
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")
os.environ.setdefault("SECRET_KEY", "dummy")
os.environ.setdefault("DEBUG", "True")

django.setup()


class HealthCheckTests(SimpleTestCase):
    def test_health_check(self):
        client = Client()
        url = reverse("health_check")
        response = client.get(url, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
