package com.near.stickmandirector.auth

import android.os.Handler
import android.os.Looper
import java.util.concurrent.Executors

/** Tiny threading helper (executors + main Handler; no coroutines). */
object Bg {
    private val pool = Executors.newFixedThreadPool(3)
    private val main = Handler(Looper.getMainLooper())

    fun io(block: () -> Unit) { pool.execute { try { block() } catch (t: Throwable) { android.util.Log.e("Bg", "task failed", t) } } }
    fun ui(block: () -> Unit) { if (Looper.myLooper() == Looper.getMainLooper()) block() else main.post(block) }
    fun uiDelayed(ms: Long, block: () -> Unit) { main.postDelayed(block, ms) }
}
