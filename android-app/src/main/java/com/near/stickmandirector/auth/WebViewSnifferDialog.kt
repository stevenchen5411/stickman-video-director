package com.near.stickmandirector.auth

import android.annotation.SuppressLint
import android.app.Activity
import android.app.Dialog
import android.graphics.Color
import android.net.Uri
import android.view.Gravity
import android.view.ViewGroup
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.LinearLayout
import androidx.browser.customtabs.CustomTabsIntent
import androidx.core.graphics.Insets
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import com.near.stickmandirector.model.AuthEndpoints
import com.near.stickmandirector.ui.Ui

/**
 * Layer 3. Full-screen web sign-in that watches CookieManager for the provider's session cookie
 * (plus cf_clearance and the WebView user-agent, which Cloudflare ties together) and hands them back.
 *
 * Known limit: Google refuses OAuth inside embedded WebViews, and a Chrome Custom Tab keeps its cookies in
 * Chrome's jar, not in this WebView's. The "Google sign-in (browser tab)" button is therefore only useful
 * to complete a login in Chrome; for Gemini the reliable route is an API key (layer 4).
 */
class WebViewSnifferDialog(
    private val activity: Activity,
    private val ep: AuthEndpoints,
    private val onCaptured: (cookies: Map<String, String>, userAgent: String) -> Unit,
    private val onFallbackToKey: () -> Unit,
) : Dialog(activity, android.R.style.Theme_DeviceDefault_NoActionBar) {

    private lateinit var web: WebView
    private var polling = false
    private var done = false

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: android.os.Bundle?) {
        super.onCreate(savedInstanceState)
        window?.let { WindowCompat.setDecorFitsSystemWindows(it, false); it.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(Ui.BG)) }
        val ctx = activity
        val root = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(Ui.BG) }

        val bar = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            val p = Ui.dp(ctx, 10); setPadding(p, p, p, p)
        }
        bar.addView(Ui.text(ctx, "Sign in to ${ep.displayName}", 16f, Ui.TEXT, true),
            LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        if (ep.provider == "gemini") {
            bar.addView(Ui.button(ctx, "Browser tab", false) {
                runCatching { CustomTabsIntent.Builder().build().launchUrl(activity, Uri.parse(ep.webLoginUrl)) }
            })
        }
        bar.addView(Ui.button(ctx, "Use API key", false) { dismiss(); onFallbackToKey() })
        bar.addView(Ui.button(ctx, "Close", false) { dismiss() })
        root.addView(bar)

        val status = Ui.muted(ctx, "Log in normally. The session is captured automatically once the cookie appears.").apply {
            val p = Ui.dp(ctx, 12); setPadding(p, 0, p, p)
        }
        root.addView(status)

        web = WebView(ctx).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            CookieManager.getInstance().setAcceptCookie(true)
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)
            webViewClient = WebViewClient()
            loadUrl(ep.webLoginUrl)
        }
        root.addView(web, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))

        val frame = FrameLayout(ctx).apply { addView(root) }
        ViewCompat.setOnApplyWindowInsetsListener(frame) { v, wi ->
            val i: Insets = wi.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout() or WindowInsetsCompat.Type.ime())
            v.setPadding(i.left, i.top, i.right, i.bottom); WindowInsetsCompat.CONSUMED
        }
        setContentView(frame)
        setOnDismissListener { polling = false; web.stopLoading(); web.destroy() }
        poll(status)
    }

    override fun onBackPressed() {
        if (::web.isInitialized && web.canGoBack()) web.goBack() else dismiss()
    }

    private fun poll(status: android.widget.TextView) {
        if (polling) return
        polling = true
        fun tick() {
            if (!polling || done) return
            val found = capture()
            val sessionOk = ep.sessionCookieNames.isEmpty() || ep.sessionCookieNames.any { found.containsKey(it) }
            val cfOk = ep.cloudflareCookieNames.isEmpty() || ep.cloudflareCookieNames.all { found.containsKey(it) }
            if (found.isNotEmpty() && sessionOk) {
                status.text = if (cfOk) "Session captured" else "Session captured (no ${ep.cloudflareCookieNames.joinToString()} yet)"
                if (cfOk || ++waitedAfterSession > 6) {
                    done = true
                    CookieManager.getInstance().flush()
                    onCaptured(found, web.settings.userAgentString)
                    dismiss(); return
                }
            }
            Bg.uiDelayed(1500) { tick() }
        }
        tick()
    }

    private var waitedAfterSession = 0

    private fun capture(): Map<String, String> {
        val cm = CookieManager.getInstance()
        val wanted = (ep.sessionCookieNames + ep.cloudflareCookieNames).toSet()
        val out = linkedMapOf<String, String>()
        for (d in ep.cookieDomains) {
            val raw = cm.getCookie("https://" + d.trimStart('.')) ?: continue
            for (part in raw.split(";")) {
                val kv = part.trim().split("=", limit = 2)
                if (kv.size == 2 && (wanted.isEmpty() || kv[0] in wanted)) out[kv[0]] = kv[1]
            }
        }
        return out
    }
}
