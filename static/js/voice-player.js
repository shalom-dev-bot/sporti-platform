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
