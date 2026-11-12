package com.near.stickmandirector.tabs

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import android.view.View
import android.view.ViewGroup
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.ui.ListAdapter
import com.near.stickmandirector.ui.Ui
import com.near.stickmandirector.workspace.Env
import com.near.stickmandirector.workspace.JobWatcher
import com.near.stickmandirector.workspace.Tab
import org.json.JSONObject
import java.io.File

/** Library: browse the asset library by category, forge new assets, rebuild thumbnails, run the curator. */
class LibraryTab(env: Env) : Tab(env) {
    override val title = "Library"
    private val ctx = env.activity
    private val categories = listOf("01_characters", "02_poses", "03_expressions", "04_motions", "05_scenes", "06_props",
        "07_widgets", "08_overlays", "09_transitions", "10_caption_styles", "11_themes", "12_voices", "13_bgm", "14_sfx")
    private var all: List<JSONObject> = emptyList()
    private var filter: String? = null
    private val info: TextView = Ui.muted(ctx, "").apply { val p = Ui.dp(ctx, 16); setPadding(p, 0, p, Ui.dp(ctx, 6)) }
    private val thumbs = LruCache<String, Bitmap>(64)
    private val adapter = ListAdapter<JSONObject>(emptyList()) { c, a -> row(c, a) }
    private val chips = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; val p = Ui.dp(ctx, 12); setPadding(p, 0, p, 0) }
    private var watcher: JobWatcher? = null

    override val view: View = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val head = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL
            val p = Ui.dp(ctx, 16); setPadding(p, p, p, Ui.dp(ctx, 8))
        }
        head.addView(Ui.title(ctx, "Library"), LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        head.addView(Ui.button(ctx, "Forge", true) { forgeSheet() })
        addView(head)
        val actions = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; val p = Ui.dp(ctx, 12); setPadding(p, 0, p, Ui.dp(ctx, 8)) }
        actions.addView(Ui.button(ctx, "Rebuild thumbs", false) { runJob("Rebuilding thumbnails") { env.api.rebuildThumbs() } })
        actions.addView(Ui.button(ctx, "Curate", false) { curate() }, Ui.lp(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { leftMargin = Ui.dp(ctx, 8) })
        addView(actions)
        addView(HorizontalScrollView(ctx).apply { isHorizontalScrollBarEnabled = false; addView(chips) })
        addView(info)
        addView(ListAdapter.recycler(ctx, adapter), LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
    }

    override fun onShow() = reload()

    private fun buildChips() {
        chips.removeAllViews()
        val counts = all.groupingBy { it.optString("category") }.eachCount()
        fun chip(label: String, cat: String?) {
            val sel = filter == cat
            chips.addView(Ui.button(ctx, label, sel) { filter = cat; applyFilter(); buildChips() },
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { rightMargin = Ui.dp(ctx, 6) })
        }
        chip("All ${all.size}", null)
        for (c in categories) chip("${c.substringAfter('_')} ${counts[c] ?: 0}", c)
    }

    private fun applyFilter() {
        val list = if (filter == null) all else all.filter { it.optString("category") == filter }
        adapter.submit(list)
        info.text = "${list.size} asset(s)"
    }

    fun reload() {
        info.text = "Loading..."
        Bg.io {
            try {
                val a = env.api.library()
                Bg.ui { all = a; buildChips(); applyFilter() }
            } catch (t: Throwable) { Bg.ui { info.text = "Daemon not reachable: ${t.message}" } }
        }
    }

    private fun row(c: Context, a: JSONObject): View {
        val card = LinearLayout(c).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL
            val p = Ui.dp(c, 10); setPadding(p, p, p, p)
            background = Ui.rounded(c, Ui.CARD)
            layoutParams = android.widget.FrameLayout.LayoutParams(-1, -2).apply { topMargin = Ui.dp(c, 6) }
        }
        val img = ImageView(c).apply { setBackgroundColor(Ui.CARD_ALT); scaleType = ImageView.ScaleType.FIT_CENTER }
        card.addView(img, LinearLayout.LayoutParams(Ui.dp(c, 56), Ui.dp(c, 56)))
        loadThumb(img, a.optString("thumb_path"))
        val col = LinearLayout(c).apply { orientation = LinearLayout.VERTICAL; setPadding(Ui.dp(c, 12), 0, 0, 0) }
        col.addView(Ui.text(c, a.optString("id"), 14f, Ui.TEXT, true))
        val tags = a.optJSONArray("niche_tags")?.let { t -> (0 until t.length()).joinToString(", ") { t.optString(it) } } ?: ""
        col.addView(Ui.muted(c, "${a.optString("category").substringAfter('_')} · ${a.optString("scope")} · used ${a.optInt("usage_count")}x" +
            if (tags.isNotEmpty()) " · $tags" else ""))
        card.addView(col, LinearLayout.LayoutParams(0, -2, 1f))
        return card
    }

    private fun loadThumb(img: ImageView, rel: String) {
        if (rel.isBlank()) return
        thumbs.get(rel)?.let { img.setImageBitmap(it); return }
        img.tag = rel
        Bg.io {
            val f = File(Defaults.STORAGE_DIR, "assets/library/$rel")
            if (!f.isFile) return@io
            val opts = BitmapFactory.Options().apply { inSampleSize = 2 }
            val bm = runCatching { BitmapFactory.decodeFile(f.absolutePath, opts) }.getOrNull() ?: return@io
            thumbs.put(rel, bm)
            Bg.ui { if (img.tag == rel) img.setImageBitmap(bm) }
        }
    }

    private fun curate() {
        Bg.io {
            try {
                val r = env.api.curate()
                Bg.ui { env.toast("Curator: ${r.toString().take(120)}"); reload() }
            } catch (t: Throwable) { Bg.ui { env.toast("Curate failed: ${t.message}") } }
        }
    }

    private fun runJob(label: String, start: () -> String) {
        info.text = "$label..."
        Bg.io {
            try {
                val id = start()
                Bg.ui {
                    watcher?.cancel(); val w = JobWatcher(env.api); watcher = w
                    w.watch(id, onUpdate = { j -> info.text = "$label: ${JobWatcher.lastLog(j, 1)}" },
                        onDone = { j -> info.text = if (j.optString("status") == "done") "$label: done" else "$label failed: ${j.optString("error")}"; reload() },
                        onError = { m -> info.text = "$label: lost contact ($m)" })
                }
            } catch (t: Throwable) { Bg.ui { info.text = "$label failed: ${t.message}" } }
        }
    }

    private fun forgeSheet() {
        var catIdx = 4
        val box = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
        box.addView(Ui.text(ctx, "Forge a new asset", 18f, Ui.TEXT, true))
        box.addView(Ui.muted(ctx, "The engine drafts it, validates it, and rejects near-duplicates of existing assets."), Ui.lp(top = 4, ctx = ctx))
        val cat = Ui.button(ctx, "Category: ${categories[catIdx]}", false) {}
        cat.setOnClickListener { catIdx = (catIdx + 1) % categories.size; cat.text = "Category: ${categories[catIdx]}" }
        box.addView(cat, Ui.lp(top = 12, ctx = ctx))
        val id = Ui.input(ctx, "id (a-z, 0-9, _)"); box.addView(id, Ui.lp(top = 8, ctx = ctx))
        val brief = Ui.input(ctx, "Brief, e.g. rooftop at dusk"); box.addView(brief, Ui.lp(top = 8, ctx = ctx))
        val err = Ui.text(ctx, "", 12f, Ui.BAD); box.addView(err, Ui.lp(top = 6, ctx = ctx))
        box.addView(Ui.button(ctx, "Forge") {
            val i = id.text.toString().trim()
            if (!Regex("^[a-z0-9][a-z0-9_]{0,63}$").matches(i)) { err.text = "id: lowercase letters, digits, underscore"; return@button }
            val category = categories[catIdx]; val b = brief.text.toString().trim()
            env.sheet.dismiss()
            runJob("Forging $i") { env.api.forge(category, i, b) }
        }, Ui.lp(top = 8, ctx = ctx))
        env.sheet.show(box)
    }
}
