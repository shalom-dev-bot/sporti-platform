/**
 * Lecteur de message vocal façon WhatsApp : bouton play/pause rond,
 * onde sonore (waveform) cliquable avec progression, temps restant.
 * Reutilisable partout ou un audio_file doit etre affiche (accueil,
 * chat, dashboard).
 */

const SPORTI_ICON_PLAY = '<svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const SPORTI_ICON_PAUSE = '<svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
const SPORTI_ICON_MIC_BADGE = '<svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1"/><line x1="12" x2="12" y1="18" y2="22"/></svg>';
const SPORTI_WAVEFORM_BARS = 40;

// Les <audio> crees ici (new Audio(src)) ne sont JAMAIS ajoutes au DOM
// (deliberement : pas besoin, .play()/.pause() marchent tres bien sur un
// element detache) -- document.querySelectorAll("audio") ne peut donc
// jamais les trouver. On garde nous-memes une reference vers celui en
// cours de lecture pour pouvoir le mettre en pause quand un autre demarre.
let sportiCurrentlyPlayingAudio = null;

function sportiFormatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

// Genere une onde "plausible" (sans decodage reel) utilisee tant que le
// vrai fichier n'est pas encore decode, ou si le decodage echoue.
function sportiFallbackPeaks(barCount) {
    const peaks = [];
    for (let i = 0; i < barCount; i++) {
        const t = i / barCount;
        peaks.push(0.25 + 0.5 * Math.abs(Math.sin(t * 11.3)) * (0.5 + 0.5 * Math.abs(Math.sin(t * 3.1))));
    }
    return peaks;
}

// Une seule passe fetch + decodeAudioData sert a la fois a calculer
// l'onde sonore ET la duree exacte (audioBuffer.duration, fiable et
// instantane -- pas besoin du bidouillage "seek vers une position enorme
// puis attendre timeupdate" qui demandait un aller-retour reseau
// SUPPLEMENTAIRE et pouvait prendre plusieurs secondes sur un reseau
// mobile, donnant l'impression que la duree restait bloquee a 0:00).
async function sportiAnalyzeAudio(src, barCount) {
    try {
        const res = await fetch(src);
        const arrayBuffer = await res.arrayBuffer();
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioCtx();
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
        const channelData = audioBuffer.getChannelData(0);
        const samplesPerBar = Math.max(1, Math.floor(channelData.length / barCount));
        const peaks = [];
        for (let i = 0; i < barCount; i++) {
            let max = 0;
            const start = i * samplesPerBar;
            for (let j = 0; j < samplesPerBar; j++) {
                const v = Math.abs(channelData[start + j] || 0);
                if (v > max) max = v;
            }
            peaks.push(Math.max(0.08, Math.min(1, max)));
        }
        const duration = audioBuffer.duration;
        ctx.close();
        return { peaks, duration: isFinite(duration) ? duration : 0 };
    } catch (err) {
        return { peaks: sportiFallbackPeaks(barCount), duration: 0 };
    }
}

// "invert" = le lecteur est place sur un fond bleu plein (bulle de son
// propre message) : il faut alors des barres claires (blanches), jamais
// bleues, sous peine de se fondre dans le fond -- exactement le bug
// remonte ("on ne voit rien"). Sans invert (bulle recue, theme clair ou
// sombre), on garde la palette bleu/neutre habituelle.
function sportiDrawWaveform(canvas, peaks, progressRatio, invert) {
    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) return;
    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);
    const barCount = peaks.length;
    const gap = 3;
    const barWidth = Math.max(2, width / barCount - gap);
    const isDark = document.documentElement.classList.contains("dark");
    let playedColor;
    let unplayedColor;
    if (invert) {
        playedColor = "rgba(255,255,255,0.95)";
        unplayedColor = "rgba(255,255,255,0.35)";
    } else {
        playedColor = isDark ? "#5b8def" : "#2d6cdf";
        unplayedColor = isDark ? "rgba(255,255,255,0.22)" : "rgba(11,15,25,0.2)";
    }
    const progressX = width * progressRatio;
    for (let i = 0; i < barCount; i++) {
        const x = i * (barWidth + gap);
        const barHeight = Math.max(3, peaks[i] * height);
        const y = (height - barHeight) / 2;
        ctx.fillStyle = x < progressX ? playedColor : unplayedColor;
        if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barHeight, barWidth / 2);
            ctx.fill();
        } else {
            ctx.fillRect(x, y, barWidth, barHeight);
        }
    }
}

function createVoicePlayer(src, options) {
    const invert = !!(options && options.invert);
    const wrap = document.createElement("div");
    wrap.className = invert ? "voice-player voice-player-invert" : "voice-player";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "voice-play-btn";
    btn.innerHTML = SPORTI_ICON_PLAY;

    const canvas = document.createElement("canvas");
    canvas.className = "voice-waveform-canvas";
    // Filet de securite : un <canvas> sans dimensions definies retombe sur
    // sa taille par defaut (300x150), ce qui gonflerait toute la bulle tant
    // que le CSS externe n'a pas fini de charger/appliquer la classe.
    canvas.style.width = "100%";
    canvas.style.height = "32px";
    canvas.width = 260;
    canvas.height = 32;

    const time = document.createElement("span");
    time.className = "voice-time";
    time.textContent = "0:00";

    const audio = new Audio(src);
    audio.preload = "metadata";
    // Duree fiable : ne jamais se fier a audio.duration seul, qui peut
    // rester Infinity/NaN pour les fichiers webm issus de MediaRecorder.
    // sportiAnalyzeAudio() la calcule en meme temps que l'onde sonore,
    // en une seule passe (voir commentaire de la fonction).
    let knownDuration = 0;
    let peaks = sportiFallbackPeaks(SPORTI_WAVEFORM_BARS);
    sportiAnalyzeAudio(src, SPORTI_WAVEFORM_BARS).then((result) => {
        peaks = result.peaks;
        if (result.duration) {
            knownDuration = result.duration;
            time.textContent = sportiFormatTime(knownDuration);
        }
        redraw();
    });

    function effectiveDuration() {
        return knownDuration || (isFinite(audio.duration) ? audio.duration : 0);
    }
    function currentRatio() {
        const duration = effectiveDuration();
        return duration ? audio.currentTime / duration : 0;
    }
    function redraw() {
        sportiDrawWaveform(canvas, peaks, currentRatio(), invert);
    }

    function attemptPlay() {
        const playPromise = audio.play();
        if (!playPromise || !playPromise.catch) return;
        playPromise.catch(() => {
            // Sur mobile, un navigateur qui a mis l'onglet en arriere-plan
            // (l'utilisateur "quitte" l'appli puis revient) peut avoir
            // libere/reinitialise silencieusement les donnees de
            // l'element audio -- un simple .play() ne suffit alors plus.
            // On force un rechargement puis on retente une seule fois,
            // plutot que de laisser le bouton ne rien faire sans retour.
            audio.load();
            audio.play().catch(() => {});
        });
    }

    btn.addEventListener("click", () => {
        if (audio.paused) {
            if (sportiCurrentlyPlayingAudio && sportiCurrentlyPlayingAudio !== audio) {
                sportiCurrentlyPlayingAudio.pause();
            }
            sportiCurrentlyPlayingAudio = audio;
            attemptPlay();
        } else {
            audio.pause();
        }
    });

    audio.addEventListener("play", () => {
        btn.innerHTML = SPORTI_ICON_PAUSE;
    });
    audio.addEventListener("pause", () => {
        btn.innerHTML = SPORTI_ICON_PLAY;
        if (sportiCurrentlyPlayingAudio === audio) sportiCurrentlyPlayingAudio = null;
    });
    audio.addEventListener("ended", () => {
        btn.innerHTML = SPORTI_ICON_PLAY;
        time.textContent = sportiFormatTime(effectiveDuration());
        redraw();
        if (sportiCurrentlyPlayingAudio === audio) sportiCurrentlyPlayingAudio = null;
    });
    audio.addEventListener("timeupdate", () => {
        const duration = effectiveDuration();
        if (duration) {
            time.textContent = sportiFormatTime(duration - audio.currentTime);
        }
        redraw();
    });

    canvas.addEventListener("click", (event) => {
        const rect = canvas.getBoundingClientRect();
        const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
        const duration = effectiveDuration();
        if (duration) audio.currentTime = ratio * duration;
        redraw();
    });

    window.addEventListener("resize", redraw);
    requestAnimationFrame(redraw);

    wrap.appendChild(btn);
    wrap.appendChild(canvas);
    wrap.appendChild(time);

    // Petite photo (ou pastille avec icone) de l'expediteur a droite de
    // la bulle, avec un badge micro -- comme WhatsApp.
    const avatarWrap = document.createElement("div");
    avatarWrap.className = "voice-avatar-wrap";
    if (options && options.avatarUrl) {
        const img = document.createElement("img");
        img.src = options.avatarUrl;
        img.alt = "";
        img.className = "voice-avatar";
        avatarWrap.appendChild(img);
    } else {
        const fallback = document.createElement("div");
        fallback.className = "voice-avatar voice-avatar-fallback";
        avatarWrap.appendChild(fallback);
    }
    const micBadge = document.createElement("span");
    micBadge.className = "voice-avatar-mic-badge";
    micBadge.innerHTML = SPORTI_ICON_MIC_BADGE;
    avatarWrap.appendChild(micBadge);
    wrap.appendChild(avatarWrap);

    return wrap;
}
