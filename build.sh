#!/usr/bin/env bash
# Script de build execute par Render avant chaque deploiement.
set -o errexit

pip install -r requirements/prod.txt

npm ci
npm run build-css

python manage.py collectstatic --noinput
python manage.py migrate --noinput

python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if username and password:
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print('Superuser', username, 'pret (cree ou mis a jour)')
"
