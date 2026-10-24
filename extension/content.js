/* 小柯機器人 YouTube 下載小圖示 - 常駐在 YouTube 頁面上的浮動按鈕與面板 */
(function () {
  "use strict";

  if (window.__xkYtDownloaderLoaded) return;
  window.__xkYtDownloaderLoaded = true;

  var HOST_ID = "xk-yt-downloader-host";
  var POS_KEY = "xk_yt_btn_bottom";

  var S = {
    settings: null,
    info: null,
    scope: "single",   // single | playlist
    mode: "mp4",
    quality: 1080,
    jobId: null,
    base: null,
    timer: null,
    open: false
  };

  /* ---------------------------------------------------- 與背景服務溝通 */

  function send(msg) {
    return new Promise(function (resolve, reject) {
      chrome.runtime.sendMessage(msg, function (res) {
        if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
        if (!res) return reject(new Error("背景服務沒有回應"));
        if (!res.ok) return reject(new Error(res.error));
        resolve(res.data);
      });
    });
  }

  /* ---------------------------------------------------- 網址判斷 */

  function params() { return new URLSearchParams(location.search); }

  function videoId() {
    if (location.pathname === "/watch") return params().get("v");
    var m = location.pathname.match(/^\/(?:shorts|live|embed)\/([\w-]{6,})/);
    return m ? m[1] : null;
  }

  function listId() {
    var l = params().get("list");
    if (l && l.indexOf("RD") !== 0 && l !== "WL" && l !== "LL") return l;  // 跳過自動混音清單
    if (location.pathname === "/playlist") return params().get("list");
    return null;
  }

  function targetUrl() {
    if (S.scope === "playlist" && listId()) {
      return "https://www.youtube.com/playlist?list=" + listId();
    }
    var v = videoId();
    return v ? "https://www.youtube.com/watch?v=" + v : location.href;
  }

  function onDownloadablePage() { return !!(videoId() || listId()); }

  /* ---------------------------------------------------- 介面 */

  var ROBOT_SVG =
    '<svg viewBox="0 0 64 64" width="100%" height="100%" aria-hidden="true">' +
    '<line x1="32" y1="4" x2="32" y2="11" stroke="#8fa6bd" stroke-width="3"/>' +
    '<circle cx="32" cy="3.5" r="3" fill="#38bdf8"/>' +
    '<rect x="8" y="10" width="48" height="40" rx="12" fill="#7d93ab"/>' +
    '<rect x="2" y="24" width="7" height="15" rx="3.5" fill="#44586e"/>' +
    '<rect x="55" y="24" width="7" height="15" rx="3.5" fill="#44586e"/>' +
    '<rect x="14" y="19" width="36" height="22" rx="9" fill="#101722"/>' +
    '<circle cx="24" cy="30" r="4" fill="#38bdf8"/><circle cx="40" cy="30" r="4" fill="#38bdf8"/>' +
    '<rect x="31" y="40" width="30" height="21" rx="6.5" fill="#ff3b30"/>' +
    '<path d="M42 44.5v12l10-6z" fill="#fff"/></svg>';

  var CSS = [
    ":host{all:initial}",
    "*{box-sizing:border-box;font-family:'Noto Sans TC','Microsoft JhengHei',system-ui,sans-serif}",
    ".fab{position:fixed;right:18px;bottom:96px;width:54px;height:54px;border-radius:50%;",
    "background:#171d27;border:2px solid #2a3342;box-shadow:0 6px 20px rgba(0,0,0,.45);",
    "cursor:pointer;z-index:2147483646;display:flex;align-items:center;justify-content:center;padding:6px;",
    "transition:transform .15s ease,border-color .15s ease}",
    ".fab:hover{transform:scale(1.08);border-color:#38bdf8}",
    ".fab.busy{border-color:#ff3b30}",
    ".ring{position:absolute;inset:-3px;border-radius:50%;border:3px solid transparent;",
    "border-top-color:#ff3b30;animation:spin 1s linear infinite;display:none}",
    ".fab.busy .ring{display:block}",
    "@keyframes spin{to{transform:rotate(360deg)}}",
    ".panel{position:fixed;right:18px;bottom:160px;width:330px;max-height:70vh;overflow-y:auto;",
    "background:#171d27;color:#e8edf4;border:1px solid #2a3342;border-radius:16px;padding:16px;",
    "box-shadow:0 14px 44px rgba(0,0,0,.55);z-index:2147483647;display:none;font-size:13px;line-height:1.6}",
    ".panel.show{display:block}",
    ".hd{display:flex;align-items:center;gap:8px;margin-bottom:10px}",
    ".hd .ic{width:26px;height:26px;flex:0 0 auto}",
    ".hd b{font-size:13px}",
    ".x{margin-left:auto;background:none;border:0;color:#94a3b8;font-size:17px;cursor:pointer;line-height:1}",
    ".ttl{font-size:12.5px;color:#cbd5e1;margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:2;",
    "-webkit-box-orient:vertical;overflow:hidden}",
    ".lbl{display:block;font-size:11px;color:#94a3b8;margin:12px 0 6px}",
    "select{width:100%;padding:8px 10px;border-radius:9px;background:#0f141c;color:#e8edf4;",
    "border:1px solid #2a3342;font-size:12.5px}",
    ".seg{display:flex;gap:6px;flex-wrap:wrap}",
    ".sb{flex:1;min-width:60px;padding:7px 8px;border-radius:9px;border:1px solid #2a3342;background:#0f141c;",
    "color:#94a3b8;font-size:12px;font-weight:700;cursor:pointer}",
    ".sb:hover{color:#e8edf4}",
    ".sb.on{background:#ff3b30;border-color:#ff3b30;color:#fff}",
    ".go{width:100%;margin-top:14px;padding:11px;border-radius:10px;border:0;background:#ff3b30;color:#fff;",
    "font-size:14px;font-weight:800;cursor:pointer}",
    ".go:hover{filter:brightness(1.1)}",
    ".go:disabled{opacity:.55;cursor:progress}",
    ".msg{margin:10px 0 0;font-size:11.5px;color:#94a3b8;word-break:break-all}",
    ".msg.err{color:#ff6b61}.msg.ok{color:#34d399}",
    ".bar{height:9px;background:#0f141c;border:1px solid #2a3342;border-radius:99px;overflow:hidden;margin-top:10px;display:none}",
    ".bar.show{display:block}",
    ".fill{height:100%;width:0;background:linear-gradient(90deg,#ff3b30,#ff8a65);transition:width .25s}",
    ".links{margin:10px 0 0;padding:0;list-style:none}",
    ".links li{margin-top:6px}",
    ".links a{color:#38bdf8;text-decoration:none;font-size:11.5px;word-break:break-all}",
    ".foot{margin-top:12px;display:flex;gap:8px}",
    ".foot button,.foot a{flex:1;text-align:center;padding:7px;border-radius:9px;border:1px solid #2a3342;",
    "background:transparent;color:#94a3b8;font-size:11.5px;cursor:pointer;text-decoration:none}",
    ".foot button:hover,.foot a:hover{color:#e8edf4;border-color:#38bdf8}"
  ].join("");

  var host, root, fab, panel, els = {};

  function build() {
    host = document.createElement("div");
    host.id = HOST_ID;
    root = host.attachShadow({ mode: "open" });

    var style = document.createElement("style");
    style.textContent = CSS;
    root.appendChild(style);

    fab = document.createElement("div");
    fab.className = "fab";
    fab.title = "小柯機器人：下載這部影片";
    fab.innerHTML = '<div class="ring"></div>' + ROBOT_SVG;
    fab.addEventListener("click", togglePanel);
    root.appendChild(fab);

    panel = document.createElement("div");
    panel.className = "panel";
    panel.innerHTML =
      '<div class="hd"><div class="ic">' + ROBOT_SVG + '</div><b>小柯機器人 下載工具</b>' +
      '<button class="x" title="關閉">✕</button></div>' +
      '<p class="ttl" id="ttl">讀取影片資訊中…</p>' +
      '<label class="lbl">分派到哪個平台</label><select id="target"></select>' +
      '<label class="lbl">下載範圍</label><div class="seg" id="scope"></div>' +
      '<label class="lbl">檔案格式</label><div class="seg" id="mode">' +
      '<button class="sb on" data-v="mp4">MP4 影片</button>' +
      '<button class="sb" data-v="mp3">MP3 音樂</button></div>' +
      '<label class="lbl" id="qlbl">解析度</label><div class="seg" id="quality"></div>' +
      '<button class="go" id="go">開始下載</button>' +
      '<div class="bar" id="bar"><div class="fill" id="fill"></div></div>' +
      '<p class="msg" id="msg"></p><ul class="links" id="links"></ul>' +
      '<div class="foot"><a id="full" target="_blank" rel="noopener">完整介面</a>' +
      '<button id="opt">平台設定</button></div>';
    root.appendChild(panel);

    ["ttl", "target", "scope", "mode", "quality", "qlbl", "go", "bar", "fill", "msg", "links", "full", "opt"]
      .forEach(function (id) { els[id] = root.getElementById(id); });

    panel.querySelector(".x").addEventListener("click", function () { setOpen(false); });
    els.opt.addEventListener("click", function () { send({ type: "openSettings" }); });
    els.go.addEventListener("click", startDownload);
    els.mode.addEventListener("click", function (e) {
      var b = e.target.closest(".sb"); if (!b) return;
      S.mode = b.dataset.v;
      paint(els.mode, S.mode);
      var video = S.mode === "mp4";
      els.quality.style.display = video ? "" : "none";
      els.qlbl.style.display = video ? "" : "none";
      save();
    });
    els.quality.addEventListener("click", function (e) {
      var b = e.target.closest(".sb"); if (!b) return;
      S.quality = parseInt(b.dataset.v, 10);
      paint(els.quality, String(S.quality));
      save();
    });
    els.scope.addEventListener("click", function (e) {
      var b = e.target.closest(".sb"); if (!b) return;
      S.scope = b.dataset.v;
      paint(els.scope, S.scope);
      loadInfo();
    });
    els.target.addEventListener("change", function () {
      S.base = els.target.value;
      chrome.storage.sync.set({ activeId: els.target.selectedOptions[0].dataset.id });
      els.full.href = S.base + "/";
      loadInfo();
    });

    (document.body || document.documentElement).appendChild(host);
  }

  function paint(box, value) {
    box.querySelectorAll(".sb").forEach(function (b) {
      b.classList.toggle("on", b.dataset.v === String(value));
    });
  }

  function say(text, cls) {
    els.msg.textContent = text || "";
    els.msg.className = "msg" + (cls ? " " + cls : "");
  }

  function setOpen(on) {
    S.open = on;
    panel.classList.toggle("show", on);
    if (on) loadInfo();
  }

  function togglePanel() { setOpen(!S.open); }

  function save() {
    chrome.storage.sync.set({ mode: S.mode, quality: S.quality });
  }

  /* ---------------------------------------------------- 載入 */

  function fillTargets() {
    var list = S.settings.targets || [];
    els.target.innerHTML = "";
    list.forEach(function (t) {
      var o = document.createElement("option");
      o.value = t.base; o.textContent = t.name; o.dataset.id = t.id;
      if (t.id === S.settings.activeId) o.selected = true;
      els.target.appendChild(o);
    });
    S.base = els.target.value || (list[0] && list[0].base) || "http://127.0.0.1:8787";
    els.full.href = S.base + "/";
  }

  function fillScope() {
    var hasList = !!listId(), hasVideo = !!videoId();
    var opts = [];
    if (hasVideo) opts.push({ v: "single", t: "這部影片" });
    if (hasList) opts.push({ v: "playlist", t: "整個播放清單" });
    if (!hasVideo && hasList) S.scope = "playlist";
    if (!hasList && S.scope === "playlist") S.scope = "single";
    els.scope.innerHTML = opts.map(function (o) {
      return '<button class="sb" data-v="' + o.v + '">' + o.t + "</button>";
    }).join("");
    paint(els.scope, S.scope);
  }

  function fillQuality(list) {
    if (!list || !list.length) list = [360, 720, 1080];
    if (list.indexOf(S.quality) < 0) S.quality = list.indexOf(1080) >= 0 ? 1080 : list[list.length - 1];
    els.quality.innerHTML = list.map(function (h) {
      return '<button class="sb" data-v="' + h + '">' + h + "p</button>";
    }).join("");
    paint(els.quality, String(S.quality));
  }

  function loadInfo() {
    if (!S.base) return;
    fillScope();
    els.links.innerHTML = "";
    els.ttl.textContent = "讀取影片資訊中…";
    say("");
    els.go.disabled = true;
    var url = targetUrl();
    send({ type: "info", base: S.base, url: url }).then(function (d) {
      if (url !== targetUrl()) return;          // 使用者中途換了頁
      S.info = d;
      els.ttl.textContent = d.type === "playlist"
        ? d.title + "（共 " + d.count + " 部）" : d.title;
      fillQuality(d.resolutions);
      els.go.disabled = false;
      say("");
    }).catch(function (e) {
      els.ttl.textContent = "讀不到影片資訊";
      say(e.message + "　（後端：" + S.base + "）", "err");
      els.go.disabled = true;
    });
  }

  /* ---------------------------------------------------- 下載 */

  function startDownload() {
    if (!S.info) return;
    var body = {
      url: targetUrl(),
      mode: S.mode,
      quality: S.mode === "mp4" ? S.quality : null,
      title: S.info.title
    };
    if (S.info.type === "playlist") {
      body.items = (S.info.entries || []).map(function (e) { return e.index; });
    }
    els.go.disabled = true;
    els.links.innerHTML = "";
    say("送出下載…");
    send({ type: "start", base: S.base, body: body }).then(function (d) {
      S.jobId = d.job_id;
      fab.classList.add("busy");
      els.bar.classList.add("show");
      poll();
      S.timer = setInterval(poll, 700);
    }).catch(function (e) {
      say(e.message, "err");
      els.go.disabled = false;
    });
  }

  function stopPolling() {
    if (S.timer) { clearInterval(S.timer); S.timer = null; }
    fab.classList.remove("busy");
  }

  function poll() {
    if (!S.jobId) return;
    send({ type: "poll", base: S.base, jobId: S.jobId }).then(function (d) {
      var j = d.job;
      els.fill.style.width = (j.percent || 0) + "%";
      var bits = [j.stage, (j.percent || 0) + "%"];
      if (j.total > 1) bits.push("第 " + j.current + "/" + j.total + " 部");
      if (j.current_title) bits.push(j.current_title);
      say(bits.join(" · "));
      if (j.status === "done") {
        stopPolling();
        say("下載完成，已存到 " + j.folder, "ok");
        els.links.innerHTML = j.files.map(function (f) {
          return '<li><a href="' + S.base + f.url + '" download>⬇ ' + f.name + "</a></li>";
        }).join("");
        els.go.disabled = false;
        send({ type: "notify", title: "下載完成", message: (S.info && S.info.title) || "" });
      } else if (j.status === "error" || j.status === "canceled") {
        stopPolling();
        say(j.error || "已取消", "err");
        els.go.disabled = false;
      }
    }).catch(function (e) {
      stopPolling();
      say(e.message, "err");
      els.go.disabled = false;
    });
  }

  /* ---------------------------------------------------- 啟動與頁面切換 */

  function refreshVisible() {
    var show = onDownloadablePage();
    fab.style.display = show ? "flex" : "none";
    if (!show) setOpen(false);
  }

  function watchNavigation() {
    var last = location.href;
    setInterval(function () {
      if (location.href === last) return;
      last = location.href;
      refreshVisible();
      if (S.open) loadInfo();
    }, 800);
    // YouTube 有時會把節點整個換掉，確保小圖示還在
    setInterval(function () {
      if (!document.getElementById(HOST_ID)) {
        (document.body || document.documentElement).appendChild(host);
      }
    }, 3000);
  }

  send({ type: "settings" }).then(function (s) {
    S.settings = s;
    S.mode = s.mode || "mp4";
    S.quality = s.quality || 1080;
    build();
    fillTargets();
    refreshVisible();
    watchNavigation();
  }).catch(function (e) {
    console.warn("[小柯] 無法讀取設定：" + e.message);
  });

  chrome.storage.onChanged.addListener(function (changes, area) {
    if (area !== "sync" || !S.settings) return;
    Object.keys(changes).forEach(function (k) { S.settings[k] = changes[k].newValue; });
    if (changes.targets || changes.activeId) fillTargets();
  });
})();
