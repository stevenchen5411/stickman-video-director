package com.near.stickmandirector.tabs

import android.view.ViewGroup
import android.widget.CheckBox
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.ui.Ui
import com.near.stickmandirector.workspace.Env
import com.near.stickmandirector.workspace.JobWatcher
import com.near.stickmandirector.workspace.Tab

/** Scout: find outlier videos and run the whole auto pipeline (scout -> forensics -> director -> audit -> queue). */
class ScoutTab(env: Env) : Tab(env) {
    override val title = "Scout"
    private val ctx = env.activity
    private val niche = Ui.input(ctx, "Niche (e.g. psychology, finance)").apply { setText("general") }
    private val queries = Ui.input(ctx, "Search queries, comma separated")
    private val channels = Ui.input(ctx, "Channels (@handle or URL), comma separated")
    private val multiplier = Ui.input(ctx, "Min outlier multiplier").apply { setText("3.0") }
    private val offline = CheckBox(ctx).apply { text = "Offline mode (use already-downloaded data only)"; setTextColor(Ui.MUTED) }
    private val status: TextView = Ui.text(ctx, "Idle", 13f, Ui.MUTED)
    private val log: TextView = Ui.text(ctx, "", 12f, Ui.MUTED)
    private var watcher: JobWatcher? = null
    private var runBtn: TextView? = null

    override val view: ScrollView = ScrollView(ctx).apply {
        val col = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            val p = Ui.dp(ctx, 16); setPadding(p, p, p, p * 2)
        }
        col.addView(Ui.title(ctx, "Scout"))
        col.addView(Ui.muted(ctx, "Finds videos that beat their channel's average, rebuilds them as a new stickman script, and queues the package in Studio."))
        val card = Ui.card(ctx)
        card.addView(niche); card.addView(queries, Ui.lp(top = 8, ctx = ctx))
        card.addView(channels, Ui.lp(top = 8, ctx = ctx)); card.addView(multiplier, Ui.lp(top = 8, ctx = ctx))
        card.addView(offline, Ui.lp(top = 4, ctx = ctx))
        val btn = Ui.button(ctx, "Run auto pipeline") { start() }
        runBtn = btn
        card.addView(btn, Ui.lp(top = 12, ctx = ctx))
        col.addView(card, Ui.lp(top = 16, ctx = ctx))
        col.addView(status, Ui.lp(top = 16, ctx = ctx))
        col.addView(log, Ui.lp(top = 4, ctx = ctx))
        addView(col, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

    private fun split(s: String) = s.split(",").map { it.trim() }.filter { it.isNotEmpty() }

    private fun start() {
        val mult = multiplier.text.toString().toDoubleOrNull()?.coerceIn(1.0, 50.0) ?: 3.0
        status.text = "Starting..."; status.setTextColor(Ui.MUTED); log.text = ""
        runBtn?.isEnabled = false
        Bg.io {
            try {
                val id = env.api.startAuto(niche.text.toString().trim().ifBlank { "general" },
                    split(queries.text.toString()), split(channels.text.toString()), mult, offline.isChecked)
                Bg.ui { follow(id) }
            } catch (t: Throwable) {
                Bg.ui { status.text = "Could not start: ${t.message}"; status.setTextColor(Ui.BAD); runBtn?.isEnabled = true }
            }
        }
    }

    private fun follow(jobId: String) {
        watcher?.cancel()
        val w = JobWatcher(env.api); watcher = w
        w.watch(jobId,
            onUpdate = { j -> status.text = "Running (${j.optString("status")})"; log.text = JobWatcher.lastLog(j, 8) },
            onDone = { j ->
                runBtn?.isEnabled = true
                log.text = JobWatcher.lastLog(j, 8)
                if (j.optString("status") == "done") {
                    status.text = "Done. New packages are in Studio."; status.setTextColor(Ui.OK); env.onQueueChanged()
                } else {
                    status.text = "Failed: ${j.optString("error")}"; status.setTextColor(Ui.BAD)
                }
            },
            onError = { m -> runBtn?.isEnabled = true; status.text = "Lost contact with the daemon: $m"; status.setTextColor(Ui.BAD) })
    }
}
