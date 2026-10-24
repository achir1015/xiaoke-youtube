/* 小柯機器人 YouTube 下載工具 - 讓網頁可以「加到主畫面／建立捷徑」並離線開啟介面 */
var CACHE = "xk-yt-v1";
var SHELL = [
  "./", "./index.html", "./style.css", "./app.js",
  "./icon.svg", "./favicon-32.png", "./icon-192.png", "./icon-512.png", "./manifest.json"
];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return c.addAll(SHELL).catch(function () {});
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) {
      return k === CACHE ? null : caches.delete(k);
    }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);
  // API 永遠走網路，不快取
  if (e.request.method !== "GET" || url.pathname.indexOf("/api/") === 0) return;
  e.respondWith(
    fetch(e.request).then(function (r) {
      var copy = r.clone();
      caches.open(CACHE).then(function (c) { c.put(e.request, copy).catch(function () {}); });
      return r;
    }).catch(function () { return caches.match(e.request); })
  );
});
