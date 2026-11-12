package com.near.stickmandirector.workspace

import android.content.Context
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import com.near.stickmandirector.ui.Ui

/** Standard sub-screen chrome: back button + title over [body]. */
object Screen {
    fun frame(ctx: Context, title: String, onBack: () -> Unit, body: View, trailing: View? = null): View =
        LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Ui.BG)
            isClickable = true                     // swallow touches so the tab below is inert
            val bar = LinearLayout(ctx).apply {
                orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
                val p = Ui.dp(ctx, 8); setPadding(p, p, p, p)
            }
            bar.addView(Ui.button(ctx, "‹ Back", false) { onBack() })
            bar.addView(Ui.text(ctx, title, 17f, Ui.TEXT, true).apply { setPadding(Ui.dp(ctx, 12), 0, 0, 0) },
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            if (trailing != null) bar.addView(trailing)
            addView(bar)
            addView(body, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        }
}
