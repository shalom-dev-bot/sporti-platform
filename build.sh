#!/usr/bin/env bash
# Script de build execute par Render avant chaque deploiement.
set -o errexit

pip install -r requirements/prod.txt

npm ci
npm run build-css

python manage.py collectstatic --noinput
python manage.py migrate --noinput
