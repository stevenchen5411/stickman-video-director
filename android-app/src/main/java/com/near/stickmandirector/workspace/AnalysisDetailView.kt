package com.near.stickmandirector.workspace

import android.view.View
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.ui.Ui
import org.json.JSONObject
import java.io.File

/** One analysis package: titles, audit, render actions (local draft + GitHub HD) and the scene list. */
class AnalysisDetailView(private val env: Env, private val id: String) {
    private val ctx = env.activity
    private var pkg: JSONObject? = null
    private val content = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val p = Ui.dp(ctx, 16); setPadding(p, p, p, p * 2)
    }
    private val status: TextView = Ui.text(ctx, "", 13f, Ui.MUTED)
    private var watcher: JobWatcher? = null

    val view: View = Screen.frame(ctx, id, { env.close() }, ScrollView(ctx).apply { addView(content) })

    private fun alive() = view.isAttachedToWindow
    private fun draftFile() = File(Defaults.STORAGE_DIR, "renders/${id}_draft.mp4")
    private fun hdFile() = File(Defaults.STORAGE_DIR, "renders/$id.mp4")

    init { load() }

    private fun load() {
        content.removeAllViews(); content.addView(Ui.muted(ctx, "Loading..."))
        Bg.io {
            try {
                val p = env.api.pkg(id)
                Bg.ui { pkg = p; build() }
            } catch (t: Throwable) {
                Bg.ui { content.removeAllViews(); content.addView(Ui.text(ctx, "Could not load: ${t.message}", 14f, Ui.BAD)) }
            }
        }
    }

    private fun build() {
        val p = pkg ?: return
        // `status` outlives rebuilds: detach it from the previous card first, or addView() throws "child already has a parent".
        (status.parent as? android.view.ViewGroup)?.removeView(status)
        content.removeAllViews()
        val vp = p.getJSONObject("viral_packaging")
        val qa = p.getJSONObject("quality_audit")
        val src = p.getJSONObject("source_viral_video")

        val titles = Ui.card(ctx)
        titles.addView(Ui.muted(ctx, "TITLE VARIANTS"))
        val tv = vp.getJSONArray("title_variants")
        for (i in 0 until tv.length()) titles.addView(Ui.text(ctx, "${i + 1}. ${tv.getString(i)}", 15f, Ui.TEXT, i == 0), Ui.lp(top = 6, ctx = ctx))
        titles.addView(Ui.muted(ctx, "Cover hook: ${vp.optString("cover_text_hook")}"), Ui.lp(top = 10, ctx = ctx))
        titles.addView(Ui.muted(ctx, "Source: ${src.optString("channel")} · ${"%.1f".format(src.optDouble("outlier_multiplier"))}x outlier · ${src.optString("niche")}"), Ui.lp(top = 4, ctx = ctx))
        content.addView(titles)

        val audit = Ui.card(ctx)
        val passed = qa.optBoolean("passed")
        val head = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
        head.addView(Ui.text(ctx, "Quality audit", 15f, Ui.TEXT, true), LinearLayout.LayoutParams(0, -2, 1f))
        head.addView(Ui.badge(ctx, if (passed) "PASSED" else "NOT PASSED", if (passed) Ui.OK else Ui.WARN))
        audit.addView(head)
        audit.addView(Ui.muted(ctx, "${"%.0f".format(qa.optDouble("estimated_duration_sec"))}s total · ${"%.1f".format(qa.optDouble("avg_beat_sec"))}s avg beat · " +
            "${"%.0f".format(qa.optDouble("visual_activity_pct"))}% of beats in motion (gate: 75%) · status ${p.optString("status")}"), Ui.lp(top = 6, ctx = ctx))
        val rep = qa.optJSONArray("auto_repaired_scenes")
        if (rep != null && rep.length() > 0) audit.addView(Ui.muted(ctx, "Auto-repaired ${rep.length()} scene(s) to reach the motion gate."), Ui.lp(top = 4, ctx = ctx))
        content.addView(audit, Ui.lp(top = 12, ctx = ctx))

        val act = Ui.card(ctx)
        act.addView(Ui.text(ctx, "Render", 15f, Ui.TEXT, true))
        act.addView(Ui.button(ctx, "Draft render (480p, on this phone)") { draft() }, Ui.lp(top = 10, ctx = ctx))
        act.addView(Ui.button(ctx, "HD render (1080p60, GitHub Actions)", false) { hdRender() }, Ui.lp(top = 8, ctx = ctx))
        act.addView(Ui.button(ctx, "Fetch finished cloud render", false) { fetchCloud(loop = false) }, Ui.lp(top = 8, ctx = ctx))
        if (draftFile().isFile) act.addView(Ui.button(ctx, "Play draft", false) { play(draftFile(), "Draft") }, Ui.lp(top = 8, ctx = ctx))
        if (hdFile().isFile) act.addView(Ui.button(ctx, "Play HD", false) { play(hdFile(), "HD") }, Ui.lp(top = 8, ctx = ctx))
        act.addView(status, Ui.lp(top = 10, ctx = ctx))
        content.addView(act, Ui.lp(top = 12, ctx = ctx))

        content.addView(Ui.text(ctx, "Storyboard", 17f, Ui.TEXT, true), Ui.lp(top = 18, ctx = ctx))
        val scenes = p.getJSONArray("scenes")
        for (i in 0 until scenes.length()) content.addView(sceneRow(i, scenes.getJSONObject(i)), Ui.lp(top = 8, ctx = ctx))
    }

    private fun sceneRow(i: Int, s: JSONObject): View {
        val ch = s.getJSONObject("character")
        val card = Ui.card(ctx)
        val text = s.getJSONObject("narration").optString("text")
        card.addView(Ui.text(ctx, "${i + 1}.  ${if (text.length > 120) text.take(117) + "..." else text}", 14f, Ui.TEXT))
        val motion = ch.optString("motion_id").takeIf { it.isNotBlank() && it != "null" } ?: "no motion"
        card.addView(Ui.muted(ctx, "${ch.optString("character_id")} · ${ch.optString("pose_id")} · ${ch.optString("expression_id")} · $motion"), Ui.lp(top = 4, ctx = ctx))
        card.setOnClickListener {
            val p = pkg ?: return@setOnClickListener
            env.open(StoryboardEditorView(env, p, i) { updated -> pkg = updated; build() }.view)
        }
        return card
    }

    // ------------------------------------------------------------------ rendering
    private fun say(s: String, color: Int = Ui.MUTED) { status.text = s; status.setTextColor(color) }

    private fun play(f: File, title: String) {
        if (!f.isFile) { env.toast("File not found: ${f.name}"); return }
        env.open(PlayerScreen.build(env, f, "$id · $title"))
    }

    private fun draft() {
        say("Starting draft render...")
        Bg.io {
            try {
                val job = env.api.renderDraft(id)
                Bg.ui {
                    watcher?.cancel(); val w = JobWatcher(env.api); watcher = w
                    w.watch(job,
                        onUpdate = { j -> say("Rendering: ${JobWatcher.lastLog(j, 1)}") },
                        onDone = { j ->
                            if (j.optString("status") == "done") {
                                runCatching { build() }
                                say("Draft ready", Ui.OK)
                                runCatching { play(draftFile(), "Draft") }.onFailure { env.toast("Could not open the player: ${it.message}") }
                            }
                            else say("Render failed: ${j.optString("error")}", Ui.BAD)
                        },
                        onError = { m -> say("Lost contact with the daemon: $m", Ui.BAD) })
                }
            } catch (t: Throwable) { Bg.ui { say("Could not start render: ${t.message}", Ui.BAD) } }
        }
    }

    private fun hdRender() {
        val p = pkg ?: return
        if (!env.github.hasToken()) { say("Add a GitHub token in the System tab first.", Ui.BAD); return }
        if (!p.getJSONObject("quality_audit").optBoolean("passed")) { say("Audit has not passed. Edit scenes until it does.", Ui.BAD); return }
        say("Uploading package to GitHub...")
        val bytes = p.toString().toByteArray(Charsets.UTF_8)
        Bg.io {
            val up = env.github.putFile("queue/$id.json", bytes, "queue: $id")
            if (up != null) { Bg.ui { say("Upload failed: $up", Ui.BAD) }; return@io }
            Bg.ui { say("Triggering render...") }
            val d = env.github.dispatchRender(id)
            if (d != null) { Bg.ui { say("Dispatch failed: $d", Ui.BAD) }; return@io }
            fetchCloudBlocking(loop = true)
        }
    }

    private fun fetchCloud(loop: Boolean) { Bg.io { fetchCloudBlocking(loop) } }

    /** Polls the `render-<id>` release (every 20 s for up to 45 min when [loop]); downloads <id>.mp4 + cover. */
    private fun fetchCloudBlocking(loop: Boolean) {
        val deadline = System.currentTimeMillis() + 45 * 60_000L
        while (true) {
            if (!alive()) return
            val rel = env.github.pollRelease(id)
            if (rel?.videoUrl != null) {
                Bg.ui { say("Downloading render...") }
                val e = env.github.downloadAsset(rel.videoUrl, hdFile())
                rel.coverUrl?.let { env.github.downloadAsset(it, File(Defaults.STORAGE_DIR, "renders/${id}_cover.jpg")) }
                Bg.ui { if (e == null) { say("HD render downloaded", Ui.OK); build(); play(hdFile(), "HD") } else say("Download failed: $e", Ui.BAD) }
                return
            }
            if (!loop || System.currentTimeMillis() > deadline) {
                val run = env.github.renderRunStatus()
                Bg.ui { say(if (loop) "Timed out waiting for the cloud render (workflow: ${run ?: "unknown"})." else "Not ready yet (workflow: ${run ?: "unknown"}).", Ui.WARN) }
                return
            }
            val run = env.github.renderRunStatus()
            Bg.ui { say("Cloud render in progress (workflow: ${run ?: "queued"}). Keep this screen open.") }
            Thread.sleep(20_000)
        }
    }
}
