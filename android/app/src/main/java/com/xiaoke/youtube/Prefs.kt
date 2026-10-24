package com.xiaoke.youtube

import android.content.Context

/** 記住使用者設定的後端網址。 */
object Prefs {
    private const val FILE = "xiaoke"
    private const val KEY_BASE = "base"

    fun base(ctx: Context): String? =
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(KEY_BASE, null)

    fun setBase(ctx: Context, value: String) {
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_BASE, normalize(value))
            .apply()
    }

    /** 補上 http:// 並去掉結尾的斜線，使用者就不用在意格式。 */
    fun normalize(value: String): String {
        var v = value.trim().trimEnd('/')
        if (!v.startsWith("http://") && !v.startsWith("https://")) {
            v = "http://$v"
        }
        return v
    }
}
