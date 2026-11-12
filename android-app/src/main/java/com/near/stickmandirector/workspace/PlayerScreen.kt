package com.near.stickmandirector.workspace

import android.media.MediaScannerConnection
import android.os.Environment
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.MediaController
import android.widget.VideoView
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.ui.Ui
import java.io.File

/** In-app video player for rendered MP4s (draft or HD) with a "Save" action that exports the file to Downloads. */
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
        val save = Ui.button(ctx, "Save", false) { saveToDownloads(env, file) }
        return Screen.frame(ctx, title, { env.close() }, box, save)
    }

    /** Copies the MP4 to Downloads/StickmanDirector (all-files access is already granted by the gate). */
    private fun saveToDownloads(env: Env, src: File) {
        env.toast("Saving...")
        Bg.io {
            try {
                val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "StickmanDirector")
                dir.mkdirs()
                val dst = File(dir, src.name)
                src.copyTo(dst, overwrite = true)
                MediaScannerConnection.scanFile(env.activity, arrayOf(dst.absolutePath), arrayOf("video/mp4"), null)
                Bg.ui { env.toast("Saved: Downloads/StickmanDirector/${dst.name}") }
            } catch (t: Throwable) {
                Bg.ui { env.toast("Save failed: ${t.message}") }
            }
        }
    }
}
