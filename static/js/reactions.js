/**
 * Reactions emoji façon WhatsApp, partagees entre la page client et le
 * dashboard admin :
 * - Un clavier complet d'emojis (grille), pas juste 6 boutons.
 * - Desktop : petit bouton visible au survol de la bulle.
 * - Mobile : appui long (maintenir) n'importe ou sur la bulle -- le survol
 *   n'existe pas au doigt, d'ou l'appui long comme sur WhatsApp/Telegram.
 */

const SPORTI_EMOJI_SET = [
    "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃", "😉", "😊", "😇", "🥰", "😍", "🤩",
    "😘", "😗", "☺️", "😚", "😙", "🥲", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔",
    "🤐", "🙄", "😬", "🤥", "😐", "😑", "😶", "😏", "😒", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒",
    "🤕", "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵", "🤯", "🥳", "😎", "🤓", "😕", "🙁", "☹️", "😮",
    "😯", "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣", "😞", "😓",
    "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "👍", "👎", "👏", "🙌", "👐", "🙏", "💪", "❤️", "🧡",
    "💛", "💚", "💙", "💜", "🖤", "🤍", "💔", "💕", "💯", "🔥", "🎉", "✨", "😺", "😻", "🎁", "👀",
];

function buildEmojiGrid(onSelect) {
    const grid = document.createElement("div");
    grid.className = "grid grid-cols-8 gap-1 max-h-52 w-64 overflow-y-auto";
    SPORTI_EMOJI_SET.forEach((emoji) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "text-lg leading-none p-1 hover:scale-125 transition-transform";
        btn.textContent = emoji;
        btn.addEventListener("click", (event) => {
            event.stopPropagation();
            onSelect(emoji);
        });
        grid.appendChild(btn);
    });
    return grid;
}

function groupReactions(emojis) {
    const counts = {};
    (emojis || []).forEach((e) => {
        counts[e] = (counts[e] || 0) + 1;
    });
    return Object.entries(counts).map(([emoji, count]) => ({ emoji, count }));
}

function renderReactionBadges(container, emojis) {
    container.innerHTML = "";
    groupReactions(emojis).forEach(({ emoji, count }) => {
        const badge = document.createElement("span");
        badge.className = "inline-flex items-center gap-1 text-xs bg-navy-900/5 dark:bg-white/10 rounded-full px-2 py-0.5 mr-1 mt-1";
        badge.textContent = count > 1 ? `${emoji} ${count}` : emoji;
        container.appendChild(badge);
    });
}

function closeAllReactionPickers() {
    document.querySelectorAll(".reaction-picker-open").forEach((p) => p.classList.add("hidden"));
}
document.addEventListener("click", closeAllReactionPickers);

/**
 * Attache le picker de reaction a une bulle de message.
 * sendReactionFn(messageId, emoji) doit envoyer la reaction via le socket.
 */
function attachReactionUI(div, messageId, sendReactionFn, isOwnMessage, onDeleteFn, deleteLabel) {
    div.classList.add("group", "relative");

    const picker = document.createElement("div");
    picker.className = "hidden absolute -top-56 right-0 bg-white dark:bg-navy-850 border border-navy-900/10 dark:border-white/10 rounded-lg p-2 shadow-lg z-20 reaction-picker-open";
    picker.appendChild(
        buildEmojiGrid((emoji) => {
            sendReactionFn(messageId, emoji);
            picker.classList.add("hidden");
        })
    );

    if (isOwnMessage && onDeleteFn) {
        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.className = "mt-1 w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-medium text-red-500 hover:bg-red-500/10 transition-colors";
        deleteBtn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span></span>';
        deleteBtn.querySelector("span").textContent = deleteLabel || "Supprimer";
        deleteBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            picker.classList.add("hidden");
            onDeleteFn(messageId);
        });
        picker.appendChild(deleteBtn);
    }

    const reactBtn = document.createElement("button");
    reactBtn.type = "button";
    reactBtn.className = "absolute -top-3 right-1 text-xs bg-white dark:bg-navy-850 border border-navy-900/10 dark:border-white/10 rounded-full w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center";
    reactBtn.textContent = "🙂";
    reactBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        closeAllReactionPickers();
        picker.classList.toggle("hidden");
    });

    // Appui long (mobile) : maintenir sur la bulle ouvre le picker.
    let pressTimer = null;
    const startPress = () => {
        pressTimer = setTimeout(() => {
            closeAllReactionPickers();
            picker.classList.remove("hidden");
            if (navigator.vibrate) navigator.vibrate(15);
        }, 450);
    };
    const cancelPress = () => {
        if (pressTimer) clearTimeout(pressTimer);
    };
    div.addEventListener("touchstart", startPress, { passive: true });
    div.addEventListener("touchend", cancelPress);
    div.addEventListener("touchmove", cancelPress);
    div.addEventListener("touchcancel", cancelPress);
    div.addEventListener("contextmenu", (event) => event.preventDefault());

    div.appendChild(reactBtn);
    div.appendChild(picker);
}

/**
 * Bouton emoji dans la barre de composition : ouvre le meme clavier complet,
 * mais pour ENVOYER un emoji comme message (pas une reaction).
 */
function attachComposerEmojiButton(button, textarea) {
    const picker = document.createElement("div");
    picker.className = "hidden absolute bottom-12 right-0 bg-white dark:bg-navy-850 border border-navy-900/10 dark:border-white/10 rounded-lg p-2 shadow-lg z-20 reaction-picker-open";
    picker.appendChild(
        buildEmojiGrid((emoji) => {
            const start = textarea.selectionStart ?? textarea.value.length;
            const end = textarea.selectionEnd ?? textarea.value.length;
            textarea.value = textarea.value.slice(0, start) + emoji + textarea.value.slice(end);
            const newPos = start + emoji.length;
            textarea.setSelectionRange(newPos, newPos);
            textarea.focus();
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
        })
    );
    button.parentElement.style.position = button.parentElement.style.position || "relative";
    button.parentElement.appendChild(picker);

    button.addEventListener("click", (event) => {
        event.stopPropagation();
        closeAllReactionPickers();
        picker.classList.toggle("hidden");
    });
}
