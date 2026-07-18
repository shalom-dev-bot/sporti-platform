/**
 * Service Worker SPORTI.
 * - Permet l'installation de l'application (PWA).
 * - Mise en cache basique des ressources statiques essentielles,
 *   pour un chargement instantane et un minimum de contenu hors-ligne.
 * - Prepare le terrain pour les notifications push (tache suivante).
 */
const CACHE_NAME = "sporti-cache-v1";
const PRECACHE_URLS = [
    "/",
    "/static/manifest.json",
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

self.addEventListener("fetch", (event) => {
    // Strategie "network first" : on essaie toujours d'avoir la version
    // la plus recente, et on ne retombe sur le cache qu'en cas d'echec
    // (perte de connexion) -- important pour un chat en temps reel, ou
    // le contenu ne doit jamais etre perime silencieusement.
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
