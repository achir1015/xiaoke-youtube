/* 小柯機器人 YouTube 下載工具 - 網頁前端 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var LS_KEY = "xk_yt_api_base";
  var DEFAULT_BASE = "http://127.0.0.1:8787";

  // 由後端自己服務這個頁面時用同源，否則用上次設定／預設值
  var servedByBackend = /^https?:$/.test(location.protocol) && location.port === "8787";
  var apiBase = servedByBackend ? location.origin
    : (localStorage.getItem(LS_KEY) || DEFAULT_BASE);

  var state = {
    info: null, mode: "mp4", quality: null, jobId: null, timer: null,
    stt: null, installTimer: null
  };

  /* ---------------------------------------------------------- 小工具 */

  function api(path) { return apiBase.replace(/\/+$/, "") + path; }

  function post(path, body) {
    return fetch(api(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    }).then(readJson);
  }

  function get(path) { return fetch(api(path)).then(readJson); }

  function readJson(r) {
    return r.json().catch(function () {
      throw new Error("後端回應無法解析（HTTP " + r.status + "）");
    }).then(function (d) {
      if (!r.ok || d.ok === false) throw new Error(d.error || ("HTTP " + r.status));
      return d;
    });
  }

  function say(el, msg, cls) {
    el.textContent = msg || "";
    el.className = "status" + (cls ? " " + cls : "");
  }

  function fmtDur(s) {
    if (!s && s !== 0) return "";
    s = Math.round(s);
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
    var p = function (n) { return n < 10 ? "0" + n : "" + n; };
    return h ? h + ":" + p(m) + ":" + p(x) : m + ":" + p(x);
  }

  function fmtSize(b) {
    if (!b) return "";
    var u = ["B", "KB", "MB", "GB"], i = 0;
    while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
    return b.toFixed(b < 10 && i > 0 ? 1 : 0) + " " + u[i];
  }

  function fmtSpeed(bps) { return bps ? fmtSize(bps) + "/s" : ""; }

  function show(id, on) { $(id).hidden = !on; }

  /* ---------------------------------------------------------- 設定 */

  $("api-base").value = apiBase;
  if (servedByBackend) $("api-base").disabled = true;

  $("btn-settings").addEventListener("click", function () {
    var p = $("panel-settings");
    p.hidden = !p.hidden;
    if (!p.hidden) checkHealth();
  });

  $("api-base").addEventListener("change", function () {
    apiBase = $("api-base").value.trim() || DEFAULT_BASE;
    localStorage.setItem(LS_KEY, apiBase);
    checkHealth();
  });

  $("btn-test").addEventListener("click", checkHealth);

  function checkHealth() {
    apiBase = $("api-base").value.trim() || DEFAULT_BASE;
    say($("health"), "檢查中…", "busy");
    get("/api/health").then(function (d) {
      say($("health"), "已連線 · yt-dlp " + d.yt_dlp + " · 存到 " + d.folder, "ok");
      loadStt();
    }).catch(function (e) {
      say($("health"), "連不上後端：" + e.message, "err");
    });
  }

  /* ---------------------------------------------------------- 解析 */

  $("btn-parse").addEventListener("click", doParse);
  $("url").addEventListener("keydown", function (e) {
    if (e.key === "Enter") doParse();
  });

  function doParse() {
    var url = $("url").value.trim();
    if (!url) { say($("parse-msg"), "請先貼上 YouTube 網址", "err"); return; }
    stopPolling();
    show("panel-media", false);
    show("panel-progress", false);
    show("panel-done", false);
    $("btn-parse").disabled = true;
    say($("parse-msg"), "正在解析…", "busy");

    post("/api/info", { url: url }).then(function (d) {
      state.info = d;
      say($("parse-msg"), "", "");
      renderMedia(d);
      show("panel-media", true);
    }).catch(function (e) {
      say($("parse-msg"), e.message + "（後端網址：" + apiBase + "）", "err");
    }).then(function () {
      $("btn-parse").disabled = false;
    });
  }

  function renderMedia(d) {
    $("thumb").src = d.thumbnail || "icon.svg";
    $("media-title").textContent = d.title;
    var sub = [];
    if (d.uploader) sub.push(d.uploader);
    if (d.type === "playlist") sub.push("播放清單 · 共 " + d.count + " 部");
    else if (d.duration) sub.push("長度 " + fmtDur(d.duration));
    $("media-sub").textContent = sub.join(" · ");

    renderQuality(d.resolutions || []);
    applyMode();
    if (d.type === "playlist") {
      renderPlaylist(d.entries || []);
      show("playlist-block", true);
    } else {
      show("playlist-block", false);
    }
  }

  function renderQuality(list) {
    var box = $("quality-group");
    box.innerHTML = "";
    if (!list.length) list = [360, 720, 1080];
    var prefer = list.indexOf(1080) >= 0 ? 1080 : list[list.length - 1];
    list.forEach(function (h) {
      var b = document.createElement("button");
      b.className = "seg-btn" + (h === prefer ? " is-on" : "");
      b.textContent = h + "p";
      b.dataset.q = h;
      b.addEventListener("click", function () {
        box.querySelectorAll(".seg-btn").forEach(function (x) { x.classList.remove("is-on"); });
        b.classList.add("is-on");
        state.quality = h;
      });
      box.appendChild(b);
    });
    state.quality = prefer;
  }

  function renderPlaylist(entries) {
    var ul = $("pl-list");
    ul.innerHTML = "";
    entries.forEach(function (e) {
      var li = document.createElement("li");
      var lab = document.createElement("label");
      lab.className = "pl-item";
      var cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = true;
      cb.value = e.index;
      cb.addEventListener("change", updateCount);
      var idx = document.createElement("span");
      idx.className = "pl-idx";
      idx.textContent = e.index + ".";
      var t = document.createElement("span");
      t.className = "pl-title";
      t.textContent = e.title;
      t.title = e.title;
      var dur = document.createElement("span");
      dur.className = "pl-dur";
      dur.textContent = fmtDur(e.duration);
      lab.appendChild(cb); lab.appendChild(idx); lab.appendChild(t); lab.appendChild(dur);
      li.appendChild(lab);
      ul.appendChild(li);
    });
    $("all-count").textContent = entries.length;
    updateCount();
  }

  function boxes() { return Array.prototype.slice.call($("pl-list").querySelectorAll("input")); }
  function updateCount() {
    $("sel-count").textContent = boxes().filter(function (c) { return c.checked; }).length;
  }

  $("btn-all").addEventListener("click", function () {
    boxes().forEach(function (c) { c.checked = true; }); updateCount();
  });
  $("btn-none").addEventListener("click", function () {
    boxes().forEach(function (c) { c.checked = false; }); updateCount();
  });
  $("btn-invert").addEventListener("click", function () {
    boxes().forEach(function (c) { c.checked = !c.checked; }); updateCount();
  });

  /* ---------------------------------------------------------- 格式 */

  $("mode-group").addEventListener("click", function (ev) {
    var b = ev.target.closest(".seg-btn");
    if (!b) return;
    $("mode-group").querySelectorAll(".seg-btn").forEach(function (x) { x.classList.remove("is-on"); });
    b.classList.add("is-on");
    state.mode = b.dataset.mode;
    applyMode();
  });

  function applyMode() {
    var srtOnly = state.mode === "srt";
    show("quality-block", state.mode === "mp4");
    show("srt-toggle-wrap", !srtOnly);
    $("btn-download").textContent = srtOnly ? "開始產生字幕" : "開始下載";
    refreshSrtPanel();
  }

  /* ---------------------------------------------------------- 語音轉文字 */

  function wantSrt() {
    return state.mode === "srt" || $("srt-toggle").checked;
  }

  function refreshSrtPanel() {
    var ready = state.stt && state.stt.available;
    show("srt-install", !ready);
    show("srt-opts", !!ready && wantSrt());
    if (ready) updateSrtHint();
  }

  function updateSrtHint() {
    var model = $("srt-model").value;
    var got = (state.stt.downloaded || []).indexOf(model) >= 0;
    $("srt-hint").textContent = got
      ? "辨識在這台後端上跑，不會把影片送到外部服務。"
      : "第一次使用這個模型會先下載模型檔，請耐心等候。";
  }

  function loadStt() {
    return get("/api/stt").then(function (d) {
      state.stt = d;
      var lang = $("srt-lang");
      if (!lang.options.length) {
        d.languages.forEach(function (l) {
          var o = document.createElement("option");
          o.value = l.code; o.textContent = l.name;
          if (l.code === "zh-TW") o.selected = true;
          lang.appendChild(o);
        });
        d.models.forEach(function (m) {
          var o = document.createElement("option");
          o.value = m.code; o.textContent = m.name;
          if (m.code === d.default_model) o.selected = true;
          $("srt-model").appendChild(o);
        });
      }
      refreshSrtPanel();
      return d;
    }).catch(function () { /* 後端還沒連上時先不顯示 */ });
  }

  $("srt-toggle").addEventListener("change", refreshSrtPanel);
  $("srt-model").addEventListener("change", updateSrtHint);

  $("btn-install-stt").addEventListener("click", function () {
    $("btn-install-stt").disabled = true;
    say($("srt-install-msg"), "開始安裝，請稍候（約需幾分鐘）…", "busy");
    post("/api/stt/install").then(function () {
      state.installTimer = setInterval(pollInstall, 2000);
    }).catch(function (e) {
      say($("srt-install-msg"), e.message, "err");
      $("btn-install-stt").disabled = false;
    });
  });

  function pollInstall() {
    get("/api/stt").then(function (d) {
      state.stt = d;
      var ins = d.install || {};
      if (d.available || ins.status === "done") {
        clearInterval(state.installTimer);
        say($("srt-install-msg"), "安裝完成，可以產生字幕了", "ok");
        loadStt();
      } else if (ins.status === "error") {
        clearInterval(state.installTimer);
        say($("srt-install-msg"), "安裝失敗：" + ins.error, "err");
        $("btn-install-stt").disabled = false;
      }
    }).catch(function () {});
  }

  /* ---------------------------------------------------------- 下載 */

  $("btn-download").addEventListener("click", function () {
    if (!state.info) return;
    var body = {
      url: $("url").value.trim(),
      mode: state.mode,
      quality: state.mode === "mp4" ? state.quality : null,
      title: state.info.title
    };
    if (wantSrt()) {
      body.want_srt = true;
      body.srt_lang = $("srt-lang").value;
      body.srt_model = $("srt-model").value;
    }
    if (state.info.type === "playlist") {
      var sel = boxes().filter(function (c) { return c.checked; })
        .map(function (c) { return parseInt(c.value, 10); });
      if (!sel.length) { alert("請至少勾選一部影片"); return; }
      body.items = sel;
    }
    $("btn-download").disabled = true;
    post("/api/jobs", body).then(function (d) {
      state.jobId = d.job_id;
      show("panel-progress", true);
      show("panel-done", false);
      setProgress({ stage: "準備中", percent: 0, item_percent: 0, current: 1, total: body.items ? body.items.length : 1 });
      $("panel-progress").scrollIntoView({ behavior: "smooth", block: "nearest" });
      startPolling();
    }).catch(function (e) {
      alert("無法開始下載：" + e.message);
    }).then(function () {
      $("btn-download").disabled = false;
    });
  });

  function startPolling() {
    stopPolling();
    state.timer = setInterval(poll, 600);
    poll();
  }
  function stopPolling() {
    if (state.timer) { clearInterval(state.timer); state.timer = null; }
  }

  function poll() {
    if (!state.jobId) return;
    get("/api/jobs/" + state.jobId).then(function (d) {
      var j = d.job;
      setProgress(j);
      if (j.status === "done") { stopPolling(); finish(j); }
      else if (j.status === "error") { stopPolling(); fail(j.error); }
      else if (j.status === "canceled") { stopPolling(); fail("已取消下載"); }
    }).catch(function (e) {
      stopPolling();
      fail(e.message);
    });
  }

  function setProgress(j) {
    $("prog-stage").textContent = j.stage || "處理中";
    $("prog-pct").textContent = (j.percent || 0) + "%";
    $("bar-fill").style.width = (j.percent || 0) + "%";
    var multi = (j.total || 1) > 1;
    show("bar-item-wrap", multi);
    if (multi) $("bar-item").style.width = (j.item_percent || 0) + "%";
    var bits = [];
    if (multi) bits.push("第 " + j.current + " / " + j.total + " 部");
    if (j.current_title) bits.push(j.current_title);
    if (j.speed) bits.push(fmtSpeed(j.speed));
    if (j.eta) bits.push("剩約 " + fmtDur(j.eta));
    $("prog-detail").textContent = bits.join(" · ");
  }

  function finish(j) {
    show("panel-progress", false);
    show("panel-done", true);
    $("done-title").textContent = "下載完成 · 共 " + j.files.length + " 個檔案";
    $("done-folder").textContent = "已存到後端資料夾：" + j.folder;
    var ul = $("file-list");
    ul.innerHTML = "";
    j.files.forEach(function (f) {
      var li = document.createElement("li");
      var n = document.createElement("span");
      n.className = "fname"; n.textContent = f.name;
      var s = document.createElement("span");
      s.className = "fsize"; s.textContent = fmtSize(f.size);
      var a = document.createElement("a");
      a.href = api(f.url); a.textContent = "存到這台裝置"; a.setAttribute("download", f.name);
      li.appendChild(n); li.appendChild(s); li.appendChild(a);
      ul.appendChild(li);
    });
    $("panel-done").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function fail(msg) {
    $("prog-stage").textContent = "失敗";
    $("prog-detail").textContent = msg || "未知錯誤";
    $("prog-detail").className = "status err";
  }

  $("btn-cancel").addEventListener("click", function () {
    if (!state.jobId) return;
    post("/api/jobs/" + state.jobId + "/cancel").catch(function () {});
  });

  $("btn-again").addEventListener("click", function () {
    show("panel-done", false);
    $("url").value = "";
    $("url").focus();
  });

  /* ---------------------------------------------------------- 桌面版專屬 */

  function deskApi() {
    return (window.pywebview && window.pywebview.api) || null;
  }

  function setupDesktop() {
    var api = deskApi();
    if (!api) return;
    show("desktop-box", true);
    Promise.all([api.version(), get("/api/settings")]).then(function (res) {
      $("desk-folder").textContent =
        "版本 " + res[0].version + "　·　下載到：" + res[1].download_dir;
    }).catch(function () {});
  }

  $("btn-open-folder").addEventListener("click", function () {
    var api = deskApi();
    if (api) api.open_folder().then(function (r) {
      if (!r.ok) say($("desk-msg"), r.error, "err");
    });
  });

  $("btn-pick-folder").addEventListener("click", function () {
    var api = deskApi();
    if (!api) return;
    api.pick_folder().then(function (r) {
      if (r.canceled) return;
      if (!r.ok) { say($("desk-msg"), r.error || "無法切換資料夾", "err"); return; }
      say($("desk-msg"), "之後會下載到：" + r.download_dir, "ok");
      checkHealth();
    });
  });

  $("btn-update").addEventListener("click", function () {
    var api = deskApi();
    if (!api) return;
    say($("desk-msg"), "檢查更新中…", "busy");
    api.check_update().then(function (r) {
      if (!r.ok) { say($("desk-msg"), "檢查失敗：" + r.error, "err"); return; }
      if (r.newer) {
        say($("desk-msg"), "有新版本 " + r.latest + "（目前 " + r.current + "）" +
          (r.notes ? "：" + r.notes : "") + " — 正在開啟下載頁", "ok");
        api.open_release_page();
      } else {
        say($("desk-msg"), "已經是最新版（" + r.current + "）", "ok");
      }
    });
  });

  window.addEventListener("pywebviewready", setupDesktop);
  if (deskApi()) setupDesktop();

  /* ---------------------------------------------------------- 捷徑／PWA */

  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    navigator.serviceWorker.register("sw.js").catch(function () {});
  }

  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    show("btn-install", true);
  });

  $("btn-install").addEventListener("click", function () {
    if (!deferredPrompt) {
      alert("請用瀏覽器選單的「安裝應用程式／加到主畫面」來建立捷徑。");
      return;
    }
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function () {
      deferredPrompt = null;
      show("btn-install", false);
    });
  });

  window.addEventListener("appinstalled", function () { show("btn-install", false); });

  /* 開頁先確認後端是否活著，沒活就把設定打開 */
  get("/api/health").then(function (d) {
    say($("health"), "已連線 · yt-dlp " + d.yt_dlp, "ok");
    loadStt();
  }).catch(function () {
    show("panel-settings", true);
    say($("health"), "還沒連上後端，請確認後端已啟動或填入網址", "err");
  });
})();
