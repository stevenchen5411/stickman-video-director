package com.near.stickmandirector.workspace

import android.text.InputType
import android.view.View
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.ui.Ui
import org.json.JSONObject

/**
 * Edits one scene. Changes are applied to a copy of the package and saved through PUT /queue/{id}, so the engine
 * re-audits (75% motion gate), validates, and rejects unknown library ids or stage directions in narration.
 */
class StoryboardEditorView(
    private val env: Env,
    original: JSONObject,
    private val index: Int,
    private val onSaved: (JSONObject) -> Unit,
) {
    private val ctx = env.activity
    private val pkg = JSONObject(original.toString())
    private val scene: JSONObject = pkg.getJSONArray("scenes").getJSONObject(index)
    private val id = pkg.getString("package_id")
    private val library = HashMap<String, List<String>>()          // category -> asset ids

    private class Choice(val label: String, val category: String, val nullable: Boolean,
                         val get: () -> String?, val set: (String?) -> Unit) { lateinit var btn: TextView }
    private val choices: List<Choice>

    private val narration = Ui.input(ctx, "Narration (spoken words only)").apply {
        setSingleLine(false); minLines = 3; inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        setText(scene.getJSONObject("narration").optString("text"))
    }
    private val acting = Ui.input(ctx, "Acting direction").apply {
        setSingleLine(false); minLines = 2; inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        setText(scene.getJSONObject("narration").getJSONObject("prosody").optString("acting_direction"))
    }
    private val pace = Ui.input(ctx, "Pace 0.5 - 2.0").apply {
        inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL
        setText(scene.getJSONObject("narration").getJSONObject("prosody").optDouble("pace_multiplier", 1.0).toString())
    }
    private val msg: TextView = Ui.text(ctx, "", 13f, Ui.BAD)

    val view: View

    private fun opt(o: JSONObject, k: String): String? = if (o.isNull(k) || !o.has(k)) null else o.optString(k).ifBlank { null }
    private fun put(o: JSONObject, k: String, v: String?) { o.put(k, v ?: JSONObject.NULL) }

    init {
        val ch = scene.getJSONObject("character"); val env2 = scene.getJSONObject("environment")
        val va = scene.getJSONObject("visual_aid"); val nar = scene.getJSONObject("narration")
        choices = listOf(
            Choice("Character", "01_characters", false, { opt(ch, "character_id") }, { put(ch, "character_id", it) }),
            Choice("Pose", "02_poses", false, { opt(ch, "pose_id") }, { put(ch, "pose_id", it) }),
            Choice("Expression", "03_expressions", false, { opt(ch, "expression_id") }, { put(ch, "expression_id", it) }),
            Choice("Motion", "04_motions", true, { opt(ch, "motion_id") }, { put(ch, "motion_id", it) }),
            Choice("Background", "05_scenes", false, { opt(env2, "scene_id") }, { put(env2, "scene_id", it) }),
            Choice("Transition in", "09_transitions", true, { opt(env2, "transition_in_id") }, { put(env2, "transition_in_id", it) }),
            Choice("Prop", "06_props", true, { opt(va, "prop_id") }, { put(va, "prop_id", it) }),
            Choice("Widget", "07_widgets", true, { opt(va, "widget_id") }, { put(va, "widget_id", it) }),
            Choice("Overlay", "08_overlays", true, { opt(va, "overlay_id") }, { put(va, "overlay_id", it) }),
            Choice("Voice", "12_voices", false, { opt(nar, "voice_profile_id") }, { put(nar, "voice_profile_id", it) }),
        )

        val col = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL; val p = Ui.dp(ctx, 16); setPadding(p, p, p, p * 2) }
        col.addView(Ui.muted(ctx, "Scene ${index + 1} of ${pkg.getJSONArray("scenes").length()}"))
        col.addView(Ui.text(ctx, "Narration", 14f, Ui.TEXT, true), Ui.lp(top = 12, ctx = ctx))
        col.addView(narration, Ui.lp(top = 6, ctx = ctx))
        col.addView(Ui.text(ctx, "Acting direction", 14f, Ui.TEXT, true), Ui.lp(top = 12, ctx = ctx))
        col.addView(acting, Ui.lp(top = 6, ctx = ctx))
        col.addView(Ui.text(ctx, "Pace", 14f, Ui.TEXT, true), Ui.lp(top = 12, ctx = ctx))
        col.addView(pace, Ui.lp(top = 6, ctx = ctx))
        col.addView(Ui.text(ctx, "Assets", 14f, Ui.TEXT, true), Ui.lp(top = 16, ctx = ctx))
        for (c in choices) {
            val row = LinearLayout(ctx).apply { orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL }
            row.addView(Ui.muted(ctx, c.label), LinearLayout.LayoutParams(0, -2, 1f))
            c.btn = Ui.button(ctx, c.get() ?: "none", false) { pick(c) }
            row.addView(c.btn, LinearLayout.LayoutParams(0, -2, 2f))
            col.addView(row, Ui.lp(top = 6, ctx = ctx))
        }
        col.addView(msg, Ui.lp(top = 12, ctx = ctx))
        col.addView(Ui.button(ctx, "Save scene") { save() }, Ui.lp(top = 8, ctx = ctx))
        view = Screen.frame(ctx, "Scene ${index + 1}", { env.close() }, ScrollView(ctx).apply { addView(col) })

        Bg.io {   // library ids for the choosers
            try {
                val all = env.api.library()
                val grouped = all.groupBy({ it.optString("category") }, { it.optString("id") })
                Bg.ui { library.putAll(grouped) }
            } catch (t: Throwable) { Bg.ui { msg.text = "Library not loaded: ${t.message}" } }
        }
    }

    private fun pick(c: Choice) {
        val ids = library[c.category]
        if (ids == null) { env.toast("Library still loading"); return }
        val box = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
        box.addView(Ui.text(ctx, c.label, 18f, Ui.TEXT, true))
        val list = LinearLayout(ctx).apply { orientation = LinearLayout.VERTICAL }
        val options = (if (c.nullable) listOf<String?>(null) else emptyList()) + ids.sorted()
        for (o in options) {
            val cur = o == c.get()
            list.addView(Ui.button(ctx, (o ?: "none") + if (cur) "  ✓" else "", cur) {
                c.set(o); c.btn.text = o ?: "none"; env.sheet.dismiss()
            }, Ui.lp(top = 6, ctx = ctx))
        }
        box.addView(ScrollView(ctx).apply { addView(list) }, LinearLayout.LayoutParams(-1, Ui.dp(ctx, 360)))
        env.sheet.show(box)
    }

    private fun save() {
        val nar = scene.getJSONObject("narration"); val pro = nar.getJSONObject("prosody")
        val text = narration.text.toString().trim()
        if (text.isEmpty()) { msg.text = "Narration cannot be empty"; return }
        nar.put("text", text)
        pro.put("acting_direction", acting.text.toString().trim())
        pro.put("pace_multiplier", (pace.text.toString().toDoubleOrNull() ?: 1.0).coerceIn(0.5, 2.0))
        msg.text = "Saving..."; msg.setTextColor(Ui.MUTED)
        Bg.io {
            try {
                val res = env.api.savePkg(id, pkg)
                val fresh = env.api.pkg(id)
                val passed = res.getJSONObject("quality_audit").optBoolean("passed")
                Bg.ui {
                    env.toast(if (passed) "Saved. Audit passed." else "Saved. Audit not passed yet.")
                    onSaved(fresh); env.close()
                }
            } catch (t: Throwable) {
                Bg.ui { msg.setTextColor(Ui.BAD); msg.text = (t.message ?: "Save failed").take(300) }
            }
        }
    }
}
