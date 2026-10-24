package com.xiaoke.youtube

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** 第一次開啟或要換後端時，填入後端網址的畫面。 */
class SetupActivity : AppCompatActivity() {

    private lateinit var input: EditText
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_setup)

        input = findViewById(R.id.input_base)
        status = findViewById(R.id.status)
        input.setText(Prefs.base(this) ?: "")

        findViewById<Button>(R.id.btn_test).setOnClickListener { test() }
        findViewById<Button>(R.id.btn_save).setOnClickListener { save() }
    }

    private fun test() {
        val typed = input.text.toString().trim()
        if (typed.isEmpty()) {
            status.text = getString(R.string.setup_empty)
            return
        }
        status.text = getString(R.string.setup_testing)
        val base = Prefs.normalize(typed)
        Thread {
            val message = try {
                val conn = (URL("$base/api/health").openConnection() as HttpURLConnection).apply {
                    connectTimeout = 6000
                    readTimeout = 6000
                }
                val body = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(body)
                "已連線 · yt-dlp " + json.optString("yt_dlp") +
                    "\n下載資料夾：" + json.optString("folder")
            } catch (e: Exception) {
                "連不上：" + (e.message ?: e.javaClass.simpleName)
            }
            runOnUiThread { status.text = message }
        }.start()
    }

    private fun save() {
        val typed = input.text.toString().trim()
        if (typed.isEmpty()) {
            status.text = getString(R.string.setup_empty)
            return
        }
        Prefs.setBase(this, typed)
        setResult(Activity.RESULT_OK)
        startActivity(Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        })
        finish()
    }
}
