"""Reglages de production, penses pour un deploiement de demo (Railway,
puis Hostinger pour la version finale une fois le client valide).

Objectif : que le client puisse voir l'appli tourner sans avoir besoin
d'un service Redis payant. Si une variable REDIS_URL est fournie plus
tard (vrai environnement de prod), le chat temps reel et Celery
basculent automatiquement dessus -- rien a changer dans le code.
"""

import os

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# Railway (et la plupart des PaaS) fournissent automatiquement le nom
# d'hote externe du service via une variable d'environnement.
EXTERNAL_HOSTNAME = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "") or os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME", ""
)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[".up.railway.app", ".onrender.com"])
if EXTERNAL_HOSTNAME and EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    f"https://{host.lstrip('.')}" if not host.startswith(".") else f"https://*{host}"
    for host in ALLOWED_HOSTS
]
if EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{EXTERNAL_HOSTNAME}")

# --- Fichiers statiques servis directement par l'appli (WhiteNoise) ---
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# --- Mode demo sans Redis ---
# Sans REDIS_URL, on reste 100% fonctionnel avec une seule instance web :
# - le chat temps reel utilise la memoire du process au lieu de Redis
# - Celery execute les taches immediatement, en synchrone (pas de worker)
# Des que REDIS_URL est defini (vrai environnement de prod), tout repasse
# automatiquement sur Redis sans rien changer ici.
if not os.environ.get("REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }

# --- Securite (derriere le proxy HTTPS de Render) ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- E-mail (mot de passe oublie, etc.) ---
# Sans EMAIL_HOST configure, on reste sur la console (rien n'est reellement
# envoye) -- des que EMAIL_HOST est fourni (ex: SMTP Gmail, Resend,
# Mailgun...), les e-mails partent reellement, sans rien changer au code.
EMAIL_HOST = env("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER or "no-reply@sporti.app")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
