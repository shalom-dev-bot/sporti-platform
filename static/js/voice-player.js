/**
 * Lecteur de message vocal façon WhatsApp : bouton play/pause rond,
 * onde sonore (waveform) cliquable avec progression, temps restant.
 * Reutilisable partout ou un audio_file doit etre affiche (accueil,
 * chat, dashboard).
 */

const SPORTI_ICON_PLAY = '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const SPORTI_ICON_PAUSE = '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
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

function sportiDrawWaveform(canvas, peaks, progressRatio) {
    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) return;
    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);
    const barCount = peaks.length;
    const gap = 2;
    const barWidth = Math.max(1.5, width / barCount - gap);
    const isDark = document.documentElement.classList.contains("dark");
    const playedColor = isDark ? "#5b8def" : "#2d6cdf";
    const unplayedColor = isDark ? "rgba(255,255,255,0.2)" : "rgba(11,15,25,0.18)";
    const progressX = width * progressRatio;
    for (let i = 0; i < barCount; i++) {
        const x = i * (barWidth + gap);
        const barHeight = Math.max(2, peaks[i] * height);
        const y = (height - barHeight) / 2;
        ctx.fillStyle = x < progressX ? playedColor : unplayedColor;
        ctx.fillRect(x, y, barWidth, barHeight);
    }
}

function createVoicePlayer(src) {
    const wrap = document.createElement("div");
    wrap.className = "voice-player";

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

    let peaks = sportiFallbackPeaks(SPORTI_WAVEFORM_BARS);
    sportiComputePeaks(src, SPORTI_WAVEFORM_BARS).then((realPeaks) => {
        peaks = realPeaks;
        redraw();
    });

    function currentRatio() {
        return audio.duration ? audio.currentTime / audio.duration : 0;
    }
    function redraw() {
        sportiDrawWaveform(canvas, peaks, currentRatio());
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
        time.textContent = sportiFormatTime(audio.duration);
        redraw();
    });
    audio.addEventListener("timeupdate", () => {
        if (audio.duration) {
            time.textContent = sportiFormatTime(audio.duration - audio.currentTime);
        }
        redraw();
    });
    audio.addEventListener("loadedmetadata", () => {
        time.textContent = sportiFormatTime(audio.duration);
        redraw();
    });

    canvas.addEventListener("click", (event) => {
        const rect = canvas.getBoundingClientRect();
        const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
        if (audio.duration) audio.currentTime = ratio * audio.duration;
        redraw();
    });

    window.addEventListener("resize", redraw);
    requestAnimationFrame(redraw);

    wrap.appendChild(btn);
    wrap.appendChild(canvas);
    wrap.appendChild(time);
    return wrap;
}
