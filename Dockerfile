# Deploiement Railway (demo). Un Dockerfile explicite au lieu de laisser
# Nixpacks deviner l'environnement -- il detectait ce depot comme "Node
# uniquement" (a cause de package.json) et ignorait Python.
#
# Build en deux etapes : l'image Node officielle compile le CSS (Tailwind),
# puis l'image Python recupere uniquement le resultat -- plus rapide et
# plus leger que d'installer Node via apt dans l'image finale.

FROM node:20-slim AS assets
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY static/css/src ./static/css/src
COPY static/js ./static/js
COPY tailwind.config.js ./
COPY templates ./templates
COPY apps ./apps
RUN npm run build-css

FROM python:3.12-slim
ENV DJANGO_SETTINGS_MODULE=config.settings.prod \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY . .
COPY --from=assets /app/static/css/dist ./static/css/dist

RUN python -m pip install --no-cache-dir -r requirements/prod.txt
RUN python manage.py collectstatic --noinput

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
