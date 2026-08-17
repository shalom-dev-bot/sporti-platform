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


def _trusted_origins(host):
    # Les deux variantes (http/https) sont toujours ajoutees : sans danger
    # une fois le HTTPS actif (l'entree http:// devient simplement inutilisee
    # des que Caddy redirige tout vers https://), mais indispensable pendant
    # la periode de transition ou un VPS tourne encore en HTTP simple, avant
    # que le nom de domaine ne soit branche.
    if host.startswith("."):
        return [f"https://*{host}", f"http://*{host}"]
    return [f"https://{host}", f"http://{host}"]


CSRF_TRUSTED_ORIGINS = [origin for host in ALLOWED_HOSTS for origin in _trusted_origins(host)]
if EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS += _trusted_origins(EXTERNAL_HOSTNAME)

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

# --- Securite (derriere un proxy HTTPS) ---
# Configurable (au lieu de force a True) pour permettre de tester un VPS
# tout juste deploye en HTTP simple, avant que le nom de domaine + le
# certificat HTTPS ne soient en place -- sans ca, le cookie de session et
# le cookie CSRF ne sont jamais renvoyes par le navigateur en HTTP,
# rendant meme la connexion admin impossible ("La verification CSRF a
# echoue"). A laisser a True (defaut) des que le HTTPS est actif.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)

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
