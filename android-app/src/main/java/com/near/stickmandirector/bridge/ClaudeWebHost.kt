package com.near.stickmandirector.bridge

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import org.json.JSONObject

/**
 * Invisible WebView parked on https://claude.ai. It shares the app-wide cookie jar with the sign-in WebView, so the
 * session captured at login is live here, and every request goes out with Chromium's own TLS fingerprint.
 * All methods must be called on the main thread.
 */
class ClaudeWebHost(ctx: Context) {
    private val web = WebView(ctx.applicationContext)
    private val runner: WebRunner
    private var ready = false
    private var loading = false
    private var queued: (() -> Unit)? = null

    val userAgent: String get() = web.settings.userAgentString

    init {
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true)
        runner = WebRunner(web)
        web.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) { loading = true }
            override fun onPageFinished(view: WebView?, url: String?) {
                loading = false
                ready = Uri.parse(url ?: "").host.orEmpty().endsWith("claude.ai")
                if (ready) queued?.let { q -> queued = null; q() }
            }
        }
        web.onResume(); web.resumeTimers()
        web.loadUrl("https://claude.ai/new")
    }

    /** Runs the full completion flow. [cb] gets {status, text, error, retry_after, org} (status 0 = local failure). */
    fun complete(prompt: String, orgId: String?, timeoutMs: Long, cb: (JSONObject) -> Unit) {
        val go = { runner.run({ tag -> ClaudeWebJs.complete(tag, prompt, orgId) }, timeoutMs, cb) }
        if (ready) { go(); return }
        queued = go
        if (!loading) web.loadUrl("https://claude.ai/new")
        // If the page never becomes ready (offline / challenge), give up instead of hanging the caller.
        com.near.stickmandirector.auth.Bg.uiDelayed(25_000) {
            if (queued === go) { queued = null; cb(JSONObject().put("status", 0).put("error", "claude.ai page not ready")) }
        }
    }

    fun destroy() { queued = null; web.stopLoading(); web.destroy() }
}
