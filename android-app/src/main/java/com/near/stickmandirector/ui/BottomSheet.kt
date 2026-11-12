package com.near.stickmandirector.ui

import android.content.Context
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout

/** In-activity modal bottom sheet (scrim + rounded card). While open it owns the back gesture via [BackScope]. */
class BottomSheet(private val ctx: Context, private val host: FrameLayout, private val back: BackScope) {
    private var root: FrameLayout? = null
    private val closer: () -> Unit = { dismiss() }
    val isShowing: Boolean get() = root != null

    fun show(content: View) {
        if (root != null) dismiss()
        val scrim = FrameLayout(ctx).apply {
            setBackgroundColor(0x99000000.toInt())
            isClickable = true
            setOnClickListener { dismiss() }
        }
        val card = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            val p = Ui.dp(ctx, 18); setPadding(p, p, p, p)
            val r = Ui.dp(ctx, 22).toFloat()
            background = Ui.rounded(ctx, Ui.CARD).apply { cornerRadii = floatArrayOf(r, r, r, r, 0f, 0f, 0f, 0f) }
            isClickable = true
            addView(content)
        }
        scrim.addView(card, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM))
        host.addView(scrim, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        root = scrim
        back.push(closer)
    }

    fun dismiss() {
        val r = root ?: return
        root = null
        host.removeView(r)
        back.remove(closer)
    }
}
