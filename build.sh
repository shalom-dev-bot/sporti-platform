#!/usr/bin/env bash
# Script de build execute avant chaque deploiement (Railway, ou Render).
set -o errexit

python3 -m pip install -r requirements/prod.txt

npm ci
npm run build-css

python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput

python3 manage.py shell -c "
from django.contrib.sites.models import Site
import os
site, _ = Site.objects.get_or_create(id=1)
site.name = 'SPORTI'
site.domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN') or os.environ.get('RENDER_EXTERNAL_HOSTNAME', site.domain)
site.save()
print('Site', site.domain, 'pret')
"

python3 manage.py shell -c "
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
