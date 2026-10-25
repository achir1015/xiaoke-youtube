package com.achir.xiaokeyoutube

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * 找電腦的畫面。一般使用者什麼都不用填：
 * 一打開就自動在 Wi-Fi 裡找小柯，只找到一台就直接連上；
 * 找到多台才請使用者點一台；手動輸入網址收在「進階」裡。
 */
class SetupActivity : AppCompatActivity() {

    companion object {
        /** 從主畫面過來、因為原本的電腦連不上 */
        const val EXTRA_LOST = "lost"
        /** 使用者自己按「後端設定」進來：一律列出來讓他選，不自動跳回去 */
        const val EXTRA_PICK = "pick"
        /** 從 YouTube 分享進來的影片網址，連上電腦後要接著處理 */
        const val EXTRA_SHARED = "shared"
    }

    private lateinit var status: TextView
    private lateinit var progress: ProgressBar
    private lateinit var hint: TextView
    private lateinit var list: LinearLayout
    private lateinit var rescan: Button
    private lateinit var manualBox: View
    private lateinit var input: EditText
    private lateinit var manualStatus: TextView

    @Volatile
    private var scanning = false

    private val picking by lazy { intent.getBooleanExtra(EXTRA_PICK, false) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_setup)

        status = findViewById(R.id.find_status)
        progress = findViewById(R.id.find_progress)
        hint = findViewById(R.id.find_hint)
        list = findViewById(R.id.found_list)
        rescan = findViewById(R.id.btn_rescan)
        manualBox = findViewById(R.id.manual_box)
        input = findViewById(R.id.input_base)
        manualStatus = findViewById(R.id.status)

        input.setText(Prefs.base(this) ?: "")
        rescan.setOnClickListener { startScan() }
        findViewById<View>(R.id.btn_manual).setOnClickListener {
            manualBox.visibility = if (manualBox.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        }
        findViewById<Button>(R.id.btn_test).setOnClickListener { testManual() }
        findViewById<Button>(R.id.btn_save).setOnClickListener { saveManual() }

        startScan()
    }

    // ------------------------------------------------------------ 自動尋找

    private fun startScan() {
        if (scanning) return
        scanning = true
        status.text = getString(
            if (intent.getBooleanExtra(EXTRA_LOST, false)) R.string.find_lost else R.string.find_searching)
        progress.visibility = View.VISIBLE
        hint.visibility = View.GONE
        rescan.visibility = View.GONE
        list.removeAllViews()

        if (Discovery.localIps().isEmpty()) {
            scanning = false
            showMessage(getString(R.string.find_no_wifi), getString(R.string.find_no_wifi_hint))
            return
        }

        Thread {
            // 先試上次用的那台：IP 沒變時一秒內就好，不必掃整個網段。
            // 使用者是要「換一台」時才掃全部。
            val saved = if (picking) null else Prefs.base(this)?.let { Discovery.probe(it, 1500) }
            val found = if (saved != null) listOf(saved) else Discovery.scan()
            runOnUiThread {
                scanning = false
                if (!isFinishing && !isDestroyed) showResult(found)
            }
        }.start()
    }

    private fun showResult(found: List<Discovery.Found>) {
        when {
            found.isEmpty() -> showMessage(getString(R.string.find_none), getString(R.string.find_none_hint))
            found.size == 1 && !picking -> {
                // 只有一台就直接連上，使用者完全不用操作
                progress.visibility = View.VISIBLE
                status.text = getString(R.string.find_one, label(found[0]))
                Handler(Looper.getMainLooper()).postDelayed({ connect(found[0]) }, 700)
            }
            else -> {
                progress.visibility = View.GONE
                status.text = getString(R.string.find_many, found.size)
                val current = Prefs.base(this)
                found.forEach { f ->
                    val inUse = if (f.base == current) "（使用中）" else ""
                    list.addView(Button(this).apply {
                        isAllCaps = false
                        textSize = 15f
                        text = "💻  ${label(f)}$inUse\n${f.base.removePrefix("http://")}"
                        setOnClickListener { connect(f) }
                    })
                }
                rescan.visibility = View.VISIBLE
            }
        }
    }

    private fun showMessage(title: String, detail: String) {
        progress.visibility = View.GONE
        status.text = title
        hint.text = detail
        hint.visibility = View.VISIBLE
        rescan.visibility = View.VISIBLE
    }

    private fun label(f: Discovery.Found) = f.host.ifEmpty { f.base.removePrefix("http://") }

    private fun connect(f: Discovery.Found) {
        if (isFinishing) return
        Prefs.setBase(this, f.base)
        openMain()
    }

    private fun openMain() {
        startActivity(Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            intent.getStringExtra(EXTRA_SHARED)?.let {
                action = Intent.ACTION_SEND
                type = "text/plain"
                putExtra(Intent.EXTRA_TEXT, it)
            }
        })
        finish()
    }

    // ------------------------------------------------------------ 進階：手動輸入

    private fun testManual() {
        val typed = input.text.toString().trim()
        if (typed.isEmpty()) {
            manualStatus.text = getString(R.string.setup_empty)
            return
        }
        manualStatus.text = getString(R.string.setup_testing)
        val base = Prefs.normalize(typed)
        Thread {
            val f = Discovery.probe(base, 5000)
            runOnUiThread {
                manualStatus.text = if (f != null) "已連線：${label(f)}" else "連不上這個網址"
            }
        }.start()
    }

    private fun saveManual() {
        val typed = input.text.toString().trim()
        if (typed.isEmpty()) {
            manualStatus.text = getString(R.string.setup_empty)
            return
        }
        // 先測過才存：存了一個連不上的網址，之後每次打開都會白跑一趟
        manualStatus.text = getString(R.string.setup_testing)
        val base = Prefs.normalize(typed)
        Thread {
            val f = Discovery.probe(base, 5000)
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (f != null) {
                    Prefs.setBase(this, base)
                    openMain()
                } else {
                    manualStatus.text = "連不上這個網址，沒有儲存。請確認網址，或改用上面的自動尋找。"
                }
            }
        }.start()
    }
}
