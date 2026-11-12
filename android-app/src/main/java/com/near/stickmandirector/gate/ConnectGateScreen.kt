package com.near.stickmandirector.gate

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.net.Uri
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.near.stickmandirector.auth.AuthSelfHealer
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.auth.ProvidersStore
import com.near.stickmandirector.auth.SecureStore
import com.near.stickmandirector.auth.TokenRefreshWorker
import com.near.stickmandirector.auth.WebViewSnifferDialog
import com.near.stickmandirector.bridge.GitHubApiClient
import com.near.stickmandirector.bridge.TermuxClient
import com.near.stickmandirector.model.AuthResult
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.model.GitHubStatus
import com.near.stickmandirector.ui.BackScope
import com.near.stickmandirector.ui.BottomSheet
import com.near.stickmandirector.ui.Ui

/**
 * Mandatory 3-point gate. The app unlocks only when ALL pass:
 *   #1 AI: at least one provider usable      #2 Termux: daemon on 127.0.0.1:8775 accepts our token
 *   #3 GitHub: PAT valid with push access to the repo
 * Gate #2 offers "Copy 1-Line Setup" (paste into Termux) plus the diagnostics list with Fix buttons.
 */
class ConnectGateScreen(
    private val activity: Activity,
    private val back: BackScope,
    private val autoUnlock: Boolean,
    private val onUnlocked: () -> Unit,
) {
    private val ctx: Context = activity
    private val store = SecureStore.get(ctx)
    private val healer = AuthSelfHealer(ctx)
    private val diag = TermuxDiagnostics(ctx)
    private val github = GitHubApiClient(ctx)

    private val host = FrameLayout(ctx)           // root: content + modal sheet overlay
    private val content = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
    private val sheet = BottomSheet(ctx, host, back)

    private var aiOk = false
    private var termuxOk = false
    private var ghOk = false
    private var diagRows: List<DiagRow> = emptyList()
    private var ghStatus: GitHubStatus = GitHubStatus(false, message = "Not checked")
    private var busy = ""
    private var unlockedFired = false

    val view: View get() = host

    init {
        val scroll = ScrollView(ctx).apply { isFillViewport = true; addView(content) }
        host.addView(scroll, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        val p = Ui.dp(ctx, 16)
        content.setPadding(p, p, p, p * 2)
        render()
        refreshAll()
    }

    // ------------------------------------------------------------------ state
    fun refreshAll() {
        aiOk = store.usableProviders().isNotEmpty()
        Bg.io {
            val rows = diag.run()
            val health = diag.lastHealth
            val gh = if (github.hasToken()) github.verify() else GitHubStatus(false, message = "No token saved")
            Bg.ui {
                diagRows = rows
                termuxOk = health.reachable && health.authOk
                ghStatus = gh; ghOk = gh.ok
                if (termuxOk) Bg.io { TermuxClient(ctx).pushKeysBlocking() }
                render()
                maybeUnlock()
            }
        }
    }

    private fun maybeUnlock() {
        if (aiOk && termuxOk && ghOk && !unlockedFired) {
            unlockedFired = true
            TokenRefreshWorker.schedule(ctx)
            Bg.io { ProvidersStore.sync(ctx) }
            if (autoUnlock) onUnlocked()
        }
    }

    fun onPermissionResult() = refreshAll()

    fun handleAuthRedirect(uri: Uri) {
        healer.handleRedirect(uri) { r -> onAuthResult(r, uri.pathSegments.lastOrNull().orEmpty()) }
    }

    // ------------------------------------------------------------------ rendering
    private fun render() {
        content.removeAllViews()
        content.addView(Ui.title(ctx, "Connect your studio"))
        content.addView(Ui.muted(ctx, "Three connections are required before the studio unlocks.").apply { setPadding(0, 0, 0, Ui.dp(ctx, 12)) })
        content.addView(aiCard(), Ui.lp(top = 4, ctx = ctx))
        content.addView(termuxCard(), Ui.lp(top = 12, ctx = ctx))
        content.addView(githubCard(), Ui.lp(top = 12, ctx = ctx))
        val all = aiOk && termuxOk && ghOk
        content.addView(Ui.button(ctx, if (all) "Open studio" else "Complete all 3 to continue", all) { if (all) onUnlocked() },
            Ui.lp(top = 16, ctx = ctx))
        content.addView(Ui.button(ctx, "Re-check everything", false) { busy = "check"; refreshAll() }, Ui.lp(top = 8, ctx = ctx))
    }

    private fun header(n: Int, title: String, ok: Boolean): View = LinearLayout(ctx).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = android.view.Gravity.CENTER_VERTICAL
        addView(Ui.text(ctx, "$n  $title", 16f, Ui.TEXT, true), LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        addView(Ui.badge(ctx, if (ok) "READY" else "REQUIRED", if (ok) Ui.OK else Ui.WARN))
    }

    // ---- Gate 1
    private fun aiCard(): View = Ui.card(ctx).apply {
        addView(header(1, "AI provider", aiOk))
        addView(Ui.muted(ctx, "Connect at least one. Others act as automatic failover on rate limits."), Ui.lp(top = 4, ctx = ctx))
        for (c in store.allCreds()) {
            val row = LinearLayout(ctx).apply {
                orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL
            }
            val label = c.name.replaceFirstChar { it.uppercase() }
            row.addView(Ui.text(ctx, label, 14f, Ui.TEXT, true), LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            row.addView(Ui.badge(ctx, if (c.usable) c.mode.wire.uppercase() else "NOT CONNECTED", if (c.usable) Ui.OK else Ui.MUTED))
            addView(row, Ui.lp(top = 12, ctx = ctx))
            val btns = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL }
            btns.addView(Ui.button(ctx, "Sign in", false) { signIn(c.name) }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            btns.addView(Ui.spacer(ctx, 1).apply { layoutParams = LinearLayout.LayoutParams(Ui.dp(ctx, 8), 1) })
            btns.addView(Ui.button(ctx, "API key", false) { showKeySheet(c.name) }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            if (c.usable) {
                btns.addView(Ui.spacer(ctx, 1).apply { layoutParams = LinearLayout.LayoutParams(Ui.dp(ctx, 8), 1) })
                btns.addView(Ui.button(ctx, "Remove", false) { store.clearCred(c.name); refreshAll(); render() }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            }
            addView(btns, Ui.lp(top = 6, ctx = ctx))
        }
        if (busy.startsWith("auth:")) addView(Ui.muted(ctx, busy.removePrefix("auth:")), Ui.lp(top = 8, ctx = ctx))
    }

    private fun signIn(provider: String) {
        busy = "auth:Starting sign-in for $provider..."; render()
        healer.start(provider, activity) { r -> onAuthResult(r, provider) }
    }

    private fun onAuthResult(r: AuthResult, provider: String) {
        when (r) {
            is AuthResult.Success -> {
                busy = ""; toast("${provider.replaceFirstChar { it.uppercase() }} connected (layer ${r.layer})")
                Bg.io { ProvidersStore.sync(ctx); TermuxClient(ctx).pushKeysBlocking() }
                refreshAll()
            }
            is AuthResult.NeedsUser -> {
                if (r.layer >= 3) openSniffer(provider, r.message) else { busy = "auth:${r.message}"; render() }
            }
            is AuthResult.Failed -> { busy = "auth:Sign-in failed (layer ${r.layer}): ${r.reason}"; render() }
        }
    }

    /** Layer 3 (cookie sniffer) with layer 4 (API key) as the fallback. */
    private fun openSniffer(provider: String, why: String) {
        val ep = healer.bundled(provider)
        if (ep == null || ep.webLoginUrl.isBlank()) { showKeySheet(provider); return }
        busy = "auth:$why"; render()
        WebViewSnifferDialog(activity, ep,
            onCaptured = { cap -> onAuthResult(healer.saveSession(provider, cap.cookies, cap.userAgent, cap.orgId), provider) },
            onFallbackToKey = { showKeySheet(provider) }).show()
    }

    private fun showKeySheet(provider: String) {
        val ep = healer.bundled(provider)
        val box = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
        box.addView(Ui.text(ctx, "${provider.replaceFirstChar { it.uppercase() }} API key", 18f, Ui.TEXT, true))
        box.addView(Ui.muted(ctx, "Stored encrypted on this phone. Get one at ${ep?.apiKeyConsoleUrl ?: "the provider console"}."), Ui.lp(top = 4, ctx = ctx))
        val input = Ui.input(ctx, "Paste API key", secret = true)
        box.addView(input, Ui.lp(top = 12, ctx = ctx))
        val err = Ui.text(ctx, "", 12f, Ui.BAD)
        box.addView(err, Ui.lp(top = 6, ctx = ctx))
        box.addView(Ui.button(ctx, "Save key") {
            val r = healer.saveApiKey(provider, input.text.toString())
            if (r is AuthResult.Failed) err.text = r.reason else { sheet.dismiss(); onAuthResult(r, provider) }
        }, Ui.lp(top = 8, ctx = ctx))
        box.addView(Ui.button(ctx, "Cancel", false) { sheet.dismiss() }, Ui.lp(top = 8, ctx = ctx))
        sheet.show(box)
    }

    // ---- Gate 2
    private fun termuxCard(): View = Ui.card(ctx).apply {
        addView(header(2, "Termux engine (127.0.0.1:8775)", termuxOk))
        addView(Ui.muted(ctx, "The Python engine runs in Termux. First time? Copy the setup line, paste it into Termux and run it."), Ui.lp(top = 4, ctx = ctx))
        addView(Ui.button(ctx, "Copy 1-Line Setup", true) {
            val cm = ctx.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            cm.setPrimaryClip(ClipData.newPlainText("stickman setup", Defaults.SETUP_ONE_LINER))
            toast("Copied. Open Termux, paste, press Enter.")
        }, Ui.lp(top = 12, ctx = ctx))
        for (row in diagRows) addView(diagRowView(row), Ui.lp(top = 10, ctx = ctx))
        if (diagRows.isEmpty()) addView(Ui.muted(ctx, "Running diagnostics..."), Ui.lp(top = 10, ctx = ctx))
        val anyFix = diagRows.any { it.fixable && it.state == DiagState.FAIL }
        if (anyFix) addView(Ui.button(ctx, "Fix everything I can", true) { fixAll() }, Ui.lp(top = 12, ctx = ctx))
    }

    private fun diagRowView(r: DiagRow): View = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val head = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        val color = when (r.state) { DiagState.OK -> Ui.OK; DiagState.WARN -> Ui.WARN; DiagState.FAIL -> Ui.BAD }
        head.addView(Ui.text(ctx, r.title, 14f, Ui.TEXT, true), LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        head.addView(Ui.badge(ctx, r.state.name, color))
        if (r.fixable && r.state != DiagState.OK) {
            head.addView(Ui.spacer(ctx, 1).apply { layoutParams = LinearLayout.LayoutParams(Ui.dp(ctx, 8), 1) })
            head.addView(Ui.button(ctx, "Fix", false) { fix(r.id) })
        }
        addView(head)
        addView(Ui.muted(ctx, r.detail), Ui.lp(top = 2, ctx = ctx))
    }

    private fun fix(id: String) {
        Bg.io {
            val msg = diag.fix(activity, id)
            Bg.ui { toast(msg) }
            Thread.sleep(2500)
            refreshAll()
        }
    }

    /** Runs every non-interactive fix in order; Settings-screen fixes are opened one at a time by their own button. */
    private fun fixAll() {
        Bg.io {
            val order = listOf("perm", "token", "daemon", "wake")
            val ids = diagRows.filter { it.fixable && it.state != DiagState.OK && it.id in order }.map { it.id }
            // Permission dialog first; the rest are retried after the permission result triggers refreshAll().
            if ("perm" in ids) { Bg.ui { toast(diag.fix(activity, "perm")) }; return@io }
            for (id in ids.filter { it != "wake" }) { diag.fix(activity, id); Thread.sleep(2000) }
            refreshAll()
        }
    }

    // ---- Gate 3
    private fun githubCard(): View = Ui.card(ctx).apply {
        addView(header(3, "GitHub (cloud renders)", ghOk))
        addView(Ui.muted(ctx, "A fine-grained token with Contents + Actions (read/write) on the repo. HD renders run in GitHub Actions."), Ui.lp(top = 4, ctx = ctx))
        val repo = Ui.input(ctx, "owner/repo").apply { setText(store.githubRepo) }
        val pat = Ui.input(ctx, if (github.hasToken()) "Token saved (paste to replace)" else "github_pat_...", secret = true)
        addView(repo, Ui.lp(top = 12, ctx = ctx))
        addView(pat, Ui.lp(top = 8, ctx = ctx))
        val status: TextView = Ui.text(ctx, ghStatus.message, 12f, if (ghOk) Ui.OK else Ui.MUTED)
        addView(status, Ui.lp(top = 6, ctx = ctx))
        addView(Ui.button(ctx, "Save & verify") {
            val r = repo.text.toString().trim()
            if (!Regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$").matches(r)) { status.text = "Repo must look like owner/name"; return@button }
            store.githubRepo = r
            val t = pat.text.toString().trim()
            if (t.isNotEmpty()) store.githubPat = t
            status.text = "Checking..."
            refreshAll()
        }, Ui.lp(top = 8, ctx = ctx))
    }

    private fun toast(s: String) = Toast.makeText(ctx, s, Toast.LENGTH_SHORT).show()
}
