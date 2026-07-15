#!/usr/bin/env python
"""Utilitaire en ligne de commande de Django pour SPORTI."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Verifiez qu'il est installe et "
            "disponible dans votre variable d'environnement PYTHONPATH. "
            "Avez-vous active votre environnement virtuel ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
