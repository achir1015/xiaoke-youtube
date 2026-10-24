/* 小柯機器人 YouTube 下載小圖示 - 背景服務
   所有跟後端的連線都在這裡做：YouTube 是 https 頁面，內容腳本直接連
   http://127.0.0.1 會被混合內容擋下，但擴充功能的背景環境沒有這個限制。 */

var DEFAULT_TARGETS = [
  { id: "local", name: "這台電腦", base: "http://127.0.0.1:8787" }
];

function getSettings() {
  return chrome.storage.sync.get({
    targets: DEFAULT_TARGETS,
    activeId: "local",
    mode: "mp4",
    quality: 1080
  });
}

chrome.runtime.onInstalled.addListener(function () {
  getSettings().then(function (s) { chrome.storage.sync.set(s); });
});

function trim(base) {
  return String(base || "").replace(/\/+$/, "");
}

async function call(base, path, body) {
  var url = trim(base) + path;
  var opt = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : { method: "GET" };
  var r = await fetch(url, opt);
  var d = null;
  try { d = await r.json(); } catch (e) { throw new Error("後端回應無法解析（HTTP " + r.status + "）"); }
  if (!r.ok || d.ok === false) throw new Error(d.error || ("HTTP " + r.status));
  return d;
}

var HANDLERS = {
  health: function (m) { return call(m.base, "/api/health"); },
  info: function (m) { return call(m.base, "/api/info", { url: m.url }); },
  start: function (m) { return call(m.base, "/api/jobs", m.body); },
  poll: function (m) { return call(m.base, "/api/jobs/" + m.jobId); },
  cancel: function (m) { return call(m.base, "/api/jobs/" + m.jobId + "/cancel", {}); },
  settings: function () { return getSettings(); },
  openSettings: function () {
    chrome.tabs.create({ url: chrome.runtime.getURL("popup.html") });
    return Promise.resolve({ ok: true });
  },
  notify: function (m) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: chrome.runtime.getURL("icons/icon-128.png"),
      title: m.title || "小柯機器人",
      message: m.message || ""
    });
    return Promise.resolve({ ok: true });
  }
};

chrome.runtime.onMessage.addListener(function (msg, sender, sendResponse) {
  var h = HANDLERS[msg && msg.type];
  if (!h) { sendResponse({ ok: false, error: "未知的指令" }); return false; }
  Promise.resolve(h(msg)).then(function (data) {
    sendResponse({ ok: true, data: data });
  }).catch(function (e) {
    sendResponse({ ok: false, error: e && e.message ? e.message : String(e) });
  });
  return true; // 非同步回覆
});
