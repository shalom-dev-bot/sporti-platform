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
    grid.className = "grid grid-cols-7 gap-0.5 max-h-52 overflow-y-auto thin-scroll";
    // Filet de securite : force la grille en ligne/colonnes via inline style,
    // independamment du chargement/purge du CSS externe (meme logique que
    // pour le canvas de l'onde vocale) -- garantit un vrai quadrillage
    // horizontal plutot qu'une colonne verticale si la classe utilitaire
    // grid-cols-7 ne s'applique pas pour une raison ou une autre.
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(7, minmax(0, 1fr))";
    grid.style.width = "17.5rem";
    SPORTI_EMOJI_SET.forEach((emoji) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "text-xl leading-none p-1.5 hover:scale-125 transition-transform flex items-center justify-center";
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
 * Selection de message façon WhatsApp : l'appui long selectionne la bulle
 * (au lieu d'ouvrir le picker de reaction) et fait apparaitre une barre en
 * haut de l'ecran avec un bouton supprimer -- plutot qu'un bouton "Supprimer"
 * planque dans le picker de reaction. Un seul message selectionne a la fois
 * (suffisant pour l'usage reel de ce chat, pas de multi-selection).
 */
let sportiSelectedMessage = null; // { messageId, bubble, onDeleteFn }

function sportiEnsureSelectBar(labels) {
    let bar = document.getElementById("sporti-select-bar");
    if (bar) return bar;
    bar = document.createElement("div");
    bar.id = "sporti-select-bar";
    bar.style.cssText =
        "display:none;position:fixed;top:0;left:0;right:0;z-index:60;align-items:center;" +
        "gap:0.5rem;padding:0 0.75rem;height:3.25rem;background:#0B0F19;" +
        "border-bottom:1px solid rgba(255,255,255,0.1);";

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.style.cssText =
        "display:flex;align-items:center;justify-content:center;width:2.25rem;height:2.25rem;" +
        "border-radius:9999px;color:rgba(255,255,255,0.8);background:transparent;border:none;flex-shrink:0;";
    closeBtn.innerHTML =
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    closeBtn.addEventListener("click", sportiDeselectMessage);

    const count = document.createElement("span");
    count.id = "sporti-select-count";
    count.style.cssText = "flex:1;font-size:0.875rem;font-weight:600;color:#fff;";
    count.textContent = labels.selected;

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.id = "sporti-select-delete-btn";
    deleteBtn.style.cssText =
        "display:none;align-items:center;justify-content:center;width:2.25rem;height:2.25rem;" +
        "border-radius:9999px;color:#f87171;background:transparent;border:none;flex-shrink:0;";
    deleteBtn.setAttribute("aria-label", labels.deleteForEveryone);
    deleteBtn.innerHTML =
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/>' +
        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';
    deleteBtn.addEventListener("click", () => sportiOpenDeleteConfirm(labels));

    bar.appendChild(closeBtn);
    bar.appendChild(count);
    bar.appendChild(deleteBtn);
    document.body.appendChild(bar);
    return bar;
}

function sportiSelectMessage(messageId, bubble, isOwnMessage, onDeleteFn, labels) {
    if (sportiSelectedMessage && sportiSelectedMessage.messageId === messageId) {
        sportiDeselectMessage();
        return;
    }
    sportiDeselectMessage();
    closeAllReactionPickers();
    sportiSelectedMessage = { messageId, bubble, onDeleteFn };
    bubble.style.outline = "2px solid #375dff";
    bubble.style.outlineOffset = "2px";
    bubble.style.borderRadius = "16px";
    const bar = sportiEnsureSelectBar(labels);
    bar.style.display = "flex";
    document.getElementById("sporti-select-count").textContent = labels.selected;
    document.getElementById("sporti-select-delete-btn").style.display = isOwnMessage && onDeleteFn ? "flex" : "none";
    if (navigator.vibrate) navigator.vibrate(15);
}

function sportiDeselectMessage() {
    if (sportiSelectedMessage) {
        sportiSelectedMessage.bubble.style.outline = "";
        sportiSelectedMessage.bubble.style.outlineOffset = "";
    }
    sportiSelectedMessage = null;
    const bar = document.getElementById("sporti-select-bar");
    if (bar) bar.style.display = "none";
}

function sportiOpenDeleteConfirm(labels) {
    if (!sportiSelectedMessage) return;
    const { messageId, bubble, onDeleteFn } = sportiSelectedMessage;

    const backdrop = document.createElement("div");
    backdrop.style.cssText =
        "position:fixed;inset:0;z-index:70;background:rgba(0,0,0,0.5);" +
        "display:flex;align-items:flex-end;justify-content:center;";

    const modal = document.createElement("div");
    modal.style.cssText =
        "width:100%;max-width:26rem;background:#121826;border-radius:1.1rem 1.1rem 0 0;" +
        "padding:0.6rem;padding-bottom:calc(env(safe-area-inset-bottom, 0px) + 0.6rem);";

    function makeBtn(label, color, onClick) {
        const b = document.createElement("button");
        b.type = "button";
        b.style.cssText =
            `width:100%;text-align:left;padding:0.85rem 1rem;border-radius:0.85rem;` +
            `font-size:0.9rem;font-weight:500;color:${color};background:transparent;border:none;`;
        b.textContent = label;
        b.addEventListener("click", onClick);
        return b;
    }

    modal.appendChild(
        makeBtn(labels.deleteForEveryone, "#f87171", () => {
            document.body.removeChild(backdrop);
            onDeleteFn(messageId);
            sportiDeselectMessage();
        })
    );
    modal.appendChild(
        makeBtn(labels.deleteForMe, "#e5e7eb", () => {
            document.body.removeChild(backdrop);
            bubble.remove();
            sportiDeselectMessage();
        })
    );
    modal.appendChild(
        makeBtn(labels.cancel, "#9ca3af", () => {
            document.body.removeChild(backdrop);
        })
    );

    backdrop.appendChild(modal);
    backdrop.addEventListener("click", (event) => {
        if (event.target === backdrop) document.body.removeChild(backdrop);
    });
    document.body.appendChild(backdrop);
}

/**
 * Attache le picker de reaction + la selection/suppression a une bulle de
 * message. sendReactionFn(messageId, emoji) envoie la reaction via le
 * socket ; labels = { deleteForEveryone, deleteForMe, cancel, selected }.
 */
function attachReactionUI(div, messageId, sendReactionFn, isOwnMessage, onDeleteFn, labels) {
    div.classList.add("group", "relative");

    const picker = document.createElement("div");
    picker.className = "hidden absolute -top-56 right-0 bg-white dark:bg-navy-850 border border-navy-900/10 dark:border-white/10 rounded-lg p-2 shadow-lg z-20 reaction-picker-open";
    picker.appendChild(
        buildEmojiGrid((emoji) => {
            sendReactionFn(messageId, emoji);
            picker.classList.add("hidden");
        })
    );

    const reactBtn = document.createElement("button");
    reactBtn.type = "button";
    // Toujours visible (pas seulement au survol) : sur tactile, un appui
    // long selectionne desormais le message (pour le supprimer), donc c'est
    // ce petit bouton qui reste le seul moyen de reagir sur mobile.
    reactBtn.className = "absolute -top-3 right-1 text-xs bg-white dark:bg-navy-850 border border-navy-900/10 dark:border-white/10 rounded-full w-6 h-6 flex items-center justify-center opacity-70 hover:opacity-100 transition-opacity";
    reactBtn.textContent = "🙂";
    reactBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        closeAllReactionPickers();
        picker.classList.toggle("hidden");
    });

    // Appui long (mobile) ou clic long (desktop) : selectionne le message
    // (barre du haut avec bouton supprimer), comme WhatsApp.
    let pressTimer = null;
    let pressMoved = false;
    const startPress = () => {
        pressMoved = false;
        pressTimer = setTimeout(() => {
            if (pressMoved) return;
            sportiSelectMessage(messageId, div, isOwnMessage, onDeleteFn, labels);
        }, 450);
    };
    const cancelPress = () => {
        if (pressTimer) clearTimeout(pressTimer);
    };
    const markMoved = () => {
        pressMoved = true;
        cancelPress();
    };
    div.addEventListener("touchstart", startPress, { passive: true });
    div.addEventListener("touchend", cancelPress);
    div.addEventListener("touchmove", markMoved);
    div.addEventListener("touchcancel", cancelPress);
    div.addEventListener("mousedown", (event) => {
        if (event.button !== 0) return;
        startPress();
    });
    div.addEventListener("mouseup", cancelPress);
    div.addEventListener("mouseleave", cancelPress);
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
