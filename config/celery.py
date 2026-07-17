"""
Configuration Celery : execute les taches lourdes (compression d'images,
plus tard notifications push, etc.) en arriere-plan, sans jamais bloquer
la reponse envoyee a l'utilisateur.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("sporti")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
