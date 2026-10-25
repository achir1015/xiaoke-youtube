package com.achir.xiaokeyoutube

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.Inet4Address
import java.net.NetworkInterface
import java.net.URL
import java.util.Collections
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * 在手機所在的 Wi-Fi 裡找開著的小柯（電腦上的桌面版或後端）。
 * 做法很單純：把同一個網段的 254 個位址都問一次 /api/health，回答自己是小柯的就是。
 */
object Discovery {

    private const val APP_ID = "小柯機器人 YouTube 下載工具"
    private val PORTS = listOf(8787)

    data class Found(val base: String, val host: String)

    /** 手機在區域網路上的 IPv4（通常就是 Wi-Fi 那張網卡）。 */
    fun localIps(): List<String> = try {
        Collections.list(NetworkInterface.getNetworkInterfaces())
            .filter { it.isUp && !it.isLoopback }
            .flatMap { Collections.list(it.inetAddresses) }
            .filterIsInstance<Inet4Address>()
            .filter { it.isSiteLocalAddress }
            .mapNotNull { it.hostAddress }
            .distinct()
    } catch (e: Exception) {
        emptyList()
    }

    /** 連得上而且確實是小柯，就回傳它的資訊。 */
    fun probe(base: String, timeoutMs: Int = 700): Found? = try {
        val conn = (URL("$base/api/health").openConnection() as HttpURLConnection).apply {
            connectTimeout = timeoutMs
            readTimeout = timeoutMs * 2
        }
        try {
            if (conn.responseCode != 200) null else {
                val json = JSONObject(conn.inputStream.bufferedReader().use { it.readText() })
                if (json.optString("app") == APP_ID) Found(base, json.optString("host")) else null
            }
        } finally {
            conn.disconnect()
        }
    } catch (e: Exception) {
        null
    }

    /** 掃描整個網段，約 3～5 秒；找到一台就呼叫一次 onFound（在背景執行緒）。 */
    fun scan(onFound: (Found) -> Unit = {}): List<Found> {
        val targets = localIps().flatMap { ip ->
            val prefix = ip.substringBeforeLast('.')
            (1..254).flatMap { n -> PORTS.map { port -> "http://$prefix.$n:$port" } }
        }
        if (targets.isEmpty()) return emptyList()

        val found = Collections.synchronizedList(mutableListOf<Found>())
        val pool = Executors.newFixedThreadPool(48)
        targets.forEach { base ->
            pool.execute {
                probe(base)?.let {
                    found.add(it)
                    onFound(it)
                }
            }
        }
        pool.shutdown()
        pool.awaitTermination(20, TimeUnit.SECONDS)
        // 同一台電腦只留一個，名稱排序讓清單穩定
        return found.distinctBy { it.host.ifEmpty { it.base } }.sortedBy { it.host.lowercase() }
    }
}
