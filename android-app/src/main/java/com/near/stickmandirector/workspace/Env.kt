package com.near.stickmandirector.workspace

import android.app.Activity
import android.view.View
import android.widget.Toast
import com.near.stickmandirector.auth.SecureStore
import com.near.stickmandirector.bridge.DaemonApi
import com.near.stickmandirector.bridge.GitHubApiClient
import com.near.stickmandirector.ui.BottomSheet

/** Shared services handed to every tab / sub-screen. */
class Env(
    val activity: Activity,
    val api: DaemonApi,
    val github: GitHubApiClient,
    val store: SecureStore,
    val sheet: BottomSheet,
    private val openScreen: (View, () -> Unit) -> Unit,
    private val closeScreen: () -> Unit,
    val onQueueChanged: () -> Unit,
    val onReconnect: () -> Unit,
) {
    /** Push a full-screen sub-screen. [onClosed] runs when it is popped (back gesture or [close]). */
    fun open(screen: View, onClosed: () -> Unit = {}) = openScreen(screen, onClosed)
    fun close() = closeScreen()
    fun toast(s: String) = Toast.makeText(activity, s, Toast.LENGTH_SHORT).show()
}

/** One bottom-nav tab. [onShow] is called each time the tab becomes visible, [onHide] when it is left or the app pauses. */
abstract class Tab(protected val env: Env) {
    abstract val title: String
    abstract val view: View
    open fun onShow() {}
    open fun onHide() {}
}
