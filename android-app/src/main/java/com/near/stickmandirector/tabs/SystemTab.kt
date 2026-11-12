package com.near.stickmandirector.tabs

import android.view.Gravity
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.auth.ProviderFailoverPool
import com.near.stickmandirector.auth.ProvidersStore
import com.near.stickmandirector.gate.DiagRow
import com.near.stickmandirector.gate.DiagState
import com.near.stickmandirector.gate.TermuxDiagnostics
import com.near.stickmandirector.model.GitHubStatus
import com.near.stickmandirector.ui.Ui
import com.near.stickmandirector.workspace.Env
import com.near.stickmandirector.workspace.Tab

/** System: engine diagnostics with fixes, AI provider pool, GitHub link, key/config sync, and re-opening the connect gate. */
class SystemTab(env: Env) : Tab(env) {
    override val title = "System"
    private val ctx = env.activity
    private val diag = TermuxDiagnostics(ctx)
    private val pool = ProviderFailoverPool(ctx)
    private val col = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val p = Ui.dp(ctx, 16); setPadding(p, p, p, p * 2)
    }
    override val view = ScrollView(ctx).apply { addView(col, ViewGroup.LayoutParams(-1, -2)) }

    private var rows: List<DiagRow> = emptyList()
    private var gh = GitHubStatus(false, message = "Checking...")
    private var workflow: String? = null
    private var note = ""

    override fun onShow() {
        Bg.io {
            val r = diag.run()
            val g = if (env.github.hasToken()) env.github.verify() else GitHubStatus(false, message = "No token saved")
            val w = if (g.ok) env.github.renderRunStatus() else null
            Bg.ui { rows = r; gh = g; workflow = w; render() }
        }
        render()
    }

    private fun render() {
        col.removeAllViews()
        col.addView(Ui.title(ctx, "System"))

        val eng = Ui.card(ctx)
        eng.addView(Ui.text(ctx, "Engine (Termux)", 15f, Ui.TEXT, true))
        if (rows.isEmpty()) eng.addView(Ui.muted(ctx, "Running diagnostics..."), Ui.lp(top = 6, ctx = ctx))
        for (r in rows) {
            val head = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
            val color = when (r.state) { DiagState.OK -> Ui.OK; DiagState.WARN -> Ui.WARN; DiagState.FAIL -> Ui.BAD }
            head.addView(Ui.text(ctx, r.title, 14f, Ui.TEXT, true), LinearLayout.LayoutParams(0, -2, 1f))
            head.addView(Ui.badge(ctx, r.state.name, color))
            if (r.fixable && r.state != DiagState.OK) head.addView(Ui.button(ctx, "Fix", false) {
                Bg.io { val m = diag.fix(env.activity, r.id); Bg.ui { env.toast(m) }; Thread.sleep(2500); onShow() }
            }, LinearLayout.LayoutParams(-2, -2).apply { leftMargin = Ui.dp(ctx, 8) })
            eng.addView(head, Ui.lp(top = 10, ctx = ctx))
            eng.addView(Ui.muted(ctx, r.detail), Ui.lp(top = 2, ctx = ctx))
        }
        col.addView(eng, Ui.lp(top = 12, ctx = ctx))

        val ai = Ui.card(ctx)
        ai.addView(Ui.text(ctx, "AI providers", 15f, Ui.TEXT, true))
        val wait = pool.secondsUntilAvailable()
        for (c in env.store.allCreds()) {
            val cool = ((c.cooldownUntilMs - System.currentTimeMillis()) / 1000).coerceAtLeast(0)
            val head = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
            head.addView(Ui.text(ctx, c.name.replaceFirstChar { it.uppercase() }, 14f, Ui.TEXT, true), LinearLayout.LayoutParams(0, -2, 1f))
            head.addView(when {
                !c.usable -> Ui.badge(ctx, "NOT CONNECTED", Ui.MUTED)
                cool > 0 -> Ui.badge(ctx, "RATE-LIMITED ${cool / 60}m", Ui.WARN)
                else -> Ui.badge(ctx, c.mode.wire.uppercase(), Ui.OK)
            })
            ai.addView(head, Ui.lp(top = 10, ctx = ctx))
        }
        ai.addView(Ui.muted(ctx, when {
            wait == 0L -> "Failover order: claude, gemini, chatgpt. A 429 moves work to the next ready provider."
            wait < 0 -> "No provider connected."
            else -> "All providers are cooling down. Next available in ${wait / 60}m."
        }), Ui.lp(top = 8, ctx = ctx))
        col.addView(ai, Ui.lp(top = 12, ctx = ctx))

        val g = Ui.card(ctx)
        val gHead = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        gHead.addView(Ui.text(ctx, "GitHub", 15f, Ui.TEXT, true), LinearLayout.LayoutParams(0, -2, 1f))
        gHead.addView(Ui.badge(ctx, if (gh.ok) "CONNECTED" else "ATTENTION", if (gh.ok) Ui.OK else Ui.WARN))
        g.addView(gHead)
        g.addView(Ui.muted(ctx, gh.message + (workflow?.let { "\nLatest render workflow: $it" } ?: "")), Ui.lp(top = 6, ctx = ctx))
        col.addView(g, Ui.lp(top = 12, ctx = ctx))

        val tools = Ui.card(ctx)
        tools.addView(Ui.text(ctx, "Sync", 15f, Ui.TEXT, true))
        tools.addView(Ui.button(ctx, "Push keys to engine now", false) {
            Bg.io { val ok = env.api.client.pushKeysBlocking(); Bg.ui { env.toast(if (ok) "Keys sent (memory only)" else "Engine did not accept keys") } }
        }, Ui.lp(top = 10, ctx = ctx))
        tools.addView(Ui.button(ctx, "Write encrypted providers.json", false) {
            Bg.io { val e = ProvidersStore.sync(ctx); Bg.ui { env.toast(e ?: "providers.json written") } }
        }, Ui.lp(top = 8, ctx = ctx))
        tools.addView(Ui.button(ctx, "Connections (AI / Termux / GitHub)", false) { env.onReconnect() }, Ui.lp(top = 8, ctx = ctx))
        tools.addView(Ui.button(ctx, "Re-run diagnostics", true) { note = ""; onShow() }, Ui.lp(top = 8, ctx = ctx))
        col.addView(tools, Ui.lp(top = 12, ctx = ctx))
    }
}
