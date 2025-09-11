// Wallai Service Worker
const CACHE_NAME = 'wallai-v1.0.0';
const API_CACHE_NAME = 'wallai-api-v1.0.0';

// Files to cache for offline use
const STATIC_CACHE_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/pwa/manifest.json',
    '/static/pwa/icon-192x192.png',
    '/static/pwa/icon-512x512.png'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
    '/api/auth/user/',
    '/api/spaces/',
    '/api/budgets/',
    '/api/expenses/'
];

// Install Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Precaching static files');
                return cache.addAll(STATIC_CACHE_FILES);
            })
            .then(() => {
                console.log('[SW] Static files cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Failed to cache static files:', error);
            })
    );
});

// Activate Service Worker
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        // Delete old caches
                        if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - Network-first strategy for API, Cache-first for static files
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }
    
    // Handle API requests with network-first strategy
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }
    
    // Handle static files with cache-first strategy
    event.respondWith(cacheFirstStrategy(request));
});

// Cache-first strategy for static files
async function cacheFirstStrategy(request) {
    try {
        const cached = await caches.match(request);
        if (cached) {
            console.log('[SW] Serving from cache:', request.url);
            return cached;
        }
        
        console.log('[SW] Fetching from network:', request.url);
        const response = await fetch(request);
        
        // Cache successful responses
        if (response.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        console.error('[SW] Cache-first strategy failed:', error);
        
        // Return offline fallback for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/');
        }
        
        throw error;
    }
}

// Network-first strategy for API requests
async function networkFirstStrategy(request) {
    try {
        console.log('[SW] API request - trying network first:', request.url);
        const response = await fetch(request);
        
        // Cache successful GET responses
        if (response.status === 200 && request.method === 'GET') {
            const cache = await caches.open(API_CACHE_NAME);
            cache.put(request, response.clone());
            console.log('[SW] API response cached:', request.url);
        }
        
        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        
        // Fallback to cache if network fails
        const cached = await caches.match(request);
        if (cached) {
            console.log('[SW] Serving API from cache:', request.url);
            return cached;
        }
        
        // Return offline response for API requests
        return new Response(
            JSON.stringify({
                success: false,
                error: {
                    message: 'No internet connection',
                    code: 'OFFLINE_ERROR'
                }
            }),
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
    }
}

// Handle push notifications (future feature)
self.addEventListener('push', (event) => {
    console.log('[SW] Push received');
    
    const options = {
        body: 'You have new updates in Wallai',
        icon: '/static/pwa/icon-192x192.png',
        badge: '/static/pwa/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View details',
                icon: '/static/pwa/icon-96x96.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/pwa/icon-96x96.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Wallai', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification click received');
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            self.clients.openWindow('/dashboard/')
        );
    }
});

// Sync background data (future feature)
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    console.log('[SW] Performing background sync');
    // Implementation for offline data sync
    // This will sync cached expenses, budgets, etc. when online
}