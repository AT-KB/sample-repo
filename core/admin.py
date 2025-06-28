from django.contrib import admin
from .models import Industry, Ticker


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "industry")
    list_filter = ("industry",)
    search_fields = ("code", "name")
