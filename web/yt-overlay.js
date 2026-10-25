/*
 * 小柯機器人 - YouTube 影片上的「下載這個視訊」浮動標籤
 *
 * 注入到內建的 YouTube 瀏覽視窗裡（桌面版 pywebview、Android WebView 共用這一份）。
 * 跟主程式溝通一律透過 window.__xkCall(method, args) → Promise，由各平台自己提供：
 *   info  {url}                 → 影片資訊與可用畫質
 *   start {url, mode, quality…} → 開始下載，回傳 job_id
 *   poll  {id}                  → 下載進度
 *   finish{id}                  → 完成後的動作（桌面版開資料夾、Android 存到手機）
 */
(function () {
  "use strict";
  if (window.__xkOverlayLoaded) return;
  window.__xkOverlayLoaded = true;

  var call = function (method, args) {
    if (typeof window.__xkCall !== "function") return Promise.reject(new Error("小柯還沒準備好"));
    return Promise.resolve(window.__xkCall(method, args || {})).then(function (r) {
      if (r && r.ok === false) throw new Error(r.error || "發生錯誤");
      return r;
    });
  };

  /* ------------------------------------------------------------ 介面 */

  var CSS = [
    ":host{all:initial}",
    "*{box-sizing:border-box;font-family:'Microsoft JhengHei','PingFang TC','Noto Sans TC',system-ui,sans-serif}",
    ".wrap{position:fixed;z-index:2147483647;display:none;pointer-events:auto}",
    ".bar{display:flex;align-items:stretch;border:1px solid #6b7b8f;border-radius:5px;overflow:hidden;",
    "box-shadow:0 2px 8px rgba(0,0,0,.45);font-size:13px;user-select:none}",
    ".go{display:flex;align-items:center;gap:6px;padding:4px 10px;cursor:pointer;color:#0b3d91;",
    "background:linear-gradient(#ffffff,#dfe7f1);font-weight:700;white-space:nowrap;position:relative;min-width:150px}",
    ".go:hover{background:linear-gradient(#ffffff,#cfe0f5)}",
    ".tri{width:0;height:0;border-left:10px solid #16a34a;border-top:6px solid transparent;border-bottom:6px solid transparent}",
    ".fill{position:absolute;left:0;bottom:0;height:3px;background:#ff3b30;width:0;transition:width .3s}",
    ".sm{width:22px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#334155;",
    "background:linear-gradient(#ffffff,#dfe7f1);border-left:1px solid #9aa7b6;font-weight:700}",
    ".sm:hover{background:#e2e8f0}",
    ".menu{margin-top:4px;background:#fff;border:1px solid #9aa7b6;border-radius:6px;padding:6px 0;",
    "box-shadow:0 6px 20px rgba(0,0,0,.35);max-width:min(560px,92vw);display:none}",
    ".menu.show{display:block}",
    ".hd{padding:4px 14px 6px;color:#0f172a;font-weight:700;font-size:13px}",
    ".it{padding:6px 14px;color:#0f172a;font-size:13px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    ".it:hover{background:#dbeafe}",
    ".it b{color:#0b3d91;font-weight:700}",
    ".it .t{color:#64748b;font-weight:400}",
    ".tip{padding:6px 14px;color:#475569;font-size:12px;line-height:1.6;white-space:normal}",
    ".err{color:#dc2626}"
  ].join("");

  // YouTube 開了 Trusted Types，不能用 innerHTML 塞字串，所有元素都用 DOM API 建立
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { e.appendChild(c); });
    return e;
  }

  var host = document.createElement("div");
  host.id = "xk-yt-overlay";
  var root = host.attachShadow({ mode: "open" });
  root.appendChild(el("style", { text: CSS }));
  root.appendChild(el("div", { "class": "wrap", id: "wrap" }, [
    el("div", { "class": "bar" }, [
      el("div", { "class": "go", id: "go" }, [
        el("span", { "class": "tri" }),
        el("span", { id: "label", text: "下載這個視訊" }),
        el("span", { "class": "fill", id: "fill" })
      ]),
      el("div", { "class": "sm", id: "help", title: "說明", text: "?" }),
      el("div", { "class": "sm", id: "close", title: "這支影片先不要顯示", text: "✕" })
    ]),
    el("div", { "class": "menu", id: "menu" })
  ]));
  (document.body || document.documentElement).appendChild(host);

  var $ = function (id) { return root.getElementById(id); };
  var wrap = $("wrap"), menu = $("menu"), label = $("label"), fill = $("fill");

  var S = {
    hiddenFor: null,      // 使用者按 ✕ 的那支影片
    info: null,           // 目前影片的資訊
    infoFor: null,
    job: null,            // 進行中的下載
    timer: null
  };

  /* ------------------------------------------------------------ 找影片 */

  function videoId() {
    var p = new URLSearchParams(location.search);
    if (/\/watch/.test(location.pathname) && p.get("v")) return p.get("v");
    var m = location.pathname.match(/^\/(shorts|live)\/([\w-]{6,})/);
    return m ? m[2] : null;
  }

  function currentUrl() {
    var id = videoId();
    if (!id) return null;
    return /\/shorts\//.test(location.pathname)
      ? "https://www.youtube.com/shorts/" + id
      : "https://www.youtube.com/watch?v=" + id;
  }

  // 主播放器：畫面上最大、看得見的那個 <video>
  function playerRect() {
    var best = null, area = 0;
    document.querySelectorAll("video").forEach(function (v) {
      var r = v.getBoundingClientRect();
      var a = Math.max(0, r.width) * Math.max(0, r.height);
      if (a > area && r.width > 160 && r.height > 90 && r.bottom > 0 && r.top < innerHeight) {
        best = r; area = a;
      }
    });
    return best;
  }

  function place() {
    var id = videoId();
    var r = id && id !== S.hiddenFor ? playerRect() : null;
    if (!r && !S.job) { wrap.style.display = "none"; return; }
    wrap.style.display = "block";
    var w = wrap.offsetWidth || 220;
    var top = r ? Math.max(4, r.top + 8) : 8;
    var left = r ? Math.min(innerWidth - w - 6, r.right - w - 10) : innerWidth - w - 10;
    wrap.style.top = top + "px";
    wrap.style.left = Math.max(6, left) + "px";
  }

  /* ------------------------------------------------------------ 選單 */

  function qualityName(h) {
    if (h >= 2160) return h + "p 4K";
    if (h >= 1440) return h + "p 2K";
    if (h >= 1080) return h + "p Full HD";
    if (h >= 720) return h + "p HD";
    return h + "p";
  }

  function short(t) { return t.length > 34 ? t.slice(0, 34) + "…" : t; }

  function openMenu() {
    if (S.job) return;
    if (menu.classList.contains("show")) { menu.classList.remove("show"); return; }
    var url = currentUrl();
    if (!url) return;
    setMenu([el("div", { "class": "tip", text: "讀取這支影片可以下載的畫質…" })]);
    menu.classList.add("show");
    place();
    var load = S.infoFor === url && S.info ? Promise.resolve(S.info) : call("info", { url: url });
    load.then(function (d) {
      S.info = d; S.infoFor = url;
      renderMenu(url, d);
    }).catch(function (e) {
      setMenu([el("div", { "class": "tip err", text: "讀不到影片資訊：" + e.message })]);
    });
  }

  function renderMenu(url, d) {
    var title = short(d.title || "這支影片");
    var res = (d.resolutions || []).slice().sort(function (a, b) { return b - a; });
    var rows = [];
    res.forEach(function (h) {
      rows.push({ fmt: "MP4 檔案，品質 " + qualityName(h),
                  args: { url: url, mode: "mp4", quality: h, title: d.title } });
    });
    rows.push({ fmt: "MP3 音樂檔案", args: { url: url, mode: "mp3", title: d.title } });
    rows.push({ fmt: "SRT 字幕檔案（自動辨識語言）",
                args: { url: url, mode: "srt", want_srt: true, srt_lang: "auto", title: d.title } });

    var items = [el("div", { "class": "hd", text: "選擇要下載的格式" })];
    rows.forEach(function (row, i) {
      // 格式放前面、標題放後面：手機螢幕窄，被截掉的要是標題，不能是「MP4 1080p」這種關鍵字
      var it = el("div", { "class": "it" }, [
        document.createTextNode((i + 1) + ". "),
        el("b", { text: row.fmt }),
        el("span", { "class": "t", text: "　" + title })
      ]);
      it.addEventListener("click", function () { startJob(row.args); });
      items.push(it);
    });
    setMenu(items);
  }

  function setMenu(nodes) {
    while (menu.firstChild) menu.removeChild(menu.firstChild);
    nodes.forEach(function (n) { menu.appendChild(n); });
  }



  /* ------------------------------------------------------------ 下載 */

  function startJob(args) {
    menu.classList.remove("show");
    setLabel("準備下載…", 0);
    call("start", args).then(function (d) {
      S.job = { id: d.job_id, done: false };
      S.timer = setInterval(poll, 1000);
      poll();
    }).catch(function (e) { fail(e.message); });
  }

  function poll() {
    if (!S.job || S.job.done) return;
    call("poll", { id: S.job.id }).then(function (d) {
      var j = d.job || d;
      if (j.status === "done") {
        clearInterval(S.timer);
        S.job.done = true;
        setLabel("✓ 完成，點這裡" + (d.finish_label || "開啟"), 100);
      } else if (j.status === "error" || j.status === "canceled") {
        fail(j.error || "已取消");
      } else {
        var pct = Math.round(j.percent || 0);
        setLabel((j.stage || "下載中") + " " + pct + "%", pct);
      }
    }).catch(function (e) { fail(e.message); });
  }

  function fail(msg) {
    clearInterval(S.timer);
    S.job = { failed: true };
    setLabel("✗ 失敗（點這裡關閉）", 0);
    label.title = msg;
  }

  function setLabel(text, pct) {
    label.textContent = text;
    fill.style.width = (pct || 0) + "%";
    place();
  }

  function reset() {
    S.job = null;
    label.title = "";
    setLabel("下載這個視訊", 0);
  }

  $("go").addEventListener("click", function () {
    if (S.job && S.job.done) {
      var id = S.job.id;
      call("finish", { id: id }).catch(function () {});
      reset();
      return;
    }
    if (S.job && S.job.failed) { reset(); return; }
    openMenu();
  });

  $("close").addEventListener("click", function () {
    S.hiddenFor = videoId();
    menu.classList.remove("show");
    place();
  });

  $("help").addEventListener("click", function () {
    setMenu([el("div", { "class": "tip", text: "小柯機器人：點「下載這個視訊」選格式和畫質，" +
      "檔案會存到電腦的「下載 › 小柯YouTube」資料夾。按 ✕ 這支影片就先不顯示。" })]);
    menu.classList.toggle("show");
    place();
  });

  // 點選單外面就收起來
  document.addEventListener("click", function (e) {
    if (!e.composedPath().includes(host)) menu.classList.remove("show");
  }, true);

  /* ------------------------------------------------------------ 換頁 */

  // YouTube 是單頁應用，換影片不會重新載入頁面，所以定時檢查網址並重新定位
  var lastUrl = location.href;
  setInterval(function () {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      menu.classList.remove("show");
      S.info = null;
      if (S.job && (S.job.done || S.job.failed)) reset();
    }
    if (!document.documentElement.contains(host)) {
      (document.body || document.documentElement).appendChild(host);
    }
    place();
  }, 500);
  addEventListener("resize", place);
  addEventListener("scroll", place, true);
})();
