package com.achir.xiaokeyoutube

import android.app.DownloadManager
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.webkit.URLUtil
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

/**
 * 小柯機器人 YouTube 下載工具 - Android 版
 *
 * 影片實際是由後端（你的電腦或 NAS）下載，這個 App 是它的手機介面：
 * 從 YouTube App 分享過來的網址會自動帶入並開始解析。
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var errorBox: View

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (Prefs.base(this).isNullOrBlank()) {
            openSetup()
            return
        }

        setContentView(R.layout.activity_main)
        web = findViewById(R.id.web)
        errorBox = findViewById(R.id.error_box)

        setupWebView()

        findViewById<Button>(R.id.btn_settings).setOnClickListener { openSetup(pick = true) }
        findViewById<Button>(R.id.btn_reconfigure).setOnClickListener { openSetup(pick = true) }
        findViewById<Button>(R.id.btn_retry).setOnClickListener { load(intent) }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (web.canGoBack()) web.goBack() else finish()
            }
        })

        load(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        if (this::web.isInitialized) load(intent)
    }

    private fun setupWebView() {
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true          // 網頁用 localStorage 記設定
            mediaPlaybackRequiresUserGesture = false
            allowFileAccess = false
            allowContentAccess = false
        }

        web.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                errorBox.visibility = View.GONE
            }

            override fun onReceivedError(
                view: WebView?, request: WebResourceRequest?, error: WebResourceError?
            ) {
                // 只有主頁面載不起來才算連不上，子資源失敗不用打擾使用者
                if (request?.isForMainFrame == true) handleLost()
            }
        }

        // 網頁上按「存到這台裝置」時，交給系統下載管理員存進手機的下載資料夾
        web.setDownloadListener { url, userAgent, contentDisposition, mimeType, _ ->
            try {
                val name = URLUtil.guessFileName(url, contentDisposition, mimeType)
                val request = DownloadManager.Request(Uri.parse(url))
                    .setTitle(name)
                    .setMimeType(mimeType)
                    .addRequestHeader("User-Agent", userAgent)
                    .setNotificationVisibility(
                        DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name)
                val manager = getSystemService(DOWNLOAD_SERVICE) as DownloadManager
                manager.enqueue(request)
                toast(getString(R.string.download_started))
            } catch (e: Exception) {
                toast(e.message ?: e.javaClass.simpleName)
            }
        }
    }

    private fun load(intent: Intent?) {
        val base = Prefs.base(this) ?: return openSetup()
        val shared = sharedUrl(intent)
        val target = if (shared != null) {
            base + "/?url=" + Uri.encode(shared)
        } else {
            "$base/"
        }
        // 先確認那台電腦還在再載入。網址錯或連不到時，WebView 常常只是一片空白、
        // 也不回報錯誤，使用者會卡住；先確認的話最多 2.5 秒就能自動去重新尋找。
        Thread {
            val alive = Discovery.probe(base, 2500) != null
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (alive) web.loadUrl(target) else openSetup(lost = true, shared = shared)
            }
        }.start()
    }

    /** 從分享或開啟連結的 Intent 取出 YouTube 網址。 */
    private fun sharedUrl(intent: Intent?): String? {
        if (intent == null) return null
        val text = when (intent.action) {
            Intent.ACTION_SEND -> intent.getStringExtra(Intent.EXTRA_TEXT)
            Intent.ACTION_VIEW -> intent.dataString
            else -> null
        } ?: return null
        // 分享過來的文字常常是「標題 + 網址」，只取網址那段
        val match = Regex("https?://\\S+").find(text)
        return (match?.value ?: text).trim().ifEmpty { null }
    }

    /**
     * 主頁面載不起來時：先確認電腦是不是真的不見了（例如換了 IP、電腦關了），
     * 是的話就自動去重新尋找；電腦還在只是頁面一時失敗，才顯示「重試」。
     * 先確認再跳，才不會在兩個畫面之間來回跳。
     */
    private fun handleLost() {
        val base = Prefs.base(this) ?: return openSetup()
        Thread {
            val alive = Discovery.probe(base, 2500) != null
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (alive) errorBox.visibility = View.VISIBLE else openSetup(lost = true)
            }
        }.start()
    }

    private fun openSetup(lost: Boolean = false, pick: Boolean = false, shared: String? = null) {
        startActivity(Intent(this, SetupActivity::class.java)
            .putExtra(SetupActivity.EXTRA_LOST, lost)
            .putExtra(SetupActivity.EXTRA_PICK, pick)
            // 從 YouTube 分享過來時，換完電腦還要接著處理那支影片
            .putExtra(SetupActivity.EXTRA_SHARED, shared ?: sharedUrl(intent)))
        finish()
    }

    private fun toast(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }
}
