/**
 * Lecteur de message vocal façon WhatsApp : bouton play/pause rond,
 * onde sonore (waveform) cliquable avec progression, temps restant.
 * Reutilisable partout ou un audio_file doit etre affiche (accueil,
 * chat, dashboard).
 */

const SPORTI_ICON_PLAY = '<svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const SPORTI_ICON_PAUSE = '<svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
const SPORTI_WAVEFORM_BARS = 40;

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

// Bug connu (Chrome/Android, WebM enregistre via MediaRecorder) : la duree
// annoncee par l'element <audio> reste Infinity ou NaN tant qu'on n'a pas
// force une lecture complete du conteneur. Solution standard : avancer la
// tete de lecture tres loin et attendre que le navigateur recalcule la
// vraie duree (evenement timeupdate/durationchange).
//
// Important : on fait ce "seek" sur une sonde <audio> jetable, JAMAIS sur
// l'element reellement utilise pour la lecture -- le manipuler pendant
// que l'utilisateur tape sur "lire" pouvait bloquer play() (course entre
// notre seek automatique et son clic), d'ou le bouton qui ne repondait
// plus une fois sur un vrai telephone.
function sportiProbeDuration(src) {
    return new Promise((resolve) => {
        const probe = new Audio();
        probe.preload = "metadata";
        probe.src = src;
        const finish = (duration) => {
            probe.pause();
            probe.removeAttribute("src");
            probe.load();
            resolve(duration);
        };
        probe.addEventListener("error", () => finish(0));
        probe.addEventListener("loadedmetadata", () => {
            if (isFinite(probe.duration) && probe.duration > 0) {
                finish(probe.duration);
                return;
            }
            const onTimeUpdate = () => {
                probe.removeEventListener("timeupdate", onTimeUpdate);
                finish(isFinite(probe.duration) ? probe.duration : 0);
            };
            probe.addEventListener("timeupdate", onTimeUpdate);
            probe.currentTime = 1e101;
            setTimeout(() => finish(isFinite(probe.duration) ? probe.duration : 0), 2000);
        });
    });
}

async function sportiComputePeaks(src, barCount) {
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
        ctx.close();
        return peaks;
    } catch (err) {
        return sportiFallbackPeaks(barCount);
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
    // Duree fiable, obtenue via la sonde jetable -- ne jamais se fier
    // uniquement a audio.duration, qui peut rester Infinity/NaN sur cet
    // element pour les fichiers webm issus de MediaRecorder.
    let knownDuration = 0;
    sportiProbeDuration(src).then((duration) => {
        knownDuration = duration;
        time.textContent = sportiFormatTime(knownDuration);
        redraw();
    });

    let peaks = sportiFallbackPeaks(SPORTI_WAVEFORM_BARS);
    sportiComputePeaks(src, SPORTI_WAVEFORM_BARS).then((realPeaks) => {
        peaks = realPeaks;
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
        time.textContent = sportiFormatTime(effectiveDuration());
        redraw();
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
    return wrap;
}
