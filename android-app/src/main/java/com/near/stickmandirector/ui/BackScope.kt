package com.near.stickmandirector.ui

import android.app.Activity
import android.os.Build
import android.window.OnBackInvokedCallback
import android.window.OnBackInvokedDispatcher

/**
 * Registers an OnBackInvokedCallback ONLY while at least one sub-screen or modal sheet is open, so the
 * system back gesture keeps its default (predictive, exit-app) behaviour on the root screen.
 * On API < 33 MainActivity forwards onBackPressed() to [handleBack].
 */
class BackScope(private val activity: Activity) {
    private val stack = ArrayList<() -> Unit>()
    private var callback: Any? = null

    val isActive: Boolean get() = stack.isNotEmpty()

    fun push(handler: () -> Unit) { stack.add(handler); sync() }
    fun remove(handler: () -> Unit) { stack.remove(handler); sync() }

    /** Runs the top-most handler (it is expected to remove itself). Returns false if nothing is open. */
    fun handleBack(): Boolean {
        val h = stack.lastOrNull() ?: return false
        h(); return true
    }

    fun release() { stack.clear(); sync() }

    private fun sync() {
        if (Build.VERSION.SDK_INT < 33) return
        val d = activity.onBackInvokedDispatcher
        if (stack.isNotEmpty() && callback == null) {
            val cb = OnBackInvokedCallback { handleBack() }
            callback = cb
            d.registerOnBackInvokedCallback(OnBackInvokedDispatcher.PRIORITY_DEFAULT, cb)
        } else if (stack.isEmpty() && callback != null) {
            d.unregisterOnBackInvokedCallback(callback as OnBackInvokedCallback)
            callback = null
        }
    }
}
