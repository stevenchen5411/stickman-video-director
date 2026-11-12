package com.near.stickmandirector.bridge

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import com.near.stickmandirector.auth.ProvidersStore
import com.near.stickmandirector.auth.SecureStore
import com.near.stickmandirector.model.AuthMode
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.model.HealthReport
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

data class WakeResult(val sent: Boolean, val message: String)

/** HTTP + RUN_COMMAND bridge to the Termux daemon on 127.0.0.1:8775. All network methods block: call off the main thread. */
class TermuxClient(private val ctx: Context) {
    private val store = SecureStore.get(ctx)
    private val http = OkHttpClient.Builder()
        .connectTimeout(2, TimeUnit.SECONDS).readTimeout(20, TimeUnit.SECONDS).build()
    private val json = "application/json".toMediaType()

    private fun req(path: String) = Request.Builder().url(Defaults.DAEMON_URL + path)
        .header("X-Stickman-Token", store.daemonToken)

    // ------------------------------------------------------------------ HTTP
    fun health(): HealthReport = try {
        http.newCall(req("/health").build()).execute().use { r ->
            if (r.isSuccessful) HealthReport.fromJson(JSONObject(r.body!!.string()))
            else HealthReport(false, error = "HTTP ${r.code}")
        }
    } catch (t: Throwable) { HealthReport(false, error = t.message ?: t.javaClass.simpleName) }

    /** Returns the response body; throws IllegalStateException with a readable message on failure. */
    fun get(path: String): String = http.newCall(req(path).get().build()).execute().use { body(it) }

    fun post(path: String, payload: JSONObject = JSONObject()): String =
        http.newCall(req(path).post(payload.toString().toRequestBody(json)).build()).execute().use { body(it) }

    fun put(path: String, payload: JSONObject): String =
        http.newCall(req(path).put(payload.toString().toRequestBody(json)).build()).execute().use { body(it) }

    private fun body(r: okhttp3.Response): String {
        val s = r.body?.string().orEmpty()
        check(r.isSuccessful) { "daemon ${r.code}: ${s.take(200)}" }
        return s
    }

    /** Push plaintext API keys into the daemon's memory (never written to disk there). */
    fun pushKeysBlocking(): Boolean = try {
        val keys = JSONObject(ProvidersStore.runtimeKeys(ctx))
        post("/config/keys", JSONObject().put("keys", keys))
        pushSessionBlocking()
        true
    } catch (t: Throwable) { false }

    /** Push the claude.ai web session (live WebView cookie jar if present) so Termux can call it via curl_cffi. */
    fun pushSessionBlocking(): Boolean {
        val c = store.loadCred("claude") ?: return false
        if (c.mode != AuthMode.SESSION || c.cookies.isEmpty()) return false
        val live = runCatching { android.webkit.CookieManager.getInstance().getCookie("https://claude.ai") }.getOrNull()
        val header = if (!live.isNullOrBlank()) live else c.cookies.entries.joinToString("; ") { "${it.key}=${it.value}" }
        return try {
            post("/config/sessions", JSONObject().put("provider", "claude").put("cookie_header", header)
                .put("user_agent", c.userAgent ?: "").put("org_id", c.orgId ?: JSONObject.NULL)); true
        } catch (t: Throwable) { false }
    }

    // ------------------------------------------------------------------ RUN_COMMAND
    /** Fire a command in Termux's background (needs com.termux.permission.RUN_COMMAND + allow-external-apps). */
    fun runCommand(path: String, args: List<String> = emptyList(), workdir: String = Defaults.TERMUX_HOME): WakeResult {
        val i = Intent("com.termux.RUN_COMMAND").apply {
            component = ComponentName(Defaults.TERMUX_PKG, "com.termux.app.RunCommandService")
            putExtra("com.termux.RUN_COMMAND_PATH", path)
            putExtra("com.termux.RUN_COMMAND_ARGUMENTS", args.toTypedArray())
            putExtra("com.termux.RUN_COMMAND_WORKDIR", workdir)
            putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)
        }
        return try {
            try { ctx.startService(i) } catch (e: IllegalStateException) { ctx.startForegroundService(i) }
            WakeResult(true, "Command sent to Termux")
        } catch (e: SecurityException) {
            WakeResult(false, "RUN_COMMAND not granted (or Termux allow-external-apps is off)")
        } catch (t: Throwable) {
            WakeResult(false, t.message ?: t.javaClass.simpleName)
        }
    }

    fun termuxInstalled(): Boolean = runCatching { ctx.packageManager.getPackageInfo(Defaults.TERMUX_PKG, 0); true }.getOrDefault(false)

    /** Start the daemon, handing it this install's token. [restart] replaces a daemon running with an old token. */
    fun wake(restart: Boolean = false): WakeResult =
        runCommand(Defaults.TERMUX_BASH, buildList {
            add(Defaults.LAUNCHER); add(store.daemonToken); if (restart) add("restart")
        })

    fun wakeLock(): WakeResult = runCommand("/data/data/com.termux/files/usr/bin/termux-wake-lock")

    /**
     * Make sure a daemon that accepts our token is up. Wakes (and restarts on token mismatch) then polls /health.
     * Returns the final report; check [HealthReport.reachable] and [HealthReport.authOk].
     */
    fun ensureAwake(timeoutMs: Long = 20_000): HealthReport {
        var h = health()
        if (h.reachable && h.authOk) return h
        val w = wake(restart = h.reachable && !h.authOk)
        if (!w.sent) return h.copy(error = w.message)
        val end = System.currentTimeMillis() + timeoutMs
        while (System.currentTimeMillis() < end) {
            Thread.sleep(1000)
            h = health()
            if (h.reachable && h.authOk) { pushKeysBlocking(); return h }
        }
        return h
    }
}
