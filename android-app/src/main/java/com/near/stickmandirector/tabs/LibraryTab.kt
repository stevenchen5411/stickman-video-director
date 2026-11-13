package com.near.stickmandirector.tabs

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.graphics.drawable.Animatable2
import android.graphics.drawable.AnimatedImageDrawable
import android.graphics.drawable.Drawable
import android.media.MediaPlayer
import android.text.Editable
import android.text.TextUtils
import android.text.TextWatcher
import android.util.LruCache
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.ui.ListAdapter
import com.near.stickmandirector.ui.Ui
import com.near.stickmandirector.workspace.Env
import com.near.stickmandirector.workspace.JobWatcher
import com.near.stickmandirector.workspace.Tab
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

/**
 * Library gallery: big square previews in a 2-column grid. Tap a moving asset (pose, motion, widget, overlay,
 * transition, caption, character, expression) to play its animation once, then it settles back to the still;
 * tap a sound to hear it (tap again to stop). Hold any asset for a bigger preview with its details.
 */
class LibraryTab(env: Env) : Tab(env) {
    override val title = "Library"
    private val ctx = env.activity
    private val categories = listOf("01_characters", "02_poses", "03_expressions", "04_motions", "05_scenes", "06_props",
        "07_widgets", "08_overlays", "09_transitions", "10_caption_styles", "11_themes", "12_voices", "13_bgm", "14_sfx")
    private val audioCats = setOf("13_bgm", "14_sfx")
    private var all: List<JSONObject> = emptyList()
    private var filter: String? = null
    private var query = ""
    private val info: TextView = Ui.muted(ctx, "").apply { val p = Ui.dp(ctx, 16); setPadding(p, Ui.dp(ctx, 6), p, Ui.dp(ctx, 6)) }
    private val decoder = Executors.newFixedThreadPool(2)
    private val thumbs = object : LruCache<String, Bitmap>(32 * 1024) {
        override fun sizeOf(key: String, value: Bitmap): Int = value.byteCount / 1024
    }
    private val adapter = ListAdapter<JSONObject>(emptyList()) { c, a -> cell(c, a) }
    private val chips = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; val p = Ui.dp(ctx, 12); setPadding(p, 0, p, 0) }
    private var watcher: JobWatcher? = null
    private var reviewBtn: TextView? = null

    // the one thing playing right now
    private var playingId: String? = null
    private var playingAsset: JSONObject? = null
    private var playingImg: ImageView? = null
    private var playingBadge: TextView? = null
    private var playingAnim: AnimatedImageDrawable? = null
    private var player: MediaPlayer? = null

    private val cellPx: Int by lazy { (ctx.resources.displayMetrics.widthPixels - Ui.dp(ctx, 56)) / 2 }

    override val view: View = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val head = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
            val p = Ui.dp(ctx, 16); setPadding(p, p, p, Ui.dp(ctx, 8))
        }
        head.addView(Ui.title(ctx, "Library"), LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        head.addView(Ui.button(ctx, "Forge", true) { forgeSheet() })
        addView(head)
        val actions = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; val p = Ui.dp(ctx, 12); setPadding(p, 0, p, Ui.dp(ctx, 8)) }
        fun action(label: String, onClick: (View) -> Unit) = actions.addView(Ui.button(ctx, label, false, onClick),
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { rightMargin = Ui.dp(ctx, 8) })
        action("Install pack") { runJob("Installing asset pack") { env.api.installPack() } }
        action("Rebuild previews") { runJob("Rebuilding previews") { env.api.rebuildThumbs() } }
        action("Curate") { curate() }
        action("Review forged") { openReview() }
        reviewBtn = (actions.getChildAt(actions.childCount - 1) as? TextView)
        addView(HorizontalScrollView(ctx).apply { isHorizontalScrollBarEnabled = false; addView(actions) })
        val search = Ui.input(ctx, "Search id or tag (e.g. virus, wave, chart)")
        search.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) { query = s?.toString() ?: ""; applyFilter() }
        })
        addView(search, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            val m = Ui.dp(ctx, 16); leftMargin = m; rightMargin = m; bottomMargin = Ui.dp(ctx, 8)
        })
        addView(HorizontalScrollView(ctx).apply { isHorizontalScrollBarEnabled = false; addView(chips) })
        addView(info)
        val grid = RecyclerView(ctx).apply {
            layoutManager = GridLayoutManager(ctx, 2)
            adapter = this@LibraryTab.adapter
            clipToPadding = false
            val p = Ui.dp(ctx, 8); setPadding(p, 0, p, Ui.dp(ctx, 16))
        }
        addView(grid, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
    }

    override fun onShow() = reload()

    override fun onHide() = stopPlaying()

    private fun JSONObject.str(k: String): String = if (isNull(k)) "" else optString(k)

    private fun tagsOf(a: JSONObject): List<String> =
        a.optJSONArray("niche_tags")?.let { t -> (0 until t.length()).map { t.optString(it) } } ?: emptyList()

    private fun kind(a: JSONObject): Int = when {
        a.optString("category") in audioCats -> AUDIO
        a.str("preview_path").isNotBlank() -> ANIM
        else -> STILL
    }

    private fun libFile(rel: String): File? =
        if (rel.isBlank()) null else File(Defaults.STORAGE_DIR, "assets/library/$rel").takeIf { it.isFile }

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
        stopPlaying()
        val q = query.trim().lowercase()
        val qu = q.replace(' ', '_')
        val list = all.filter { a ->
            (filter == null || a.optString("category") == filter) &&
                (q.isEmpty() || a.optString("id").contains(qu) || tagsOf(a).any { it.contains(q) || it.contains(qu) })
        }
        adapter.submit(list)
        val pend = all.count { it.optJSONObject("meta")?.optString("review") == "pending" }
        reviewBtn?.text = if (pend > 0) "Review forged ($pend)" else "Review forged"
        val packed = all.count { it.optJSONObject("meta")?.has("pack") == true }
        info.text = if (all.isNotEmpty() && packed == 0) "${list.size} asset(s) · tap Install pack to add the 1,500-asset starter pack"
        else "${list.size} asset(s) · tap to play · hold for details"
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

    // ------------------------------------------------------------------ grid cell
    private fun cell(c: Context, a: JSONObject): View {
        val id = a.optString("id")
        val box = LinearLayout(c).apply {
            orientation = LinearLayout.VERTICAL
            val p = Ui.dp(c, 6); setPadding(p, p, p, Ui.dp(c, 8))
            background = Ui.rounded(c, Ui.CARD)
            layoutParams = FrameLayout.LayoutParams(-1, -2).apply { val m = Ui.dp(c, 4); setMargins(m, m, m, m) }
        }
        val frame = FrameLayout(c)
        val img = ImageView(c).apply { scaleType = ImageView.ScaleType.FIT_CENTER; background = Ui.rounded(c, Ui.CARD_ALT, 10) }
        frame.addView(img, FrameLayout.LayoutParams(-1, cellPx))
        val k = kind(a)
        val badge = Ui.badge(c, when (k) { AUDIO -> "♪"; ANIM -> "▶"; else -> "" }, Ui.ACCENT)
        if (k != STILL) frame.addView(badge, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply { val m = Ui.dp(c, 6); setMargins(m, m, m, m) })
        box.addView(frame)
        box.addView(Ui.text(c, id, 13f, Ui.TEXT, true).apply { maxLines = 1; ellipsize = TextUtils.TruncateAt.END }, Ui.lp(top = 6, ctx = c))
        val tag = tagsOf(a).firstOrNull { it != "general" } ?: a.optString("scope")
        box.addView(Ui.text(c, "${a.optString("category").substringAfter('_')} · $tag", 11f, Ui.MUTED).apply { maxLines = 1; ellipsize = TextUtils.TruncateAt.END })
        if (id == playingId && playingAnim != null) {      // re-bound while its animation is still running
            img.tag = "anim:$id"; img.setImageDrawable(playingAnim); playingImg = img
        } else showStill(img, a)
        box.setOnClickListener { if (k == STILL) detail(a) else play(a, img, badge) }
        box.setOnLongClickListener { detail(a); true }
        return box
    }

    private fun showStill(img: ImageView, a: JSONObject) {
        val rel = a.str("thumb_path")
        img.tag = rel
        img.setImageDrawable(null)
        if (rel.isBlank()) return
        thumbs.get(rel)?.let { img.setImageBitmap(it); return }
        decoder.execute {
            val f = libFile(rel) ?: return@execute
            val bm = runCatching { BitmapFactory.decodeFile(f.absolutePath) }.getOrNull() ?: return@execute
            thumbs.put(rel, bm)
            Bg.ui { if (img.tag == rel) img.setImageBitmap(bm) }
        }
    }

    // ------------------------------------------------------------------ playback (one at a time, plays once)
    private fun play(a: JSONObject, img: ImageView, badge: TextView?) {
        val same = playingId == a.optString("id") && playingImg === img
        stopPlaying()
        if (same) return                       // second tap stops it
        when (kind(a)) {
            AUDIO -> playAudio(a, img, badge)
            ANIM -> playAnim(a, img)
            else -> {}
        }
    }

    private fun playAnim(a: JSONObject, img: ImageView) {
        val f = libFile(a.str("preview_path")) ?: run { env.toast("No preview yet - tap Rebuild previews"); return }
        val id = a.optString("id")
        playingId = id; playingAsset = a; playingImg = img
        img.tag = "anim:$id"
        decoder.execute {
            val d = runCatching { ImageDecoder.decodeDrawable(ImageDecoder.createSource(f)) }.getOrNull()
            Bg.ui {
                if (playingId != id) return@ui
                val anim = d as? AnimatedImageDrawable
                if (anim == null) { stopPlaying(); return@ui }
                anim.repeatCount = 0                // play once, then settle back to the still
                anim.registerAnimationCallback(object : Animatable2.AnimationCallback() {
                    override fun onAnimationEnd(drawable: Drawable?) { if (playingAnim === anim) stopPlaying() }
                })
                playingAnim = anim
                (playingImg ?: img).setImageDrawable(anim)
                anim.start()
            }
        }
    }

    private fun playAudio(a: JSONObject, img: ImageView, badge: TextView?) {
        val f = libFile(a.str("file_path")) ?: run { env.toast("Sound file missing"); return }
        try {
            val mp = MediaPlayer()
            mp.setDataSource(f.absolutePath)
            mp.setOnCompletionListener { done -> if (player === done) stopPlaying() }
            mp.prepare()
            mp.start()
            player = mp
            playingId = a.optString("id"); playingAsset = a; playingImg = img; playingBadge = badge
            badge?.text = "■"
        } catch (t: Throwable) { env.toast("Can't play: ${t.message}") }
    }

    private fun stopPlaying() {
        playingAnim?.let { runCatching { it.clearAnimationCallbacks(); it.stop() } }
        player?.let { runCatching { it.stop() }; runCatching { it.release() } }
        val img = playingImg; val a = playingAsset
        playingBadge?.text = "♪"
        playingAnim = null; player = null; playingImg = null; playingBadge = null; playingId = null; playingAsset = null
        if (img != null && a != null) showStill(img, a)
    }

    // ------------------------------------------------------------------ detail sheet (bigger preview)
    private fun detail(a: JSONObject) {
        stopPlaying()
        val box = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
        val side = minOf(ctx.resources.displayMetrics.widthPixels - Ui.dp(ctx, 36), Ui.dp(ctx, 340))
        val big = ImageView(ctx).apply { scaleType = ImageView.ScaleType.FIT_CENTER; background = Ui.rounded(ctx, Ui.CARD_ALT, 12) }
        box.addView(big, LinearLayout.LayoutParams(side, side).apply { gravity = Gravity.CENTER_HORIZONTAL })
        showStill(big, a)
        box.addView(Ui.text(ctx, a.optString("id"), 18f, Ui.TEXT, true), Ui.lp(top = 12, ctx = ctx))
        box.addView(Ui.muted(ctx, "${a.optString("category").substringAfter('_')} · ${a.optString("scope")} · used ${a.optInt("usage_count")}x"),
            Ui.lp(top = 2, ctx = ctx))
        val tags = tagsOf(a).joinToString(", ")
        if (tags.isNotEmpty()) box.addView(Ui.muted(ctx, "Tags: $tags"), Ui.lp(top = 2, ctx = ctx))
        box.addView(Ui.text(ctx, a.str("file_path"), 11f, Ui.MUTED), Ui.lp(top = 2, ctx = ctx))
        val k = kind(a)
        if (k != STILL) box.addView(Ui.button(ctx, if (k == AUDIO) "Play / stop" else "Play again", true) { play(a, big, null) },
            Ui.lp(top = 12, ctx = ctx))
        env.sheet.show(box) { stopPlaying() }
        if (k != STILL) play(a, big, null)
    }

    // ------------------------------------------------------------------ actions
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
                        onDone = { j ->
                            info.text = if (j.optString("status") == "done") "$label: done" else "$label failed: ${j.optString("error")}"
                            thumbs.evictAll(); reload()
                        },
                        onError = { m -> info.text = "$label: lost contact ($m)" })
                }
            } catch (t: Throwable) { Bg.ui { info.text = "$label failed: ${t.message}" } }
        }
    }

    // ------------------------------------------------------------------ review of forged assets (approve -> public repo, reject -> delete)
    private fun openReview() {
        val root = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL; val p = Ui.dp(ctx, 12); setPadding(p, p, p, p) }
        val status = Ui.muted(ctx, "Loading...")
        val list = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
        root.addView(Ui.title(ctx, "Review forged"))
        root.addView(status, Ui.lp(top = 4, ctx = ctx))
        val bar = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL }
        root.addView(bar, Ui.lp(top = 8, ctx = ctx))
        root.addView(list, Ui.lp(top = 8, ctx = ctx))
        val scroll = android.widget.ScrollView(ctx).apply { addView(root) }

        fun refresh() {
            Bg.io {
                try {
                    val pend = env.api.reviewList()
                    Bg.ui {
                        status.text = if (pend.isEmpty()) "Nothing waiting. Forged assets show up here until you approve them."
                        else "${pend.size} waiting. Approve adds it to the shared library on GitHub; Reject deletes it from this phone."
                        bar.removeAllViews()
                        if (pend.size > 1) bar.addView(Ui.button(ctx, "Approve all", true) { approve(pend.map { it.optString("id") }, status, ::reloadAfter) })
                        list.removeAllViews()
                        for (a in pend) list.addView(reviewRow(a, status))
                    }
                } catch (t: Throwable) { Bg.ui { status.text = "Daemon not reachable: ${t.message}" } }
            }
        }
        reviewRefresh = ::refresh
        env.open(scroll) { reviewRefresh = null; reload() }
        refresh()
    }

    private var reviewRefresh: (() -> Unit)? = null
    private fun reloadAfter() { reviewRefresh?.invoke() }

    private fun reviewRow(a: JSONObject, status: TextView): View {
        val id = a.optString("id")
        val row = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL; background = Ui.rounded(ctx, Ui.CARD)
            val p = Ui.dp(ctx, 10); setPadding(p, p, p, p)
            layoutParams = LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = Ui.dp(ctx, 8) }
        }
        val img = ImageView(ctx).apply { scaleType = ImageView.ScaleType.FIT_CENTER; background = Ui.rounded(ctx, Ui.CARD_ALT, 10) }
        row.addView(img, LinearLayout.LayoutParams(-1, Ui.dp(ctx, 180)))
        showStill(img, a)
        row.addView(Ui.text(ctx, id, 15f, Ui.TEXT, true), Ui.lp(top = 6, ctx = ctx))
        row.addView(Ui.muted(ctx, "${a.optString("category").substringAfter('_')} · ${a.optString("scope")} · ${tagsOf(a).joinToString(", ")}"))
        val btns = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL }
        btns.addView(Ui.button(ctx, "Approve", true) { approve(listOf(id), status, ::reloadAfter) },
            LinearLayout.LayoutParams(-2, -2).apply { rightMargin = Ui.dp(ctx, 8) })
        btns.addView(Ui.button(ctx, "Reject", false) { reject(id, status) })
        row.addView(btns, Ui.lp(top = 8, ctx = ctx))
        return row
    }

    private fun approve(ids: List<String>, status: TextView, done: () -> Unit) {
        status.text = "Syncing ${ids.size} asset(s) to GitHub..."
        Bg.io {
            try {
                val repoIdx = env.github.getRepoText("assets/library/library_index.json")?.let { JSONObject(it) }
                    ?: throw IllegalStateException("cannot read the repo library index (check the GitHub token)")
                val plan = env.api.reviewPlan(ids, repoIdx)
                val files = plan.getJSONArray("files")
                for (i in 0 until files.length()) {
                    val f = files.getJSONObject(i)
                    Bg.ui { status.text = "Uploading ${i + 1}/${files.length() + 1}: ${f.getString("path")}" }
                    val e = env.github.putFile("assets/library/" + f.getString("path"),
                        android.util.Base64.decode(f.getString("b64"), android.util.Base64.DEFAULT), "library: add forged ${ids.joinToString(",")}")
                    if (e != null) throw IllegalStateException(e)
                }
                val e = env.github.putFile("assets/library/library_index.json", plan.getJSONObject("index").toString(2).toByteArray(),
                    "library: index for forged ${ids.joinToString(",")}")
                if (e != null) throw IllegalStateException(e)
                env.api.reviewApproved(ids)
                Bg.ui { env.toast("Approved ${ids.size}"); done() }
            } catch (t: Throwable) { Bg.ui { status.text = "Approve failed: ${t.message}" } }
        }
    }

    private fun reject(id: String, status: TextView) {
        status.text = "Deleting $id..."
        Bg.io {
            try {
                val r = env.api.reviewReject(listOf(id))
                val blocked = r.optJSONObject("blocked")
                Bg.ui {
                    if (blocked != null && blocked.has(id)) status.text = "Can't reject $id: used by ${blocked.optJSONArray(id)?.join(", ")}"
                    else { env.toast("Rejected $id"); reloadAfter() }
                }
            } catch (t: Throwable) { Bg.ui { status.text = "Reject failed: ${t.message}" } }
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

    companion object {
        private const val STILL = 0
        private const val ANIM = 1
        private const val AUDIO = 2
    }
}
