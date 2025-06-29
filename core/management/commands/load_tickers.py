from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Industry, Ticker


class Command(BaseCommand):
    help = "Load tickers from data_j.xls"

    def handle(self, *args, **options):
        path = Path(settings.BASE_DIR) / "data_j.xls"
        df = pd.read_excel(path, header=0, engine="xlrd")
        for _, row in df.iterrows():
            if pd.isna(row[0]) or pd.isna(row[1]) or pd.isna(row[2]):
                continue
            industry_name = row[0]
            code = str(row[1]).zfill(4)
            name = row[2]
            industry, _ = Industry.objects.get_or_create(name=industry_name)
            Ticker.objects.update_or_create(
                code=code,
                defaults={"name": name, "industry": industry},
            )
        self.stdout.write(self.style.SUCCESS("Tickers loaded"))
