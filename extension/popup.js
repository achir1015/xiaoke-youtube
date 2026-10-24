/* 小柯機器人 - 下載平台設定 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  function load() {
    return chrome.storage.sync.get({
      targets: [{ id: "local", name: "這台電腦", base: "http://127.0.0.1:8787" }],
      activeId: "local"
    });
  }

  function send(msg) {
    return new Promise(function (resolve, reject) {
      chrome.runtime.sendMessage(msg, function (res) {
        if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
        if (!res || !res.ok) return reject(new Error((res && res.error) || "沒有回應"));
        resolve(res.data);
      });
    });
  }

  function render(s) {
    var ul = $("list");
    ul.innerHTML = "";
    s.targets.forEach(function (t) {
      var li = document.createElement("li");

      var row = document.createElement("div");
      row.className = "row";
      var r = document.createElement("input");
      r.type = "radio"; r.name = "active"; r.checked = t.id === s.activeId;
      r.addEventListener("change", function () {
        chrome.storage.sync.set({ activeId: t.id });
      });
      var nm = document.createElement("span");
      nm.className = "nm"; nm.textContent = t.name;
      row.appendChild(r); row.appendChild(nm);

      var base = document.createElement("div");
      base.className = "base"; base.textContent = t.base;

      var st = document.createElement("div");
      st.className = "st";

      var acts = document.createElement("div");
      acts.className = "acts";
      var test = document.createElement("button");
      test.textContent = "測試連線";
      test.addEventListener("click", function () {
        st.textContent = "檢查中…"; st.className = "st";
        send({ type: "health", base: t.base }).then(function (d) {
          st.textContent = "已連線 · yt-dlp " + d.yt_dlp;
          st.className = "st ok";
        }).catch(function (e) {
          st.textContent = e.message;
          st.className = "st err";
        });
      });
      var open = document.createElement("button");
      open.textContent = "開啟介面";
      open.addEventListener("click", function () {
        chrome.tabs.create({ url: t.base.replace(/\/+$/, "") + "/" });
      });
      acts.appendChild(test); acts.appendChild(open);

      if (s.targets.length > 1) {
        var del = document.createElement("button");
        del.textContent = "刪除";
        del.addEventListener("click", function () {
          var left = s.targets.filter(function (x) { return x.id !== t.id; });
          var active = s.activeId === t.id ? left[0].id : s.activeId;
          chrome.storage.sync.set({ targets: left, activeId: active }, refresh);
        });
        acts.appendChild(del);
      }

      li.appendChild(row); li.appendChild(base); li.appendChild(st); li.appendChild(acts);
      ul.appendChild(li);
    });
  }

  function refresh() { load().then(render); }

  $("add").addEventListener("click", function () {
    var name = $("name").value.trim();
    var base = $("base").value.trim();
    if (!name || !base) { alert("請填名稱與網址"); return; }
    if (!/^https?:\/\//.test(base)) base = "http://" + base;
    load().then(function (s) {
      s.targets.push({ id: "t" + Date.now().toString(36), name: name, base: base.replace(/\/+$/, "") });
      chrome.storage.sync.set({ targets: s.targets }, function () {
        $("name").value = ""; $("base").value = "";
        refresh();
      });
    });
  });

  refresh();
})();
