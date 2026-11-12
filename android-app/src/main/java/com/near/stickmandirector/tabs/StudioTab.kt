package com.near.stickmandirector.tabs

import android.content.Context
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.ui.ListAdapter
import com.near.stickmandirector.ui.Ui
import com.near.stickmandirector.workspace.AnalysisDetailView
import com.near.stickmandirector.workspace.Env
import com.near.stickmandirector.workspace.Tab
import org.json.JSONObject

/** Studio: the queue of analysis packages. Tap one to inspect, edit scenes and render. */
class StudioTab(env: Env) : Tab(env) {
    override val title = "Studio"
    private val ctx = env.activity
    private val empty: TextView = Ui.muted(ctx, "").apply { val p = Ui.dp(ctx, 16); setPadding(p, p, p, p) }
    private val adapter = ListAdapter<JSONObject>(emptyList()) { c, item -> row(c, item) }

    override val view: View = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val head = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL
            val p = Ui.dp(ctx, 16); setPadding(p, p, p, Ui.dp(ctx, 8))
        }
        head.addView(Ui.title(ctx, "Studio"), LinearLayout.LayoutParams(0, android.view.ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        head.addView(Ui.button(ctx, "Refresh", false) { reload() })
        addView(head)
        addView(empty)
        addView(ListAdapter.recycler(ctx, adapter), LinearLayout.LayoutParams(android.view.ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
    }

    override fun onShow() = reload()

    fun reload() {
        empty.text = "Loading..."
        Bg.io {
            try {
                val items = env.api.queue()
                Bg.ui {
                    adapter.submit(items)
                    empty.text = if (items.isEmpty()) "No packages yet. Run the pipeline from the Scout tab." else ""
                    empty.visibility = if (items.isEmpty()) View.VISIBLE else View.GONE
                }
            } catch (t: Throwable) {
                Bg.ui { adapter.submit(emptyList()); empty.visibility = View.VISIBLE; empty.text = "Daemon not reachable: ${t.message}\nCheck the System tab." }
            }
        }
    }

    private fun row(c: Context, it: JSONObject): View {
        val card = Ui.card(c)
        card.setOnClickListener { _ -> env.open(AnalysisDetailView(env, it.getString("package_id")).view) { reload() } }
        card.addView(Ui.text(c, it.optString("title", it.optString("package_id")), 15f, Ui.TEXT, true))
        val badges = LinearLayout(c).apply { orientation = LinearLayout.HORIZONTAL }
        val passed = it.optBoolean("passed")
        badges.addView(Ui.badge(c, if (passed) "AUDIT PASSED" else "NEEDS WORK", if (passed) Ui.OK else Ui.WARN))
        badges.addView(Ui.badge(c, "${it.optInt("scenes")} scenes", Ui.ACCENT))
        card.addView(badges, Ui.lp(top = 8, ctx = c))
        card.addView(Ui.muted(c, "${it.optString("niche")}  ·  ${"%.1f".format(it.optDouble("outlier_multiplier"))}x outlier  ·  " +
            "${"%.0f".format(it.optDouble("duration_sec"))}s  ·  ${"%.0f".format(it.optDouble("visual_activity_pct"))}% active"), Ui.lp(top = 6, ctx = c))
        card.layoutParams = android.widget.FrameLayout.LayoutParams(-1, -2).apply { topMargin = Ui.dp(c, 8) }
        return card
    }
}
