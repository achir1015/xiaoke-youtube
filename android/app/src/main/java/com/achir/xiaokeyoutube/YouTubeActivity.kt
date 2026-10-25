package com.achir.xiaokeyoutube

import android.app.DownloadManager
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.view.View
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.URLUtil
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * App 內建的 YouTube：在影片右上角放「下載這個視訊」標籤（web/yt-overlay.js，跟桌面版共用）。
 * 標籤要下載時透過 XiaokeBridge 呼叫這裡，由這裡去連家裡電腦上的小柯——
 * YouTube 是 https 頁面，不能直接從網頁連到家裡的 http 服務。
 */
class YouTubeActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var frame: FrameLayout
    private var overlayJs: String? = null
    private var fullView: View? = null
    private val main = Handler(Looper.getMainLooper())

    // 把 overlay 的 __xkCall 接到 XiaokeBridge：結果非同步地用 __xkResolve 回傳
    private val glue = """
        window.__xkCall = function (m, a) {
          return new Promise(function (resolve) {
            var id = 'x' + Date.now() + Math.random().toString(36).slice(2);
            (window.__xkP = window.__xkP || {})[id] = resolve;
            XiaokeBridge.call(id, m, JSON.stringify(a || {}));
          });
        };
        window.__xkResolve = function (id, r) {
          var p = (window.__xkP || {})[id];
          if (p) { delete window.__xkP[id]; p(r); }
        };
    """.trimIndent()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        frame = FrameLayout(this).apply {
            // Android 15 起畫面預設延伸到狀態列底下，會壓到 YouTube 的標題列，讓內容避開系統列
            fitsSystemWindows = true
            setBackgroundColor(android.graphics.Color.BLACK)
        }
        web = WebView(this)
        frame.addView(web, FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        setContentView(frame)

        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
        }
        web.addJavascriptInterface(Bridge(), "XiaokeBridge")

        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                // 只在這裡面瀏覽；YouTube 會想用 intent:// 跳去開 YouTube App，攔下來
                val scheme = request?.url?.scheme ?: return true
                return scheme != "http" && scheme != "https"
            }

            override fun onPageFinished(view: WebView?, url: String?) = inject()
        }

        // 全螢幕播放：WebView 預設不支援，要自己把影片畫面掛上來
        web.webChromeClient = object : WebChromeClient() {
            override fun onShowCustomView(view: View?, callback: CustomViewCallback?) {
                fullView = view
                frame.addView(view, FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
                web.visibility = View.GONE
            }

            override fun onHideCustomView() {
                fullView?.let { frame.removeView(it) }
                fullView = null
                web.visibility = View.VISIBLE
            }
        }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                when {
                    fullView != null -> web.webChromeClient?.onHideCustomView()
                    web.canGoBack() -> web.goBack()
                    else -> finish()
                }
            }
        })

        loadOverlay()
        web.loadUrl("https://m.youtube.com/")
    }

    /** 下載標籤的腳本放在電腦的小柯上，跟桌面版用同一份 */
    private fun loadOverlay() {
        val base = Prefs.base(this) ?: return
        Thread {
            val js = try {
                (URL("$base/yt-overlay.js").openConnection() as HttpURLConnection).run {
                    connectTimeout = 4000
                    readTimeout = 8000
                    inputStream.bufferedReader().use { it.readText() }
                }
            } catch (e: Exception) {
                null
            }
            main.post {
                if (js == null) {
                    Toast.makeText(this, "連不上家裡的電腦，影片上不會出現下載標籤", Toast.LENGTH_LONG).show()
                } else {
                    overlayJs = js
                    inject()
                }
            }
        }.start()
    }

    private fun inject() {
        val js = overlayJs ?: return
        web.evaluateJavascript(glue + "\n" + js, null)
    }

    // ------------------------------------------------------------ 給下載標籤用的橋接

    inner class Bridge {
        @JavascriptInterface
        fun call(id: String, method: String, args: String) {
            Thread {
                val result = try {
                    handle(method, JSONObject(args))
                } catch (e: Exception) {
                    JSONObject().put("ok", false).put("error", e.message ?: e.javaClass.simpleName)
                }
                main.post {
                    web.evaluateJavascript(
                        "window.__xkResolve(${JSONObject.quote(id)}, $result)", null)
                }
            }.start()
        }
    }

    private fun handle(method: String, args: JSONObject): JSONObject {
        val base = Prefs.base(this) ?: return err("還沒連上家裡的電腦")
        return when (method) {
            "info" -> http("$base/api/info", JSONObject().put("url", args.optString("url")), 90_000)
            "start" -> http("$base/api/jobs", args, 30_000)
            "poll" -> http("$base/api/jobs/${args.optString("id")}", null, 15_000)
                .put("finish_label", "存到手機")
            "finish" -> saveToPhone(base, args.optString("id"))
            else -> err("不認得的指令：$method")
        }
    }

    /** 下載完成後，把電腦上的檔案交給 Android 下載管理員存進手機的「下載」資料夾 */
    private fun saveToPhone(base: String, id: String): JSONObject {
        val job = http("$base/api/jobs/$id", null, 15_000).optJSONObject("job")
            ?: return err("找不到這個下載")
        val files: JSONArray = job.optJSONArray("files") ?: JSONArray()
        val manager = getSystemService(DOWNLOAD_SERVICE) as DownloadManager
        for (i in 0 until files.length()) {
            val f = files.getJSONObject(i)
            val url = base + f.getString("url")
            val name = f.optString("name").ifEmpty { URLUtil.guessFileName(url, null, null) }
            manager.enqueue(DownloadManager.Request(Uri.parse(url))
                .setTitle(name)
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name))
        }
        main.post { Toast.makeText(this, "開始存到手機的「下載」資料夾", Toast.LENGTH_SHORT).show() }
        return JSONObject().put("ok", true)
    }

    private fun err(msg: String) = JSONObject().put("ok", false).put("error", msg)

    private fun http(url: String, body: JSONObject?, timeoutMs: Int): JSONObject {
        val conn = (URL(url).openConnection() as HttpURLConnection).apply {
            connectTimeout = 5000
            readTimeout = timeoutMs
            if (body != null) {
                requestMethod = "POST"
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                outputStream.use { it.write(body.toString().toByteArray()) }
            }
        }
        try {
            val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() } ?: "{}"
            return JSONObject(text)
        } finally {
            conn.disconnect()
        }
    }

    override fun onDestroy() {
        web.destroy()
        super.onDestroy()
    }
}
