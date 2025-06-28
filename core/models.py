from django.db import models


class Industry(models.Model):
    """Industry name master."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Ticker(models.Model):
    """Ticker information."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.code} {self.name}"
