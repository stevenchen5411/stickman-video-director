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
import com.near.stickmandirector.bridge.ClaudeWebJs
import com.near.stickmandirector.bridge.WebRunner
import com.near.stickmandirector.model.AuthEndpoints
import org.json.JSONArray
import com.near.stickmandirector.ui.Ui

/** What the sniffer hands back. [cookieHeader] is the live jar for the site; [orgId] is set once /api/organizations answered. */
data class SessionCapture(val cookies: Map<String, String>, val cookieHeader: String, val userAgent: String, val orgId: String?)

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
    private val onCaptured: (SessionCapture) -> Unit,
    private val onFallbackToKey: () -> Unit,
) : Dialog(activity, android.R.style.Theme_DeviceDefault_NoActionBar) {

    private lateinit var web: WebView
    private lateinit var runner: WebRunner
    private var verifying = false
    private var verifyTries = 0
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
        runner = WebRunner(web)
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
            if (found.isNotEmpty() && sessionOk) {
                if (ep.provider == "claude") verifyClaude(status) else finish(status, null)
                if (done) return
            }
            Bg.uiDelayed(1500) { tick() }
        }
        tick()
    }

    /**
     * Force-warm + verify inside the WebView before "captured" turns green: GET /api/organizations with the live
     * cookie jar. A 200 proves the session works and makes Cloudflare issue cf_clearance if it wants one for this network.
     */
    private fun verifyClaude(status: android.widget.TextView) {
        if (verifying) return
        val host = Uri.parse(web.url ?: "").host.orEmpty()
        if (!host.endsWith("claude.ai")) { status.text = "Waiting for claude.ai..."; return }
        verifying = true
        status.text = "Verifying session..."
        runner.run({ tag -> ClaudeWebJs.listOrgs(tag) }, 20_000) { res ->
            verifying = false
            if (!polling || done) return@run          // dialog closed while verifying
            val code = res.optInt("status")
            if (code == 200) {
                val org = runCatching {
                    val arr = JSONArray(res.optString("body"))
                    var pick: String? = null
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        val caps = o.optJSONArray("capabilities")
                        val chat = caps != null && (0 until caps.length()).any { caps.optString(it) == "chat" }
                        if (pick == null || chat) pick = o.optString("uuid").ifBlank { null } ?: pick
                        if (chat) break
                    }
                    pick
                }.getOrNull()
                if (org != null) finish(status, org)
                else status.text = "Signed in, but no organization found on this account"
            } else {
                verifyTries++
                status.text = when {
                    code == 401 || code == 403 -> "Not verified yet (HTTP $code). If a check page is showing, finish it; try again shortly."
                    else -> "Could not verify (${res.optString("error", "HTTP $code")}). Retrying..."
                }
                if (verifyTries >= 40) status.text = "Verification keeps failing (HTTP $code). Close and retry, or use an API key."
            }
        }
    }

    private fun finish(status: android.widget.TextView, orgId: String?) {
        done = true
        val cm = CookieManager.getInstance()
        cm.flush()
        val header = ep.cookieDomains.firstNotNullOfOrNull { d -> cm.getCookie("https://" + d.trimStart('.'))?.takeIf { it.isNotBlank() } }.orEmpty()
        val jar = if (ep.provider == "claude") parseHeader(header) else capture()
        val cf = if (ep.cloudflareCookieNames.all { jar.containsKey(it) }) "" else " (no ${ep.cloudflareCookieNames.joinToString()} issued; the app bridge covers that)"
        status.text = "Session verified$cf"
        onCaptured(SessionCapture(jar, header, web.settings.userAgentString, orgId))
        dismiss()
    }

    private fun parseHeader(h: String): Map<String, String> {
        val out = linkedMapOf<String, String>()
        for (part in h.split(";")) {
            val kv = part.trim().split("=", limit = 2)
            if (kv.size == 2 && kv[0].isNotEmpty()) out[kv[0]] = kv[1]
        }
        return out
    }

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
