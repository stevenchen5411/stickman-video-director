package com.near.stickmandirector.workspace

import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.MediaController
import android.widget.VideoView
import java.io.File

/** Minimal in-app video player for rendered MP4s (draft or HD). */
object PlayerScreen {
    fun build(env: Env, file: File, title: String): View {
        val ctx = env.activity
        val vv = VideoView(ctx)
        val box = FrameLayout(ctx).apply { setBackgroundColor(0xFF000000.toInt()) }
        box.addView(vv, FrameLayout.LayoutParams(-1, -1, Gravity.CENTER))
        vv.setMediaController(MediaController(ctx).also { it.setAnchorView(box) })
        vv.setOnErrorListener { _, _, _ -> env.toast("Cannot play ${file.name}"); true }
        vv.setVideoPath(file.absolutePath)
        vv.setOnPreparedListener { it.isLooping = false; vv.start() }
        return Screen.frame(ctx, title, { env.close() }, box)
    }
}
