/* 小柯機器人 - 把影片右上角「下載這個視訊」標籤（yt-overlay.js）接到擴充功能
   yt-overlay.js 是從 web/yt-overlay.js 複製過來的同一份（桌面版、Android 共用），不要直接改這裡的副本。
   標籤透過 window.__xkCall 要資料；這裡轉給 background.js，由它去連目前選取的下載平台。 */
(function () {
  "use strict";

  function send(msg) {
    return new Promise(function (resolve, reject) {
      chrome.runtime.sendMessage(msg, function (res) {
        if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
        if (!res || !res.ok) return reject(new Error((res && res.error) || "沒有回應"));
        resolve(res.data);
      });
    });
  }

  function target() {
    return chrome.storage.sync.get({
      targets: [{ id: "local", name: "這台電腦", base: "http://127.0.0.1:8787" }],
      activeId: "local"
    }).then(function (s) {
      return s.targets.filter(function (t) { return t.id === s.activeId; })[0] || s.targets[0];
    });
  }

  // 平台就是這台電腦時，檔案本來就在電腦上，不用再存一次
  function isLocal(base) {
    return /^https?:\/\/(127\.0\.0\.1|localhost|\[::1\])(:|\/|$)/i.test(base);
  }

  // 只留最後兩層，例如「Downloads › 小柯YouTube」
  function shortFolder(p) {
    var parts = String(p || "").split(/[\\/]+/).filter(Boolean);
    return parts.slice(-2).join(" › ");
  }

  var folder = null;

  function handle(m, a, t) {
    switch (m) {
      case "info":
        return send({ type: "info", base: t.base, url: a.url });
      case "start":
        return send({ type: "start", base: t.base, body: a });
      case "poll":
        return send({ type: "poll", base: t.base, jobId: a.id }).then(function (d) {
          var j = d.job || {};
          if (j.status !== "done") return d;
          if (!isLocal(t.base)) return { ok: true, job: j, finish_label: "存到這台電腦" };
          var dir = folder ? Promise.resolve(folder)
            : send({ type: "health", base: t.base }).then(function (h) { return (folder = h.folder); });
          return dir.catch(function () { return ""; }).then(function (f) {
            return { ok: true, job: j,
                     done_text: "✓ 完成，已存到「" + (shortFolder(f) || "下載 › 小柯YouTube") + "」" };
          });
        });
      case "finish":
        if (isLocal(t.base)) return Promise.resolve({ ok: true });
        return send({ type: "save", base: t.base, jobId: a.id });
      default:
        return Promise.reject(new Error("不認得的指令：" + m));
    }
  }

  window.__xkCall = function (m, a) {
    return target().then(function (t) { return handle(m, a || {}, t); })
      .catch(function (e) { return { ok: false, error: e.message }; });
  };
})();
