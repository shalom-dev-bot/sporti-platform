from django.contrib import admin

from .models import Event, Prediction, Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("home_team", "away_team", "competition", "sport", "kickoff_at")
    list_filter = ("sport", "competition")
    search_fields = ("home_team__name", "away_team__name", "competition")


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "pick",
        "confidence",
        "is_featured",
        "result",
        "is_published",
        "created_at",
    )
    list_filter = ("result", "is_published", "is_featured")
    search_fields = ("pick", "analysis")
