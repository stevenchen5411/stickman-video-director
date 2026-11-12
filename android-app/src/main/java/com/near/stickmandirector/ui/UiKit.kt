package com.near.stickmandirector.ui

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/** Programmatic UI helpers. No XML layouts anywhere in this app. */
object Ui {
    const val BG = 0xFF0E1116.toInt()
    const val CARD = 0xFF181D26.toInt()
    const val CARD_ALT = 0xFF202736.toInt()
    const val TEXT = 0xFFEAEFF7.toInt()
    const val MUTED = 0xFF8C98AD.toInt()
    const val ACCENT = 0xFF5B8CFF.toInt()
    const val OK = 0xFF3DDC84.toInt()
    const val WARN = 0xFFFFB84D.toInt()
    const val BAD = 0xFFFF5C6C.toInt()

    fun dp(ctx: Context, v: Int): Int = (v * ctx.resources.displayMetrics.density + 0.5f).toInt()

    fun rounded(ctx: Context, fill: Int, radiusDp: Int = 14, strokeColor: Int = 0, strokeDp: Int = 0): GradientDrawable =
        GradientDrawable().apply {
            setColor(fill)
            cornerRadius = dp(ctx, radiusDp).toFloat()
            if (strokeDp > 0) setStroke(dp(ctx, strokeDp), strokeColor)
        }

    fun text(ctx: Context, s: CharSequence, sizeSp: Float = 14f, color: Int = TEXT, bold: Boolean = false): TextView =
        TextView(ctx).apply {
            text = s
            textSize = sizeSp
            setTextColor(color)
            if (bold) setTypeface(typeface, Typeface.BOLD)
        }

    fun title(ctx: Context, s: CharSequence) = text(ctx, s, 22f, TEXT, true)
    fun muted(ctx: Context, s: CharSequence) = text(ctx, s, 13f, MUTED)

    fun card(ctx: Context): LinearLayout = LinearLayout(ctx).apply {
        orientation = LinearLayout.VERTICAL
        val p = dp(ctx, 14)
        setPadding(p, p, p, p)
        background = rounded(ctx, CARD)
    }

    fun button(ctx: Context, label: String, primary: Boolean = true, onClick: (View) -> Unit): TextView =
        TextView(ctx).apply {
            text = label
            textSize = 14f
            gravity = Gravity.CENTER
            isAllCaps = false
            setTypeface(typeface, Typeface.BOLD)
            setTextColor(if (primary) Color.WHITE else ACCENT)
            val h = dp(ctx, 12)
            setPadding(h * 2, h, h * 2, h)
            background = if (primary) rounded(ctx, ACCENT, 12)
            else rounded(ctx, Color.TRANSPARENT, 12, ACCENT, 1)
            isClickable = true
            setOnClickListener(onClick)
        }

    fun input(ctx: Context, hint: String, secret: Boolean = false): EditText = EditText(ctx).apply {
        this.hint = hint
        setHintTextColor(MUTED)
        setTextColor(TEXT)
        textSize = 14f
        setSingleLine(true)
        inputType = InputType.TYPE_CLASS_TEXT or
            (if (secret) InputType.TYPE_TEXT_VARIATION_PASSWORD else InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD)
        val p = dp(ctx, 12)
        setPadding(p, p, p, p)
        background = rounded(ctx, CARD_ALT, 10)
    }

    fun badge(ctx: Context, s: String, color: Int): TextView = text(ctx, s, 11f, color, true).apply {
        val h = dp(ctx, 8); val v = dp(ctx, 3)
        setPadding(h, v, h, v)
        background = rounded(ctx, (color and 0x00FFFFFF) or 0x26000000, 8)
    }

    fun lp(w: Int = ViewGroup.LayoutParams.MATCH_PARENT, h: Int = ViewGroup.LayoutParams.WRAP_CONTENT,
           top: Int = 0, ctx: Context? = null): LinearLayout.LayoutParams =
        LinearLayout.LayoutParams(w, h).apply { if (ctx != null) topMargin = dp(ctx, top) }

    fun spacer(ctx: Context, heightDp: Int): View = View(ctx).apply {
        layoutParams = LinearLayout.LayoutParams(1, dp(ctx, heightDp))
    }
}
