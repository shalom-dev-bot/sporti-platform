/**
 * Service Worker SPORTI.
 * - Permet l'installation de l'application (PWA).
 * - Met en cache les ressources essentielles, dont la page hors-ligne.
 * - En cas de coupure reseau sur une navigation, affiche la page offline
 *   plutot qu'une erreur brute du navigateur.
 * - Gere la reception et l'affichage des notifications push.
 */
const CACHE_NAME = "sporti-cache-v2";
const OFFLINE_URL = "/offline/";
const PRECACHE_URLS = [
    "/",
    "/static/manifest.json",
    OFFLINE_URL,
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) =>
            Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            )
        )
    );
    self.clients.claim();
});

self.addEventListener("push", (event) => {
    const data = event.data ? event.data.json() : {};
    event.waitUntil(
        self.registration.showNotification(data.title || "SPORTI", {
            body: data.body || "",
            icon: "/static/icons/icon-192.png",
            data: { url: data.url || "/" },
        })
    );
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url || "/"));
});

self.addEventListener("fetch", (event) => {
    // Pour les navigations de page (pas les appels API/WebSocket), on
    // bascule sur la page offline si le reseau echoue completement.
    if (event.request.mode === "navigate") {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(OFFLINE_URL))
        );
        return;
    }

    // Pour le reste (styles, scripts, images), strategie network-first
    // avec repli sur le cache si disponible.
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
