#!/usr/bin/env bash
set -e
# Lance ce script depuis la racine de ton projet (~/sporti-platform)

mkdir -p  apps/chat apps/company apps/company/migrations apps/dashboard static/css/src static/icons static/images static/js templates/account templates/chat templates/dashboard

cat > static/js/voice-player.js << 'EOF_STATIC_JS_VOICE-PLAYER_JS'
/**
 * Lecteur de message vocal façon WhatsApp : bouton play/pause rond,
 * barre de progression cliquable, temps restant. Reutilisable partout
 * ou un audio_file doit etre affiche (accueil, chat, dashboard).
 */

const SPORTI_ICON_PLAY = '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const SPORTI_ICON_PAUSE = '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';

function sportiFormatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

function createVoicePlayer(src) {
    const wrap = document.createElement("div");
    wrap.className = "voice-player";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "voice-play-btn";
    btn.innerHTML = SPORTI_ICON_PLAY;

    const track = document.createElement("div");
    track.className = "voice-track";
    const progress = document.createElement("div");
    progress.className = "voice-progress";
    track.appendChild(progress);

    const time = document.createElement("span");
    time.className = "voice-time";
    time.textContent = "0:00";

    const audio = new Audio(src);
    audio.preload = "metadata";

    btn.addEventListener("click", () => {
        if (audio.paused) {
            document.querySelectorAll("audio").forEach((a) => {
                if (a !== audio) a.pause();
            });
            audio.play().catch(() => {});
        } else {
            audio.pause();
        }
    });

    audio.addEventListener("play", () => {
        btn.innerHTML = SPORTI_ICON_PAUSE;
    });
    audio.addEventListener("pause", () => {
        btn.innerHTML = SPORTI_ICON_PLAY;
    });
    audio.addEventListener("ended", () => {
        btn.innerHTML = SPORTI_ICON_PLAY;
        progress.style.width = "0%";
        time.textContent = sportiFormatTime(audio.duration);
    });
    audio.addEventListener("timeupdate", () => {
        if (audio.duration) {
            progress.style.width = `${(audio.currentTime / audio.duration) * 100}%`;
            time.textContent = sportiFormatTime(audio.duration - audio.currentTime);
        }
    });
    audio.addEventListener("loadedmetadata", () => {
        time.textContent = sportiFormatTime(audio.duration);
    });

    track.addEventListener("click", (event) => {
        const rect = track.getBoundingClientRect();
        const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
        if (audio.duration) audio.currentTime = ratio * audio.duration;
    });

    wrap.appendChild(btn);
    wrap.appendChild(track);
    wrap.appendChild(time);
    return wrap;
}
EOF_STATIC_JS_VOICE-PLAYER_JS

cat > static/css/src/input.css << 'EOF_STATIC_CSS_SRC_INPUT_CSS'
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply font-body antialiased;
  }
  h1, h2, h3, h4 {
    @apply font-display;
  }
}

@layer components {
  /* Coins en equerre facon HUD -- element signature de l'identite SPORTI,
     utilise sur les avatars en ligne et les elements actifs. */
  .hud-corners {
    position: relative;
  }
  .hud-corners::before,
  .hud-corners::after {
    content: "";
    position: absolute;
    width: 10px;
    height: 10px;
    border-color: theme('colors.accent.500');
    transition: all 0.2s ease;
  }
  .hud-corners::before {
    top: -3px;
    left: -3px;
    border-top: 2px solid;
    border-left: 2px solid;
  }
  .hud-corners::after {
    bottom: -3px;
    right: -3px;
    border-bottom: 2px solid;
    border-right: 2px solid;
  }

  /* Bouton principal SPORTI : coins tailles (clip-path), pas de
     bord arrondi generique -- coherent avec l'esprit angulaire du logo. */
  .btn-primary {
    @apply relative inline-flex items-center justify-center gap-2 px-6 py-3
           font-display font-semibold uppercase tracking-wide text-sm
           text-white bg-accent-600 transition-all duration-200
           hover:bg-accent-500 hover:shadow-glow
           active:scale-[0.98];
    clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
  }

  .btn-secondary {
    @apply relative inline-flex items-center justify-center gap-2 px-6 py-3
           font-display font-semibold uppercase tracking-wide text-sm
           border border-navy-800 text-navy-900 dark:text-white
           dark:border-white/20 transition-all duration-200
           hover:border-accent-500 hover:text-accent-600;
    clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
  }

  .btn-ghost {
    @apply relative inline-flex items-center justify-center gap-2 px-5 py-2.5
           font-display font-semibold uppercase tracking-wide text-xs
           text-navy-900/70 dark:text-white/70 transition-all duration-200
           hover:text-accent-600 dark:hover:text-accent-400;
  }

  .btn-icon {
    @apply relative inline-flex items-center justify-center w-11 h-11 shrink-0
           text-navy-900/60 dark:text-white/60 border border-navy-900/10 dark:border-white/10
           transition-all duration-200 hover:border-accent-500 hover:text-accent-600;
  }

  .auth-shell {
    @apply min-h-screen flex flex-col items-center justify-center px-4 py-12
           relative overflow-hidden;
  }

  .auth-shell::before {
    content: "";
    @apply absolute inset-0 pointer-events-none opacity-60 dark:opacity-100;
    background:
      radial-gradient(circle at 15% 20%, rgba(45, 108, 223, 0.16), transparent 45%),
      radial-gradient(circle at 85% 80%, rgba(59, 130, 246, 0.12), transparent 40%);
  }

  .auth-card {
    @apply relative w-full max-w-md bg-white dark:bg-navy-850
           border border-navy-900/10 dark:border-white/10 hud-corners
           px-8 py-10 sm:px-10 sm:py-12 shadow-xl shadow-navy-950/5
           dark:shadow-none;
  }

  .field-group {
    @apply mb-5 text-left;
  }

  .field-label {
    @apply block text-xs font-display font-semibold uppercase tracking-wider
           text-navy-900/60 dark:text-white/50 mb-2;
  }

  .field-input {
    @apply w-full bg-transparent border border-navy-900/15 dark:border-white/15
           text-navy-900 dark:text-white placeholder-navy-900/30 dark:placeholder-white/25
           px-4 py-3 text-sm rounded-sm transition-all duration-200
           focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500/40;
  }

  .field-input.has-error {
    @apply border-red-500/60 focus:border-red-500 focus:ring-red-500/30;
  }

  .field-error {
    @apply mt-1.5 text-xs text-red-500 dark:text-red-400;
  }

  .field-check-row {
    @apply flex items-center gap-2 text-sm text-navy-900/60 dark:text-white/50;
  }

  .form-alert {
    @apply mb-5 px-4 py-3 text-sm border border-red-500/30 bg-red-500/5
           text-red-600 dark:text-red-400;
  }

  .divider-row {
    @apply flex items-center gap-3 my-6 text-[11px] uppercase tracking-wider
           text-navy-900/35 dark:text-white/30;
  }
  .divider-row::before,
  .divider-row::after {
    content: "";
    @apply flex-1 h-px bg-navy-900/10 dark:bg-white/10;
  }

  .btn-google {
    @apply relative w-full inline-flex items-center justify-center gap-2.5 px-6 py-3
           font-body font-medium text-sm rounded-sm
           border border-navy-900/15 dark:border-white/15
           text-navy-900 dark:text-white bg-white dark:bg-navy-900
           transition-all duration-200 hover:border-accent-500 hover:shadow-glow-sm;
  }

  .chat-shell {
    @apply flex flex-col h-screen bg-surface-light dark:bg-navy-950;
  }

  .chat-header {
    @apply flex items-center gap-3 px-4 sm:px-6 py-4
           bg-white dark:bg-navy-900 border-b border-navy-900/10 dark:border-white/10
           shrink-0;
  }

  .chat-thread {
    @apply flex-1 overflow-y-auto px-3 sm:px-6 py-6 space-y-4;
  }

  .bubble {
    @apply max-w-[78%] sm:max-w-[65%] px-4 py-2.5 text-sm leading-relaxed
           break-words animate-fade-in-up;
  }

  .bubble-admin {
    @apply bubble bg-white dark:bg-navy-850 text-navy-900 dark:text-white
           border border-navy-900/5 dark:border-white/5
           rounded-r-lg rounded-tl-lg self-start;
  }

  .bubble-client {
    @apply bubble bg-accent-600 text-white rounded-l-lg rounded-tr-lg self-end;
  }

  .bubble-system {
    @apply max-w-[88%] sm:max-w-md mx-auto px-5 py-4 text-sm
           bg-accent-600/5 dark:bg-accent-500/10 border border-accent-500/20
           hud-corners text-navy-900 dark:text-white/90 animate-fade-in-up;
  }

  .chat-composer {
    @apply flex items-end gap-2 px-3 sm:px-6 py-3
           bg-white dark:bg-navy-900 border-t border-navy-900/10 dark:border-white/10
           shrink-0;
  }

  .chat-textarea {
    @apply flex-1 resize-none bg-navy-900/[0.03] dark:bg-white/5 border border-navy-900/10
           dark:border-white/10 rounded-sm px-4 py-3 text-sm text-navy-900 dark:text-white
           placeholder-navy-900/35 dark:placeholder-white/25 max-h-32
           focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500/40;
  }

  .presence-dot {
    @apply w-2.5 h-2.5 rounded-full bg-navy-900/20 dark:bg-white/20 shrink-0;
  }
  .presence-dot.online {
    @apply bg-emerald-500 shadow-[0_0_0_3px_rgba(16,185,129,0.2)];
  }

  .status-tick {
    @apply inline-flex text-[10px] ml-1 align-middle;
  }

  .typing-dots span {
    @apply inline-block w-1.5 h-1.5 rounded-full bg-navy-900/40 dark:bg-white/40 mx-0.5;
    animation: typing-bounce 1.2s infinite ease-in-out;
  }
  .typing-dots span:nth-child(2) { animation-delay: 0.15s; }
  .typing-dots span:nth-child(3) { animation-delay: 0.3s; }

  @keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
    30% { transform: translateY(-3px); opacity: 1; }
  }

  /* --- Dashboard admin --- */

  .dashboard-shell {
    @apply flex min-h-screen;
  }

  .dashboard-sidebar {
    @apply hidden lg:flex flex-col w-64 shrink-0 bg-white dark:bg-navy-900
           border-r border-navy-900/10 dark:border-white/10 px-5 py-6;
  }

  .dashboard-topbar {
    @apply flex lg:hidden items-center justify-between px-4 py-3
           bg-white dark:bg-navy-900 border-b border-navy-900/10 dark:border-white/10;
  }

  .dashboard-nav-link {
    @apply flex items-center gap-3 px-3 py-2.5 mb-1 text-sm font-medium rounded-sm
           text-navy-900/60 dark:text-white/55 transition-colors duration-150
           hover:bg-navy-900/[0.04] dark:hover:bg-white/5 hover:text-navy-900 dark:hover:text-white;
  }

  .dashboard-nav-link.active {
    @apply bg-accent-600/10 text-accent-600 dark:text-accent-400 font-semibold;
  }

  .dashboard-main {
    @apply flex-1 min-w-0 px-4 sm:px-8 py-8 max-w-6xl;
  }

  .dashboard-page-title {
    @apply font-display text-2xl font-bold mb-1;
  }

  .dashboard-page-subtitle {
    @apply text-sm text-navy-900/50 dark:text-white/45 mb-8;
  }

  .stat-card {
    @apply bg-white dark:bg-navy-900 border border-navy-900/10 dark:border-white/10
           hud-corners px-5 py-5;
  }

  .stat-card-label {
    @apply text-xs uppercase tracking-wider text-navy-900/45 dark:text-white/40 mb-2;
  }

  .stat-card-value {
    @apply font-display text-3xl font-bold;
  }

  .panel {
    @apply bg-white dark:bg-navy-900 border border-navy-900/10 dark:border-white/10 p-6;
  }

  .data-table {
    @apply w-full text-sm border-collapse;
  }

  .data-table th {
    @apply text-left text-xs uppercase tracking-wider text-navy-900/40 dark:text-white/35
           font-medium pb-3 border-b border-navy-900/10 dark:border-white/10;
  }

  .data-table td {
    @apply py-4 border-b border-navy-900/5 dark:border-white/5 align-top;
  }

  .data-table tr:hover td {
    @apply bg-navy-900/[0.015] dark:bg-white/[0.02];
  }

  .badge {
    @apply inline-flex items-center justify-center min-w-[1.4rem] h-5 px-1.5
           text-[11px] font-semibold bg-accent-600 text-white rounded-full;
  }

  .conversation-row-link {
    @apply flex items-center gap-3 font-medium text-navy-900 dark:text-white
           hover:text-accent-600 dark:hover:text-accent-400;
  }

  .avatar-circle {
    @apply w-9 h-9 shrink-0 rounded-full bg-accent-600/10 text-accent-600
           flex items-center justify-center font-display font-semibold text-sm;
  }

  .toggle-row {
    @apply flex items-center justify-between gap-4 py-3 border-b border-navy-900/5
           dark:border-white/5 last:border-0;
  }

  /* --- Lecteur vocal (style WhatsApp) --- */

  .voice-player {
    @apply flex items-center gap-3 mt-2 px-1;
  }

  .voice-play-btn {
    @apply w-9 h-9 shrink-0 rounded-full bg-accent-600 text-white
           flex items-center justify-center transition-transform duration-150
           hover:scale-105 active:scale-95;
  }

  .voice-track {
    @apply relative flex-1 h-1.5 rounded-full bg-navy-900/10 dark:bg-white/15 cursor-pointer;
  }

  .voice-progress {
    @apply absolute inset-y-0 left-0 w-0 rounded-full bg-accent-600;
  }

  .voice-time {
    @apply text-xs tabular-nums text-navy-900/45 dark:text-white/40 shrink-0 w-9 text-right;
  }
}
EOF_STATIC_CSS_SRC_INPUT_CSS

cat > tailwind.config.js << 'EOF_TAILWIND_CONFIG_JS'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/forms.py",
    "./static/js/**/*.js",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#0B0F19",
          900: "#0D1321",
          850: "#121826",
          800: "#182236",
        },
        accent: {
          400: "#5B8DEF",
          500: "#3B82F6",
          600: "#2D6CDF",
        },
        surface: {
          light: "#F7F9FC",
          "light-elevated": "#FFFFFF",
        },
      },
      fontFamily: {
        display: ["Rajdhani", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(45, 108, 223, 0.35)",
        "glow-sm": "0 0 10px rgba(45, 108, 223, 0.25)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(45, 108, 223, 0.5)" },
          "70%": { boxShadow: "0 0 0 8px rgba(45, 108, 223, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(45, 108, 223, 0)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in-up": "fade-in-up 0.3s ease-out",
      },
    },
  },
  plugins: [],
};
EOF_TAILWIND_CONFIG_JS

cat > apps/company/models.py << 'EOF_APPS_COMPANY_MODELS_PY'
"""
Modeles gerant l'identite de l'entreprise, son message d'accueil et ses
liens externes -- entierement pilotables depuis le tableau de bord admin.
"""

from django.db import models


class CompanyProfile(models.Model):
    """Profil unique de l'entreprise (singleton applicatif)."""

    name = models.CharField(max_length=150, default="SPORTI")
    logo = models.ImageField(upload_to="company/", blank=True, null=True)
    cover_image = models.ImageField(upload_to="company/", blank=True, null=True)
    description_fr = models.TextField(blank=True, verbose_name="Description (Francais)")
    description_en = models.TextField(blank=True, verbose_name="Description (Anglais)")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Profil entreprise"
        verbose_name_plural = "Profil entreprise"

    def __str__(self):
        return self.name

    def get_description(self, language_code="fr"):
        """Renvoie la description dans la langue demandee, avec repli sur
        le francais si la traduction anglaise n'est pas encore remplie."""
        if language_code == "en" and self.description_en:
            return self.description_en
        return self.description_fr


class WelcomeMessage(models.Model):
    """Message d'accueil affiche aux nouveaux visiteurs, avec audio/video
    optionnels, activables independamment."""

    text_fr = models.TextField(verbose_name="Message (Francais)")
    text_en = models.TextField(blank=True, verbose_name="Message (Anglais)")
    audio_file = models.FileField(upload_to="welcome/audio/", blank=True, null=True)
    video_file = models.FileField(upload_to="welcome/video/", blank=True, null=True)
    is_text_enabled = models.BooleanField(default=True)
    is_audio_enabled = models.BooleanField(default=True)
    is_video_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Message d'accueil"
        verbose_name_plural = "Message d'accueil"

    def __str__(self):
        return "Message d'accueil"

    def get_text(self, language_code="fr"):
        if language_code == "en" and self.text_en:
            return self.text_en
        return self.text_fr


class ExternalLink(models.Model):
    """Lien de contact externe (WhatsApp, Telegram, Facebook, Instagram...)."""

    class Platform(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        TELEGRAM = "telegram", "Telegram"
        FACEBOOK = "facebook", "Facebook Messenger"
        INSTAGRAM = "instagram", "Instagram"
        OTHER = "other", "Autre"

    platform = models.CharField(max_length=20, choices=Platform.choices)
    label = models.CharField(max_length=100, blank=True)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Lien externe"
        verbose_name_plural = "Liens externes"
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_platform_display()} -- {self.url}"
EOF_APPS_COMPANY_MODELS_PY

cat > apps/company/migrations/0003_alter_welcomemessage_is_audio_enabled_and_more.py << 'EOF_APPS_COMPANY_MIGRATIONS_0003_ALTER_WELCOMEMESSAGE_IS_AUDIO_ENABLED_AND_MORE_PY'
# Generated by Django 5.1.4 on 2026-07-24 18:15

from django.db import migrations, models


def enable_existing_media(apps, schema_editor):
    """Les messages d'accueil deja crees avant ce correctif peuvent avoir
    un fichier audio/video televerse mais jamais active -- on les
    reactive ici pour ne pas laisser un vocal deja en place invisible."""
    WelcomeMessage = apps.get_model("company", "WelcomeMessage")
    WelcomeMessage.objects.filter(audio_file__gt="").update(is_audio_enabled=True)
    WelcomeMessage.objects.filter(video_file__gt="").update(is_video_enabled=True)


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0002_remove_companyprofile_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='welcomemessage',
            name='is_audio_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='welcomemessage',
            name='is_video_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(enable_existing_media, migrations.RunPython.noop),
    ]
EOF_APPS_COMPANY_MIGRATIONS_0003_ALTER_WELCOMEMESSAGE_IS_AUDIO_ENABLED_AND_MORE_PY

cat > apps/dashboard/views.py << 'EOF_APPS_DASHBOARD_VIEWS_PY'
"""
Espace de gestion de l'entreprise -- interface personnalisee SPORTI,
distincte de l'admin Django par defaut (reserve aux developpeurs sur /admin/).
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.chat.models import Conversation, Message
from apps.company.forms import CompanyProfileForm, ExternalLinkForm, WelcomeMessageForm
from apps.company.models import CompanyProfile, ExternalLink, WelcomeMessage

CACHE_KEY_DASHBOARD_STATS = "dashboard:stats"
CACHE_TTL_DASHBOARD_STATS = 60  # secondes : assez court pour rester a jour,
# assez long pour eviter de recalculer a chaque chargement de page.


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/gestion/"


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def dashboard_home(request):
    """Vue d'ensemble : statistiques cles et evolution du nombre de clients.
    Mise en cache Redis : les statistiques ne sont recalculees qu'une fois
    par minute maximum, meme si plusieurs admins consultent la page en
    meme temps."""
    context = cache.get(CACHE_KEY_DASHBOARD_STATS)
    if context is not None:
        return render(request, "dashboard/home.html", context)

    total_clients = User.objects.filter(is_staff=False).count()
    total_conversations = Conversation.objects.count()

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = Message.objects.filter(created_at__gte=today_start).count()

    unread_conversations = (
        Conversation.objects.filter(messages__sender__is_staff=False)
        .exclude(messages__status=Message.Status.READ)
        .distinct()
        .count()
    )

    twelve_months_ago = timezone.now() - timedelta(days=365)
    growth_qs = (
        User.objects.filter(is_staff=False, date_joined__gte=twelve_months_ago)
        .annotate(month=TruncMonth("date_joined"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    growth_labels = [row["month"].strftime("%b %Y") for row in growth_qs]
    growth_values = [row["count"] for row in growth_qs]

    context = {
        "total_clients": total_clients,
        "total_conversations": total_conversations,
        "messages_today": messages_today,
        "unread_conversations": unread_conversations,
        "growth_labels": growth_labels,
        "growth_values": growth_values,
    }
    cache.set(CACHE_KEY_DASHBOARD_STATS, context, CACHE_TTL_DASHBOARD_STATS)
    return render(request, "dashboard/home.html", context)


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversations_list(request):
    """Liste complete et organisee des conversations, triee par activite
    recente. 3 requetes au total, peu importe le nombre de conversations."""
    conversations = (
        Conversation.objects.select_related("client")
        .prefetch_related("messages")
        .order_by("-updated_at")
    )

    unread_rows = (
        Message.objects.filter(sender__is_staff=False)
        .exclude(status=Message.Status.READ)
        .values("conversation_id")
        .annotate(count=Count("id"))
    )
    unread_by_conversation = {row["conversation_id"]: row["count"] for row in unread_rows}

    conversations_data = []
    for conversation in conversations:
        sorted_messages = sorted(
            conversation.messages.all(), key=lambda m: m.created_at, reverse=True
        )
        last_message = sorted_messages[0] if sorted_messages else None

        conversations_data.append(
            {
                "conversation": conversation,
                "last_message": last_message,
                "unread_count": unread_by_conversation.get(conversation.id, 0),
            }
        )

    return render(
        request, "dashboard/conversations_list.html", {"conversations_data": conversations_data}
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def change_password(request):
    """Permet a l'administrateur de changer son mot de passe depuis
    l'espace de gestion, sans devoir passer par /admin/."""
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe modifie avec succes.")
            return redirect("dashboard:change_password")
    else:
        form = PasswordChangeForm(user=request.user)

    for field in form.fields.values():
        field.widget.attrs.update({"class": "field-input"})

    return render(request, "dashboard/change_password.html", {"form": form})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def conversation_detail(request, conversation_id):
    """Vue d'une conversation precise : historique + reponse en temps reel."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.select_related("sender").order_by("created_at")
    return render(
        request,
        "dashboard/conversation.html",
        {"conversation": conversation, "messages": messages},
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def company_settings(request):
    """Permet a l'admin de modifier l'identite entreprise et le message
    d'accueil (texte / audio / video, chacun activable independamment)."""
    profile, _ = CompanyProfile.objects.get_or_create(pk=1)
    welcome, _ = WelcomeMessage.objects.get_or_create(pk=1)

    if request.method == "POST" and request.POST.get("form_type") == "profile":
        profile_form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        welcome_form = WelcomeMessageForm(instance=welcome)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profil de l'entreprise mis a jour.")
            return redirect("dashboard:company_settings")
    elif request.method == "POST" and request.POST.get("form_type") == "welcome":
        welcome_form = WelcomeMessageForm(request.POST, request.FILES, instance=welcome)
        profile_form = CompanyProfileForm(instance=profile)
        if welcome_form.is_valid():
            welcome_obj = welcome_form.save(commit=False)
            # Un fichier vient d'etre televerse -> on l'active automatiquement,
            # pour eviter qu'il reste invisible faute d'avoir coche la case.
            if request.FILES.get("audio_file"):
                welcome_obj.is_audio_enabled = True
            if request.FILES.get("video_file"):
                welcome_obj.is_video_enabled = True
            welcome_obj.save()
            messages.success(request, "Message d'accueil mis a jour.")
            return redirect("dashboard:company_settings")
    else:
        profile_form = CompanyProfileForm(instance=profile)
        welcome_form = WelcomeMessageForm(instance=welcome)

    return render(
        request,
        "dashboard/company_settings.html",
        {"profile_form": profile_form, "welcome_form": welcome_form, "profile": profile},
    )


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def links_list(request):
    """CRUD des liens externes (WhatsApp, Telegram, etc.) affiches sur la
    page d'accueil publique."""
    links = ExternalLink.objects.all().order_by("order", "id")
    return render(request, "dashboard/links_list.html", {"links": links})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_create(request):
    if request.method == "POST":
        form = ExternalLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lien ajoute.")
            return redirect("dashboard:links_list")
    else:
        form = ExternalLinkForm()
    return render(request, "dashboard/link_form.html", {"form": form, "is_edit": False})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_edit(request, link_id):
    link = get_object_or_404(ExternalLink, id=link_id)
    if request.method == "POST":
        form = ExternalLinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, "Lien mis a jour.")
            return redirect("dashboard:links_list")
    else:
        form = ExternalLinkForm(instance=link)
    return render(request, "dashboard/link_form.html", {"form": form, "is_edit": True, "link": link})


@login_required(login_url="/gestion/connexion/")
@user_passes_test(_is_staff, login_url="/gestion/connexion/")
def link_delete(request, link_id):
    link = get_object_or_404(ExternalLink, id=link_id)
    if request.method == "POST":
        link.delete()
        messages.success(request, "Lien supprime.")
    return redirect("dashboard:links_list")
EOF_APPS_DASHBOARD_VIEWS_PY

cat > apps/chat/serializers.py << 'EOF_APPS_CHAT_SERIALIZERS_PY'
"""
Serializers DRF pour l'historique du chat.
"""

from rest_framework import serializers

from .models import Attachment, Conversation, Message, MessageReaction


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "file", "file_name", "file_type", "file_size", "uploaded_at"]


class MessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReaction
        fields = ["id", "user", "emoji", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.__str__", read_only=True)
    is_staff = serializers.BooleanField(source="sender.is_staff", read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_name",
            "is_staff",
            "content",
            "status",
            "created_at",
            "attachments",
            "reactions",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.__str__", read_only=True)
    client_is_online = serializers.BooleanField(source="client.is_online", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "client",
            "client_name",
            "client_is_online",
            "created_at",
            "updated_at",
            "is_archived",
            "last_message",
            "unread_count",
        ]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last is None:
            return None
        return {"content": last.content, "created_at": last.created_at, "status": last.status}

    def get_unread_count(self, obj):
        return obj.messages.exclude(status=Message.Status.READ).count()
EOF_APPS_CHAT_SERIALIZERS_PY

cat > templates/account/login.html << 'EOF_TEMPLATES_ACCOUNT_LOGIN_HTML'
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block title %}{% trans "Connexion" %} — SPORTI{% endblock %}

{% block content %}
<div class="auth-shell">

    <form action="{% url 'set_language' %}" method="post" class="absolute top-5 left-5 z-10">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.path }}">
        <select name="language" onchange="this.form.submit()"
                class="text-xs bg-transparent border border-navy-900/15 dark:border-white/15 px-2 py-1.5 text-navy-900/60 dark:text-white/50">
            {% get_current_language as CURRENT_LANGUAGE %}
            {% get_available_languages as LANGUAGES %}
            {% for lang_code, lang_name in LANGUAGES %}
                <option value="{{ lang_code }}" {% if lang_code == CURRENT_LANGUAGE %}selected{% endif %}>{{ lang_name }}</option>
            {% endfor %}
        </select>
    </form>

    <div class="relative w-full max-w-md text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 hud-corners mb-4 overflow-hidden bg-navy-950">
            <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
        </div>
        <h1 class="font-display text-2xl font-bold tracking-wide">SPORTI</h1>
        <p class="text-[11px] uppercase tracking-[0.2em] text-navy-900/40 dark:text-white/35 mt-1">
            Vision · Speed · Strength
        </p>
    </div>

    <div class="auth-card">
        <h2 class="font-display text-xl font-semibold text-center mb-1">{% trans "Content de vous revoir" %}</h2>
        <p class="text-sm text-center text-navy-900/50 dark:text-white/45 mb-7">
            {% trans "Connectez-vous pour retrouver votre conversation." %}
        </p>

        {% if form.non_field_errors %}
            <div class="form-alert">
                {% for error in form.non_field_errors %}{{ error }}{% endfor %}
            </div>
        {% endif %}

        <a href="{% url 'google_login' %}" class="btn-google">
            <svg class="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.47c-.28 1.5-1.13 2.78-2.4 3.63v3.01h3.89c2.28-2.1 3.56-5.19 3.56-8.83z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.95-2.9l-3.89-3.01c-1.08.72-2.46 1.15-4.06 1.15-3.12 0-5.77-2.11-6.72-4.94H1.27v3.1C3.25 21.3 7.31 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.3c-.24-.72-.38-1.49-.38-2.3s.14-1.58.38-2.3v-3.1H1.27A11.96 11.96 0 000 12c0 1.94.46 3.77 1.27 5.4l4.01-3.1z"/>
                <path fill="#EA4335" d="M12 4.77c1.76 0 3.35.6 4.6 1.8l3.44-3.44C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.6l4.01 3.1C6.23 6.88 8.88 4.77 12 4.77z"/>
            </svg>
            {% trans "Continuer avec Google" %}
        </a>

        <div class="divider-row">{% trans "ou par e-mail" %}</div>

        <form method="post" action="{% url 'account_login' %}" novalidate>
            {% csrf_token %}
            {% for field in form %}
                {% if field.name != "remember" %}
                <div class="field-group">
                    <label for="{{ field.id_for_label }}" class="field-label">{{ field.label }}</label>
                    {{ field|safe }}
                    {% for error in field.errors %}
                        <p class="field-error">{{ error }}</p>
                    {% endfor %}
                </div>
                {% endif %}
            {% endfor %}

            <div class="flex items-center justify-between mb-6">
                {% for field in form %}
                    {% if field.name == "remember" %}
                    <label class="field-check-row">
                        {{ field }} {% trans "Se souvenir de moi" %}
                    </label>
                    {% endif %}
                {% endfor %}
                <a href="{% url 'account_reset_password' %}" class="text-xs text-accent-600 hover:text-accent-500">
                    {% trans "Mot de passe oublié ?" %}
                </a>
            </div>

            <button type="submit" class="btn-primary w-full">{% trans "Se connecter" %}</button>
        </form>

        <p class="text-center text-sm text-navy-900/50 dark:text-white/45 mt-7">
            {% trans "Pas encore de compte ?" %}
            <a href="{% url 'account_signup' %}" class="text-accent-600 hover:text-accent-500 font-medium">{% trans "Inscrivez-vous" %}</a>
        </p>
    </div>
</div>
{% endblock %}
EOF_TEMPLATES_ACCOUNT_LOGIN_HTML

cat > templates/account/signup.html << 'EOF_TEMPLATES_ACCOUNT_SIGNUP_HTML'
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block title %}{% trans "Créer un compte" %} — SPORTI{% endblock %}

{% block content %}
<div class="auth-shell">

    <form action="{% url 'set_language' %}" method="post" class="absolute top-5 left-5 z-10">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.path }}">
        <select name="language" onchange="this.form.submit()"
                class="text-xs bg-transparent border border-navy-900/15 dark:border-white/15 px-2 py-1.5 text-navy-900/60 dark:text-white/50">
            {% get_current_language as CURRENT_LANGUAGE %}
            {% get_available_languages as LANGUAGES %}
            {% for lang_code, lang_name in LANGUAGES %}
                <option value="{{ lang_code }}" {% if lang_code == CURRENT_LANGUAGE %}selected{% endif %}>{{ lang_name }}</option>
            {% endfor %}
        </select>
    </form>

    <div class="relative w-full max-w-md text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 hud-corners mb-4 overflow-hidden bg-navy-950">
            <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
        </div>
        <h1 class="font-display text-2xl font-bold tracking-wide">SPORTI</h1>
        <p class="text-[11px] uppercase tracking-[0.2em] text-navy-900/40 dark:text-white/35 mt-1">
            Vision · Speed · Strength
        </p>
    </div>

    <div class="auth-card">
        <h2 class="font-display text-xl font-semibold text-center mb-1">{% trans "Créer votre compte" %}</h2>
        <p class="text-sm text-center text-navy-900/50 dark:text-white/45 mb-7">
            {% trans "Rejoignez SPORTI pour discuter directement avec nous." %}
        </p>

        {% if form.non_field_errors %}
            <div class="form-alert">
                {% for error in form.non_field_errors %}{{ error }}{% endfor %}
            </div>
        {% endif %}

        <a href="{% url 'google_login' %}" class="btn-google">
            <svg class="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.47c-.28 1.5-1.13 2.78-2.4 3.63v3.01h3.89c2.28-2.1 3.56-5.19 3.56-8.83z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.95-2.9l-3.89-3.01c-1.08.72-2.46 1.15-4.06 1.15-3.12 0-5.77-2.11-6.72-4.94H1.27v3.1C3.25 21.3 7.31 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.3c-.24-.72-.38-1.49-.38-2.3s.14-1.58.38-2.3v-3.1H1.27A11.96 11.96 0 000 12c0 1.94.46 3.77 1.27 5.4l4.01-3.1z"/>
                <path fill="#EA4335" d="M12 4.77c1.76 0 3.35.6 4.6 1.8l3.44-3.44C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.6l4.01 3.1C6.23 6.88 8.88 4.77 12 4.77z"/>
            </svg>
            {% trans "Continuer avec Google" %}
        </a>
        <p class="text-center text-[11px] text-navy-900/35 dark:text-white/30 mt-2">
            {% trans "Nom et photo récupérés automatiquement, sans mot de passe." %}
        </p>

        <div class="divider-row">{% trans "ou avec un e-mail" %}</div>

        <form method="post" action="{% url 'account_signup' %}" novalidate>
            {% csrf_token %}
            {% for field in form %}
                <div class="field-group">
                    <label for="{{ field.id_for_label }}" class="field-label">{{ field.label }}</label>
                    {{ field }}
                    {% if field.help_text %}
                        <p class="mt-1 text-xs text-navy-900/40 dark:text-white/35">{{ field.help_text }}</p>
                    {% endif %}
                    {% for error in field.errors %}
                        <p class="field-error">{{ error }}</p>
                    {% endfor %}
                </div>
            {% endfor %}

            <button type="submit" class="btn-primary w-full">{% trans "Créer mon compte" %}</button>
        </form>

        <p class="text-center text-sm text-navy-900/50 dark:text-white/45 mt-7">
            {% trans "Déjà un compte ?" %}
            <a href="{% url 'account_login' %}" class="text-accent-600 hover:text-accent-500 font-medium">{% trans "Connectez-vous" %}</a>
        </p>
    </div>
</div>
{% endblock %}
EOF_TEMPLATES_ACCOUNT_SIGNUP_HTML

cat > templates/dashboard/login.html << 'EOF_TEMPLATES_DASHBOARD_LOGIN_HTML'
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block title %}{% trans "Espace de gestion" %} — SPORTI{% endblock %}

{% block content %}
<div class="auth-shell">
    <div class="relative w-full max-w-md text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 hud-corners mb-4 overflow-hidden bg-navy-950">
            <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
        </div>
        <h1 class="font-display text-2xl font-bold tracking-wide">SPORTI</h1>
        <p class="text-[11px] uppercase tracking-[0.2em] text-navy-900/40 dark:text-white/35 mt-1">
            {% trans "Espace de gestion" %}
        </p>
    </div>

    <div class="auth-card">
        {% if form.errors %}
            <div class="form-alert">{% trans "Identifiants incorrects. Réessayez." %}</div>
        {% endif %}

        <form method="post">
            {% csrf_token %}
            <div class="field-group">
                <label for="id_username" class="field-label">{% trans "Nom d'utilisateur" %}</label>
                <input type="text" name="username" id="id_username" class="field-input" required autofocus>
            </div>
            <div class="field-group">
                <label for="id_password" class="field-label">{% trans "Mot de passe" %}</label>
                <input type="password" name="password" id="id_password" class="field-input" required>
            </div>
            <button type="submit" class="btn-primary w-full">{% trans "Se connecter" %}</button>
        </form>
    </div>
</div>
{% endblock %}
EOF_TEMPLATES_DASHBOARD_LOGIN_HTML

cat > templates/dashboard/_base.html << 'EOF_TEMPLATES_DASHBOARD__BASE_HTML'
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block content %}
<div class="dashboard-shell">
    <aside class="dashboard-sidebar">
        <div class="flex items-center gap-2 mb-8 px-1">
            <div class="w-8 h-8 hud-corners flex items-center justify-center bg-navy-950 overflow-hidden">
                <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
            </div>
            <span class="font-display font-bold tracking-wide">SPORTI</span>
        </div>

        <nav class="flex-1">
            <a href="{% url 'dashboard:home' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'home' %}active{% endif %}">
                {% trans "Vue d'ensemble" %}
            </a>
            <a href="{% url 'dashboard:conversations_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'conversations_list' or request.resolver_match.url_name == 'conversation_detail' %}active{% endif %}">
                {% trans "Conversations" %}
            </a>
            <a href="{% url 'dashboard:company_settings' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'company_settings' %}active{% endif %}">
                {% trans "Accueil & Profil" %}
            </a>
            <a href="{% url 'dashboard:links_list' %}" class="dashboard-nav-link {% if request.resolver_match.url_name in 'links_list link_create link_edit' %}active{% endif %}">
                {% trans "Liens externes" %}
            </a>
            <a href="{% url 'dashboard:change_password' %}" class="dashboard-nav-link {% if request.resolver_match.url_name == 'change_password' %}active{% endif %}">
                {% trans "Mot de passe" %}
            </a>
        </nav>

        <form method="post" action="{% url 'dashboard:logout' %}">
            {% csrf_token %}
            <button type="submit" class="dashboard-nav-link w-full text-left">
                {% trans "Déconnexion" %}
            </button>
        </form>
    </aside>

    <div class="flex-1 min-w-0 flex flex-col">
        <div class="dashboard-topbar">
            <span class="font-display font-bold">SPORTI</span>
            <div class="flex items-center gap-3 text-xs">
                <a href="{% url 'dashboard:home' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Vue" %}</a>
                <a href="{% url 'dashboard:conversations_list' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Chat" %}</a>
                <a href="{% url 'dashboard:company_settings' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Accueil" %}</a>
                <a href="{% url 'dashboard:links_list' %}" class="text-navy-900/60 dark:text-white/50">{% trans "Liens" %}</a>
            </div>
        </div>

        <main class="dashboard-main">
            {% if messages %}
                <div class="mb-6 space-y-2">
                    {% for message in messages %}
                        <div class="px-4 py-3 text-sm border border-accent-500/25 bg-accent-500/5 text-accent-700 dark:text-accent-300">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
            {% block dashboard_content %}{% endblock %}
        </main>
    </div>
</div>
{% endblock %}
EOF_TEMPLATES_DASHBOARD__BASE_HTML

cat > templates/chat/home.html << 'EOF_TEMPLATES_CHAT_HOME_HTML'
{% extends "base.html" %}
{% load i18n %}
{% load static %}

{% block title %}SPORTI{% endblock %}

{% block content %}
{% if user.is_authenticated %}

<div class="chat-shell">
    <header class="chat-header">
        <div id="company-logo-wrap" class="w-10 h-10 shrink-0 hud-corners bg-navy-950 flex items-center justify-center overflow-hidden">
            <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
        </div>
        <div class="min-w-0 flex-1">
            <p id="company-name" class="font-display font-semibold text-sm truncate">SPORTI</p>
            <p class="flex items-center gap-1.5 text-xs text-navy-900/45 dark:text-white/40">
                <span id="admin-presence-dot" class="presence-dot"></span>
                <span id="admin-presence-label">{% trans "Hors ligne" %}</span>
            </p>
        </div>
        <form method="post" action="{% url 'account_logout' %}">
            {% csrf_token %}
            <button type="submit" class="btn-ghost">{% trans "Déconnexion" %}</button>
        </form>
    </header>

    <div id="chat-thread" class="chat-thread flex flex-col"></div>

    <form id="composer-form" class="chat-composer">
        <input type="file" id="attachment-input" class="hidden" accept="image/*,.pdf,.doc,.docx">
        <button type="button" id="attach-btn" class="btn-icon" aria-label="{% trans 'Joindre un fichier' %}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21.44 11.05l-9.19 9.19a5 5 0 01-7.07-7.07l9.19-9.19a3.5 3.5 0 014.95 4.95l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
            </svg>
        </button>
        <textarea id="message-input" rows="1" class="chat-textarea"
                  placeholder="{% trans 'Écrivez votre message…' %}"></textarea>
        <button type="submit" class="btn-icon !text-accent-600 !border-accent-500" aria-label="{% trans 'Envoyer' %}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12l15-8-5.5 8 5.5 8-15-8z"/>
            </svg>
        </button>
    </form>
</div>

{% else %}

<div class="max-w-2xl mx-auto px-4 py-14 animate-fade-in-up">

    <form action="{% url 'set_language' %}" method="post" class="flex justify-end mb-6">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.path }}">
        <select name="language" onchange="this.form.submit()"
                class="text-sm bg-transparent border border-navy-900/20 dark:border-white/20 px-2 py-1">
            {% get_current_language as CURRENT_LANGUAGE %}
            {% get_available_languages as LANGUAGES %}
            {% for lang_code, lang_name in LANGUAGES %}
                <option value="{{ lang_code }}" {% if lang_code == CURRENT_LANGUAGE %}selected{% endif %}>
                    {{ lang_name }}
                </option>
            {% endfor %}
        </select>
    </form>

    <div id="company-config" class="text-center">
        <div id="company-logo-wrap" class="inline-flex items-center justify-center w-20 h-20 hud-corners mb-5 bg-navy-950 overflow-hidden">
            <img src="{% static 'images/sporti-logo.png' %}" alt="SPORTI" class="w-full h-full object-cover">
        </div>
        <h1 id="company-name" class="font-display text-3xl font-bold"></h1>
        <p id="company-description" class="mt-3 text-navy-900/60 dark:text-white/60 max-w-lg mx-auto"></p>
    </div>

    <div id="welcome-message" class="mt-8 hidden bubble-system"></div>

    <div id="external-links" class="mt-6 flex flex-wrap justify-center gap-3"></div>

    <div class="mt-10 flex justify-center">
        <div class="flex flex-col sm:flex-row gap-3">
            <a href="{% url 'account_login' %}" class="btn-primary">{% trans "Se connecter" %}</a>
            <a href="{% url 'account_signup' %}" class="btn-secondary">{% trans "Créer un compte" %}</a>
        </div>
    </div>

</div>

{% endif %}
{% endblock %}

{% block extra_scripts %}
<script src="{% static 'js/voice-player.js' %}"></script>
<script>
    const CURRENT_USER_ID = {{ user.id|default:"null" }};
    const IS_AUTHENTICATED = {{ user.is_authenticated|yesno:"true,false" }};

    function getCsrfToken() {
        return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";
    }

    fetch("{% url 'company:api_config' %}")
        .then((res) => res.json())
        .then((data) => {
            const profile = data.profile;
            const welcome = data.welcome_message;
            const links = data.external_links || [];

            const nameEl = document.getElementById("company-name");
            if (nameEl) nameEl.textContent = profile.name;

            const descEl = document.getElementById("company-description");
            if (descEl) descEl.textContent = profile.description || "";

            const logoWrap = document.getElementById("company-logo-wrap");
            if (profile.logo && logoWrap) {
                logoWrap.innerHTML = "";
                const img = document.createElement("img");
                img.src = profile.logo;
                img.alt = profile.name;
                img.className = "w-full h-full object-cover";
                logoWrap.appendChild(img);
            }

            if (!IS_AUTHENTICATED) {
                const welcomeBox = document.getElementById("welcome-message");
                if (welcome && welcomeBox) {
                    let hasContent = false;
                    welcomeBox.innerHTML = "";

                    if (welcome.is_text_enabled && welcome.text) {
                        const p = document.createElement("p");
                        p.textContent = welcome.text;
                        welcomeBox.appendChild(p);
                        hasContent = true;
                    }
                    if (welcome.is_audio_enabled && welcome.audio_file) {
                        welcomeBox.appendChild(createVoicePlayer(welcome.audio_file));
                        hasContent = true;
                    }
                    if (welcome.is_video_enabled && welcome.video_file) {
                        const video = document.createElement("video");
                        video.controls = true;
                        video.className = "mt-3 w-full";
                        video.src = welcome.video_file;
                        welcomeBox.appendChild(video);
                        hasContent = true;
                    }
                    if (hasContent) {
                        welcomeBox.classList.remove("hidden");
                    }
                }

                const linksBox = document.getElementById("external-links");
                if (linksBox) {
                    links.forEach((link) => {
                        const a = document.createElement("a");
                        a.href = link.url;
                        a.target = "_blank";
                        a.rel = "noopener noreferrer";
                        a.className = "btn-secondary text-xs";
                        a.textContent = link.platform_label + (link.label ? ` — ${link.label}` : "");
                        linksBox.appendChild(a);
                    });
                }
            } else {
                window.__sportiWelcome = welcome;
            }
        })
        .catch((err) => console.error("Erreur chargement config entreprise :", err));

    {% if user.is_authenticated %}
    // --- Chat en temps reel ---
    (function () {
        const thread = document.getElementById("chat-thread");
        const form = document.getElementById("composer-form");
        const input = document.getElementById("message-input");
        const attachBtn = document.getElementById("attach-btn");
        const attachmentInput = document.getElementById("attachment-input");
        const presenceDot = document.getElementById("admin-presence-dot");
        const presenceLabel = document.getElementById("admin-presence-label");

        let conversationId = null;
        let typingTimeout = null;
        let typingBubble = null;
        let socket = null;

        function ticksFor(status) {
            if (status === "read") {
                return '<span class="status-tick text-white/90">✓✓</span>';
            }
            if (status === "delivered") {
                return '<span class="status-tick text-white/60">✓✓</span>';
            }
            return '<span class="status-tick text-white/60">✓</span>';
        }

        function renderWelcomeBubble() {
            const welcome = window.__sportiWelcome;
            if (!welcome) return;

            const div = document.createElement("div");
            div.className = "bubble-system";
            let hasContent = false;

            if (welcome.is_text_enabled && welcome.text) {
                const p = document.createElement("p");
                p.textContent = welcome.text;
                div.appendChild(p);
                hasContent = true;
            }
            if (welcome.is_audio_enabled && welcome.audio_file) {
                div.appendChild(createVoicePlayer(welcome.audio_file));
                hasContent = true;
            }
            if (welcome.is_video_enabled && welcome.video_file) {
                const video = document.createElement("video");
                video.controls = true;
                video.className = "mt-3 w-full";
                video.src = welcome.video_file;
                div.appendChild(video);
                hasContent = true;
            }
            if (!hasContent) return;
            thread.appendChild(div);
        }

        function renderMessage(msg) {
            const isMine = msg.sender_id === CURRENT_USER_ID || (msg.sender && msg.sender === CURRENT_USER_ID);
            const div = document.createElement("div");
            div.className = isMine ? "bubble-client" : "bubble-admin";
            div.dataset.messageId = msg.id;

            let inner = "";
            if (msg.content) {
                inner += `<span>${escapeHtml(msg.content)}</span>`;
            }
            if (msg.attachment) {
                const att = msg.attachment;
                if (att.file_type && att.file_type.startsWith("image/")) {
                    inner += `<img src="${att.file_url}" class="mt-2 max-h-56 rounded-sm" alt="${att.file_name}">`;
                } else {
                    inner += `<a href="${att.file_url}" target="_blank" class="underline text-xs">${att.file_name}</a>`;
                }
            } else if (msg.attachments && msg.attachments.length) {
                msg.attachments.forEach((att) => {
                    if (att.file_type && att.file_type.startsWith("image/")) {
                        inner += `<img src="${att.file}" class="mt-2 max-h-56 rounded-sm" alt="${att.file_name}">`;
                    } else {
                        inner += `<a href="${att.file}" target="_blank" class="underline text-xs">${att.file_name}</a>`;
                    }
                });
            }
            if (isMine) {
                inner += ticksFor(msg.status);
            }
            div.innerHTML = inner;
            thread.appendChild(div);
        }

        function escapeHtml(str) {
            const div = document.createElement("div");
            div.textContent = str;
            return div.innerHTML;
        }

        function scrollToBottom() {
            thread.scrollTop = thread.scrollHeight;
        }

        function updateTicks(messageIds, status) {
            messageIds.forEach((id) => {
                const bubble = thread.querySelector(`[data-message-id="${id}"]`);
                if (bubble && bubble.classList.contains("bubble-client")) {
                    const tick = bubble.querySelector(".status-tick");
                    if (tick) tick.outerHTML = ticksFor(status);
                }
            });
        }

        function setPresence(isOnline) {
            if (isOnline) {
                presenceDot.classList.add("online");
                presenceLabel.textContent = "{% trans 'En ligne' %}";
            } else {
                presenceDot.classList.remove("online");
                presenceLabel.textContent = "{% trans 'Hors ligne' %}";
            }
        }

        function showTyping() {
            if (typingBubble) return;
            typingBubble = document.createElement("div");
            typingBubble.className = "bubble-admin typing-dots";
            typingBubble.innerHTML = "<span></span><span></span><span></span>";
            thread.appendChild(typingBubble);
            scrollToBottom();
        }

        function hideTyping() {
            if (typingBubble) {
                typingBubble.remove();
                typingBubble = null;
            }
        }

        function connectSocket() {
            const protocol = window.location.protocol === "https:" ? "wss" : "ws";
            socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/`);

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === "presence") {
                    if (data.user_id !== CURRENT_USER_ID) setPresence(data.is_online);
                    return;
                }
                if (data.type === "read_receipt") {
                    updateTicks(data.message_ids, "read");
                    return;
                }
                if (data.type === "typing") {
                    if (data.user_id === CURRENT_USER_ID) return;
                    if (data.is_typing) showTyping();
                    else hideTyping();
                    return;
                }

                hideTyping();
                if (!thread.querySelector(`[data-message-id="${data.id}"]`)) {
                    renderMessage(data);
                    scrollToBottom();
                }
            };

            socket.onclose = () => {
                setTimeout(connectSocket, 2000);
            };
        }

        function loadHistory() {
            fetch("{% url 'chat:api_my_conversation' %}")
                .then((res) => res.json())
                .then((data) => {
                    conversationId = data.conversation_id;
                    renderWelcomeBubble();
                    data.messages.forEach(renderMessage);
                    scrollToBottom();
                    connectSocket();
                })
                .catch((err) => console.error("Erreur chargement conversation :", err));
        }

        form.addEventListener("submit", (event) => {
            event.preventDefault();
            const text = input.value.trim();
            if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
            socket.send(JSON.stringify({ message: text }));
            input.value = "";
            input.style.height = "auto";
            sendTyping(false);
        });

        input.addEventListener("input", () => {
            input.style.height = "auto";
            input.style.height = Math.min(input.scrollHeight, 128) + "px";
            sendTyping(true);
        });

        function sendTyping(isTyping) {
            if (!socket || socket.readyState !== WebSocket.OPEN) return;
            socket.send(JSON.stringify({ type: "typing", is_typing: isTyping }));
            if (isTyping) {
                clearTimeout(typingTimeout);
                typingTimeout = setTimeout(() => sendTyping(false), 2500);
            } else {
                clearTimeout(typingTimeout);
            }
        }

        const ATTACHMENT_URL_TEMPLATE = "{% url 'chat:api_attachment_upload' conversation_id=999999 %}";

        attachBtn.addEventListener("click", () => {
            if (!conversationId) {
                alert("{% trans 'Un instant, la conversation se charge encore…' %}");
                return;
            }
            attachmentInput.click();
        });

        attachmentInput.addEventListener("change", () => {
            const file = attachmentInput.files[0];
            attachmentInput.value = "";
            if (!file) return;
            if (!conversationId) {
                alert("{% trans 'Un instant, la conversation se charge encore…' %}");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);
            const uploadUrl = ATTACHMENT_URL_TEMPLATE.replace("999999", conversationId);

            fetch(uploadUrl, {
                method: "POST",
                headers: { "X-CSRFToken": getCsrfToken() },
                body: formData,
            })
                .then(async (res) => {
                    const data = await res.json().catch(() => ({}));
                    if (!res.ok) {
                        alert(data.detail || "{% trans "Échec de l'envoi du fichier." %}");
                        return;
                    }
                    if (!thread.querySelector(`[data-message-id="${data.id}"]`)) {
                        hideTyping();
                        renderMessage(data);
                        scrollToBottom();
                    }
                })
                .catch((err) => {
                    console.error("Erreur envoi piece jointe :", err);
                    alert("{% trans "Échec de l'envoi du fichier, vérifiez votre connexion." %}");
                });
        });

        loadHistory();
    })();
    {% endif %}

    {% if user.is_authenticated %}
    const VAPID_PUBLIC_KEY = "BADV9JSLdUH2Le2D-bXyMeZbedSC8cfyiXc7aH4ieUmJne8aMU1xptDYjgmFqJ4Tb9ZY7rCzUAv1aUKvYCUcICo";

    function urlBase64ToUint8Array(base64String) {
        const padding = "=".repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
        const rawData = window.atob(base64);
        return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
    }

    navigator.serviceWorker.ready.then(async (registration) => {
        if (Notification.permission === "denied") return;
        const permission = await Notification.requestPermission();
        if (permission !== "granted") return;

        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
        });

        await fetch("{% url 'accounts:push_subscribe' %}", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify(subscription),
        });
    });
    {% endif %}
</script>
{% endblock %}
EOF_TEMPLATES_CHAT_HOME_HTML

cat > templates/dashboard/company_settings.html << 'EOF_TEMPLATES_DASHBOARD_COMPANY_SETTINGS_HTML'
{% extends "dashboard/_base.html" %}
{% load i18n %}

{% block title %}{% trans "Accueil & Profil" %} — SPORTI{% endblock %}

{% block dashboard_content %}
<h1 class="dashboard-page-title">{% trans "Accueil & Profil" %}</h1>
<p class="dashboard-page-subtitle">
    {% trans "Ce que voit un visiteur en arrivant sur la plateforme, avant de se connecter." %}
</p>

<div class="grid lg:grid-cols-2 gap-6">

    <div class="panel">
        <h2 class="font-display font-semibold mb-1">{% trans "Profil de l'entreprise" %}</h2>
        <p class="text-xs text-navy-900/45 dark:text-white/40 mb-5">
            {% trans "Logo, nom et description affichés en haut de la page d'accueil." %}
        </p>
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            <input type="hidden" name="form_type" value="profile">
            {% for field in profile_form %}
            <div class="field-group">
                <label for="{{ field.id_for_label }}" class="field-label">{{ field.label }}</label>
                {% if field.name == "logo" or field.name == "cover_image" %}
                    {% if field.value %}
                        <img src="{{ field.value.url }}" alt="" class="w-16 h-16 object-cover mb-2 hud-corners">
                    {% endif %}
                {% endif %}
                {{ field }}
                {% for error in field.errors %}<p class="field-error">{{ error }}</p>{% endfor %}
            </div>
            {% endfor %}
            <button type="submit" class="btn-primary">{% trans "Enregistrer le profil" %}</button>
        </form>
    </div>

    <div class="panel">
        <h2 class="font-display font-semibold mb-1">{% trans "Message d'accueil" %}</h2>
        <p class="text-xs text-navy-900/45 dark:text-white/40 mb-5">
            {% trans "Texte, audio et vidéo affichés dès l'arrivée du visiteur, chacun activable indépendamment." %}
        </p>
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            <input type="hidden" name="form_type" value="welcome">

            <div class="field-group">
                <label for="{{ welcome_form.text_fr.id_for_label }}" class="field-label">{{ welcome_form.text_fr.label }}</label>
                {{ welcome_form.text_fr }}
            </div>
            <div class="field-group">
                <label for="{{ welcome_form.text_en.id_for_label }}" class="field-label">{{ welcome_form.text_en.label }}</label>
                {{ welcome_form.text_en }}
            </div>
            <div class="toggle-row">
                <span class="text-sm">{{ welcome_form.is_text_enabled.label }}</span>
                {{ welcome_form.is_text_enabled }}
            </div>

            <div class="field-group mt-4">
                <label for="{{ welcome_form.audio_file.id_for_label }}" class="field-label">{{ welcome_form.audio_file.label }}</label>
                {% if welcome_form.audio_file.value %}
                    <div id="audio-preview"></div>
                {% endif %}
                {{ welcome_form.audio_file }}
            </div>
            <div class="toggle-row">
                <span class="text-sm">{{ welcome_form.is_audio_enabled.label }}</span>
                {{ welcome_form.is_audio_enabled }}
            </div>

            <div class="field-group mt-4">
                <label for="{{ welcome_form.video_file.id_for_label }}" class="field-label">{{ welcome_form.video_file.label }}</label>
                {% if welcome_form.video_file.value %}
                    <video controls class="w-full mb-2" src="{{ welcome_form.video_file.value.url }}"></video>
                {% endif %}
                {{ welcome_form.video_file }}
            </div>
            <div class="toggle-row">
                <span class="text-sm">{{ welcome_form.is_video_enabled.label }}</span>
                {{ welcome_form.is_video_enabled }}
            </div>

            <button type="submit" class="btn-primary mt-5">{% trans "Enregistrer le message d'accueil" %}</button>
        </form>
    </div>

</div>
{% endblock %}

{% block extra_scripts %}
{% load static %}
<script src="{% static 'js/voice-player.js' %}"></script>
{% if welcome_form.audio_file.value %}
<script>
    document.getElementById("audio-preview").appendChild(
        createVoicePlayer("{{ welcome_form.audio_file.value.url }}")
    );
</script>
{% endif %}
{% endblock %}
EOF_TEMPLATES_DASHBOARD_COMPANY_SETTINGS_HTML

base64 -d << 'B64_STATIC_IMAGES_SPORTI-LOGO_PNG' > static/images/sporti-logo.png
iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAMAAABrrFhUAAADAFBMVEUAAhT7/PwBByYNFS0DGEzn6OwDJ2/IytLS1NoHdu4DR60E
N44JZdUDWMsmJzECaufW2uQxOEkKJVIMhvYSEhtHR09maG8LVbOGiI6mp61SWWkKNXJzeYgYIzQLRZOztLgrl/eRmadTVFmUlZnV
5fASlfozNDp0dHk2Q1RSt/WyusYupvkteM9v1vsBPKQvSGlYZHS4w894g5NvyPeO1/cpiO4VNVVNqPGXo7EBLYIzhtLS9v0TZLJs
uPOv1/ATdNKPyPEmLENxiqgBHWYVRXGx5/uMqssXpPxOl89Rd5NYxPgxVnEsV44VVZMydrQsZ61QaIpxpdJMhq6tyeYxZ5BLidBR
p9N06P4ATMRLmeeNuehLeKyP5fyS9f9wla5sqOeStdNqmc8ofOROmLZut9E2dpQ1ltNETGNkbYOs9v9a1v43t/wyhrEYg9gkPGcl
asgADURQhJIVVXYhHiQlW6xAPkM2ZXknTYdvpreCjqWNxNEhGxpJXogYcq9EesVifKZxwtcAXeAbaY1EbKhYorlcttN0k5x48//h
4d49g5wxo8tBOTdFQTxUcntiXV1hi8VlneGEnMXAv8Pg3+GBfHihnqOkvuLCvLkZMj4RQl0oIBc+V10nlbhEi+BhXmCEr+OUt76k
op+61d3BzuIbIB8ald1a4P99gH91sbuBf4mAgH+O0Nmln5ujrsXDwb7e4N7h3d4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADjIqK2AAAAyHRSTlP/////
////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK1Jx/kAAELJSURBVHja7b2Ff9xI1i5cUkktdbda
bqmZGY1tjtmOmR2HkwnMJBmm3cHl9y68e+/LfBk/5j/xO6dKUqvBHtuTwU39djOGdrfOUweec+pUFSGvxqvxarwar8ar8Wq8Gq/G
q/FqvBqvxqvxXQyRUir+icqe2fv4d8+GJx8ODz97Y2cv86cm/fGzh6+99nDiN89gTOCXJ5/RPx3xjTcevvbwi88MW2Ra3wE8hnf+
RCDIvHHntZUx0PmwkazF4/F00sCffjz82uTxn4L8n02+9rMx/KI6K9hDJTRM6M7ka8/MH738j157uBMmxcJsjZB600agGFZLlFD4
5d6PW3z67LWfgcLryn1tplkl+mywHIQht0hJaMHvxx6+Pfbjlv/tJyScS4RJ7SQwdBohxvGbxqqeMcZIRBAytSIZffjaj1kHTkD+
qiyU5QiJPtZCSzqColerepjoZSESEaLEmHxY/7GyPrLzWosYgrB0+6kACOQH8s1SK1hmQ/mXlbejVBBqpP5w8scaDo2HkxkqC6fb
t2JDcpU88AYWJwfzlVAoVBl8d7gx8Y+kLIAO7Lz96Ec28cz6jWhp5e0iUeTC/eVYzHcLIt/cgLfi9XpD1mjUyOmkIETEZw9no9Uf
leuLpJsyxLqHm6QmyMmMFvPFfPfj5CchrzNCIe9MjSzNACeg9YdvC0I5EdXb+P2Ahx5NoPBKqXhj1ySynKxT0YcDPGDIO9CGwJsf
I8HQiiCMk0cP0/FcELCIGz906WsK8rxC8afwzYv3SFSIjxIgPCD/yK0SOQhpA/bwDuST9NSbDwoynX7tM9Sbt2bLgEH1B2v4NIpE
Txlns1j9Dzcae0RRDZIBBDyoAvd1+r5mD4Agb2RWtOUnQfCDEyt1yo2nFBSUKP2hWQI+bSSBcx/HmK6P/eHZxOC7uzQsx5kszAhG
/tM4OfDa0qMO0OnFgPa0IOTI8+GVn82OMR9AkwlZLhk/JG8g4uSD6suJJIhbreWWFgdD3tBugxTLEfw9DFSBwCYxvQFnaBoZvRfQ
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
B64_STATIC_IMAGES_SPORTI-LOGO_PNG

base64 -d << 'B64_STATIC_ICONS_ICON-192_PNG' > static/icons/icon-192.png
iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAMAAABlApw1AAADAFBMVEUBAhQBByb7+/wNFi0CGEwDKG7n6OwnKDLR1NrIydEESK0E
N44FdvAKJlEKZtUxOEgSExsEWMvV2uNHSFBmZ24CaeenqK0MhveHh40KNXNTWWgKRZMMVrMXIzVyeIeUlJmztbk0NDl1dXqzusWT
maZTVFkSlvssl/dWY3RTt/Yqh+wWNlOXo7E0RFQxpvsVdNXY5O52g5MqeM+3w89OldJsx/lt1/pLqfQBPKVLh7IrR2iO2PlVxvdy
qNITRnVsufEVZbMsWI8vd7Kv1/GQttAuVnM0hdQnLEIsaKtoms2w5vwCLYNLh9FKl+qMqszT9/1viKuOye4VVZNSdpNNeq2M5vwV
o/0xZ4+QuehLaY1sqetwuNMATMRRptFvlbIBHGNQlbUADUk1YnisyeslaslShpp15P8gHiQkW6YvtP4iHBw4hbJtprk2dJgleuRB
PkNDS2RHiuIXg9kUdLYvk9NlbYGY9f6v+f8jO2RDbKkXYZdLQjxjXFkAWuI6UVhFXYVe1P9knOd2xNyHgnygnqMXQVhYtddgXmVj
i8eEjaKGncGUsLujoJ290tlAOjpWc3xoY12CfnmCreWFydqgnpzAv8LDzuEcUXglTpI4wP9awd9gfqd98v+irsOgv+XAwL/h39/g
3+Hn5d8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABraQWIAAAAyHRSTlP/////
////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////
////////////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABLnkX8AACrPSURBVHja7X2He9tG0vcCCxCFRCEB
sfdOiZKo3rssybItS5Z7j51cerlcLrney1vu3l6+3v7Sb2YXAEmJtmmnP4/3zlEBScxv+swOVoS8Xq/X6/V6vV6v1+v1en1Xl2Dd
ebx27969x6fj9HtI/vgHKzdW1h6/9dZbD+Zu3Fgb/76R/7vP7zVzhNiK8jYhuSf3Pv/dhe8R+fSDz+9Z8DUZEmGFNNCg3AdffPC9
UaTxGysWcR8eO8TtIAKxoKgOsVZWrO8J/Z//PXEU52jybpmkj6pT+akqUUVFIfc+/14gsL5ok4IYc+yHI3ddQqkCiyTFUrFMPriR
+x7o/8ouKYonszuOPTuyFt89WTlZ2ZmZOXSSokv+9V+/8+SXPjgEdp9MZ7NPFSMSaSVw1W9OtGrNq2I6d2NK+Q4T7yQ1UfwiXRLb
lpnV36yQzYi3EpEJx50TReX0CzHWTn8XQShlIL7Tri09IJpmUapnF2f/iSZGcCGExri7cCLGhbmHbjwWm8l/tzAoeVUUK03w8/Zn
6yUxDd8YUV1fI5sj5ghfjdLp6F4HRHAPX+8W1Yr7nQkL6RmgPk3I279668HEKk1WIA0ShLC+eLlGIz6ABL0+OdkWk8bK2nHNBn1z
K1oVvarwraZrwEyItmqeAlOPNibqiXdbpOgyAJKuR98i0Wg2m9V1PZsl183IHVUTJhqN1sZDlJZSiBWdbxGCADe24iJYLBgAUA/e
JrL6J0pchV2UQATTOUHwyaPvR80tV6WPWwmwCMAA6R0tiBCiiSB8S9xH8qcoqbWR+nr9083W6hgpOPwqDQPjt0nJdcv/nEwWlDFT
jxpKke43T2evNBKJxsbuP9pEKYqa4wlB4P++ATj8LvtAfp6+Xd7dqEcS9dkPx8iTeUrsaqxM0DwFORPWZXJvbmOj1VpotUlG1ylJ
I7xSeurildHEaOsE4FsVsagwpetfX6/yAIOTyH1l6vZCIlJfWBoHuyR/ukVc8pM7FYsYhiHJ4bBMxhZGIuhGRzZ+DkZBmyEHLRj0
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
SUVORK5CYII=
B64_STATIC_ICONS_ICON-192_PNG

base64 -d << 'B64_STATIC_ICONS_ICON-512_PNG' > static/icons/icon-512.png
iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAMAAADDpiTIAAADAFBMVEUAAhT7/PwBByYMFS0DGEwDJ2/n6OwHduwJZdUEWcoDR60E
N4/IytPR09sKhvUCaufX2+MLJVIwN0omJzIKVbQREhsrlvQMNXNRWGpGSFEMRZPU5vBweIqGiJAZIjVmZ3CnqK4SlvhSuPQBLIQn
ie9ryPWRmKeztbowpffS9vyM2PZv1/qyusYzNDo4Q1URdNZWxviUlZlTVVpXZHYpd9Kx5/gvSGt0dHkBPKNMp+6v1++R5vsBHWR3
g5S2w9AZpPxsuOwuhtOXpLGNyO0UZbVSaIkXNVRRl9GQqcoyVXElLUOUttVNh8txiKgqaLAzZ4+syudFTGOy9/0VRHMVVZVUp9Qt
WIxTdpBHmulwptM1tPl24f5Lh7AxdbRNeK4oe+N0lq8BTcJsmc1kbIOMuuZS1fs0lNUYhNZPlbFpqeUmasckO2Vvt9AzhbIlWqgz
yvyU8/4ADUVUtNmRxtdvpbWDjaIZdbgkS4Y1dZTg3uNFfMdyxNpQhZcyYnlxk5s4pc1gXmSz1NsaQVhjfKUaZpkgHiZGXIVli8Wg
nqMYVXY5UlyAfoeYtbxWpbujrsTAvsI20f5APkSFncR3s7uM0tujvuMblNUylLKBrOMddZRHaa0dMjsasv1SdnxonOZ98v+CfXu7
wL/i3t4BXuEvgZtakZ7FzuIhGh4dYHwgP4JCPz5BX6JfYFphWF1jZF5hf8uDgH+doJ+hm5egoJ/Cvr7a4d8AAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA6nUMTAAAAyHRSTlP+////
////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAAL0znwcAALmqSURBVHja7f0HY9vIli6KAigCzBQB
5kwFkgoUKYkKFhWsLFnJObbtdttud+7dcffOs+PsSWfmTLzzTron33fvy+n/vVpVBaAQGCTbsrs3q4NliSIBrK/W+laotQRhsAZr
sAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZrsAZr
sAZrsAZrsAbre7YQQsViEaHBk/iTk7x25e6H33z680lYlZ9/+s2Hd69oAxz8aazilf/x6eTKyso77+D/TU7BIl+uTH76i8YABD/w
pba+AeGvELGvrHzxxcqK/tcp+ME/fXOlOHhKP1jF/8tPqbDJfv/5/Scf/uIuXr/4xYf3f05gMQn/n3zSGDyqH+Tm/8UkiBj+9+nD
VqNo0fao2Lj74dcrX4BNWFn59Io0eF4/sLX3BEsXa/mFyScdlTzS7lIVMYDAD474/Q/Q7fjfb67wGx/FyOK/9e8BAwQCA0Pwg1nS
3Uli+ReeGHs/Nlco18KKIsJSwn9XLsxp+s+ufEPZwJMBHfxhLO3TL94h4tdFHCuERZdVMH6j8c0C1hdf/NOVwcP7ASzY/pMrbUP8
gIDMbDjqREBMEEoZBoGjGyvYDjwZxAW+99b/Plj0G99MU8n/P2t/HaNqoRpS7ACYFYSMGEpTs9ECs7HytTp4hN9v9Q/bf6FNhBpL
15XoUVupkm2NCvWoaMVANCEIZVGHQPEbYAKTAy74fV6LWIIrN7awxBMCqoriyY5v52FOKZEfrlWv5XIWBMwJwhz8uUR/exc8h4UB
Efj+rivYo1tZyOt/na7lHu40fTv3QdnjlX9Sv7Zerx/A+tv6elgpY8UASiGE/yRMYHKAgO+//IHWabVSAr6zJD6N+3zxY7FGXnBS
fXJyspbP53db6dazfLWOxV6jdLBEfAL16y+wPzhAwPdX/gtRIP8lvK3DRO9ncvd9eG1SBMTSGhcFShQz+C9/DQBIY01Qj2E1gI6A
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
B64_STATIC_ICONS_ICON-512_PNG

echo "Fichiers ecrits."
