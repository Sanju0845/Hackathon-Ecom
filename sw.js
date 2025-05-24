const CACHE_NAME = 'store-v1';
const urlsToCache = [
  '/',
  '/auth/login.html',
  '/auth/signup.html',
  '/admin/admin.html',
  '/admin/orders.html',
  '/users/products.html',
  'https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
}); 