# SPORTI Platform

Plateforme web (PWA) permettant a une entreprise de communiquer en prive et
en temps reel avec chacun de ses clients : chat interne, gestion des medias,
tableau de bord administrateur, themes clair/sombre, internationalisation.

Projet monolithique : Django sert directement les templates (Tailwind CSS +
JS), pas de frontend separe.

## Stack technique

- Backend : Python 3.12, Django 5.x
- Temps reel : Django Channels + Redis
- Base de donnees : PostgreSQL 16
- Frontend : Django Templates, Tailwind CSS, JavaScript
- Auth : django-allauth (Google OAuth 2.0)

## Demarrage rapide

  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements/dev.txt
  cp .env.example .env
  docker compose up -d
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py runserver

## Convention de branches

- main : code stable, toujours deployable
- develop : integration des fonctionnalites
- feature/<nom> : une branche par tache ClickUp
- fix/<nom> : correctifs

## Convention de commits

  feat: ajout de l'authentification Google
  fix: correction de la pagination des messages
  chore: mise a jour des dependances
  docs: mise a jour du README
