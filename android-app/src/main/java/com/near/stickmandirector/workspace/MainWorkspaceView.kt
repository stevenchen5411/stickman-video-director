package com.near.stickmandirector.workspace

import android.app.Activity
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import com.near.stickmandirector.auth.AuthSelfHealer
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.auth.ProvidersStore
import com.near.stickmandirector.auth.SecureStore
import com.near.stickmandirector.auth.WebViewSnifferDialog
import com.near.stickmandirector.bridge.BridgeService
import com.near.stickmandirector.bridge.DaemonApi
import com.near.stickmandirector.bridge.GitHubApiClient
import com.near.stickmandirector.tabs.LibraryTab
import com.near.stickmandirector.tabs.ScoutTab
import com.near.stickmandirector.tabs.StudioTab
import com.near.stickmandirector.tabs.SystemTab
import com.near.stickmandirector.ui.BackScope
import com.near.stickmandirector.ui.BottomSheet
import com.near.stickmandirector.ui.Ui

/**
 * The unlocked app: 4 tabs (Scout / Studio / Library / System) + a stack of full-screen sub-screens.
 * While any sub-screen or sheet is open, BackScope owns the back gesture; otherwise it is not registered.
 */
class MainWorkspaceView(
    private val activity: Activity,
    private val back: BackScope,
    onReconnect: () -> Unit,
) {
    val view = FrameLayout(activity)
    private val stage = FrameLayout(activity)
    private val nav = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
    private val navItems = ArrayList<TextView>()
    private val screens = ArrayList<Triple<View, () -> Unit, () -> Unit>>()   // view, onClosed, back handler
    private val sheet = BottomSheet(activity, view, back)
    private val banner = LinearLayout(activity).apply {
        orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; visibility = View.GONE
        val p = Ui.dp(activity, 10); setPadding(p, p, p, p)
        background = Ui.rounded(activity, 0xFF3A2A12.toInt(), 12)
    }

    private val env: Env
    private val tabs: List<Tab>
    private var current = -1

    init {
        val storeRef = SecureStore.get(activity)
        env = Env(activity, DaemonApi(activity), GitHubApiClient(activity), storeRef, sheet,
            { v, closed -> pushScreen(v, closed) }, { popScreen() },
            { (tabs.getOrNull(1) as? StudioTab)?.reload() }, onReconnect)
        tabs = listOf(ScoutTab(env), StudioTab(env), LibraryTab(env), SystemTab(env))

        val column = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        banner.addView(Ui.text(activity, "Claude session expired. Work is using the next provider.", 13f, Ui.WARN, true),
            LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        banner.addView(Ui.button(activity, "Refresh Session", true) { refreshSession() })
        column.addView(banner, Ui.lp(top = 6, ctx = activity).apply { leftMargin = Ui.dp(activity, 10); rightMargin = Ui.dp(activity, 10) })
        column.addView(stage, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        nav.setBackgroundColor(Ui.CARD)
        tabs.forEachIndexed { i, t ->
            val item = Ui.text(activity, t.title, 13f, Ui.MUTED, true).apply {
                gravity = Gravity.CENTER
                val p = Ui.dp(activity, 14); setPadding(0, p, 0, p)
                setOnClickListener { select(i) }
            }
            navItems.add(item)
            nav.addView(item, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        }
        column.addView(nav)
        view.addView(column, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        select(1)                                   // open on Studio
        pollBanner()
    }

    /** Shows a 1-tap "Refresh Session" badge while the engine reports the Claude web session as needing a re-login. */
    fun checkBanner() {
        Bg.io {
            val need = env.api.client.health().aiStatus["claude"] == "needs_refresh"
            Bg.ui { banner.visibility = if (need) View.VISIBLE else View.GONE }
        }
    }

    private fun pollBanner() {
        Bg.uiDelayed(30_000) { if (view.isAttachedToWindow) { checkBanner(); pollBanner() } }
    }

    private fun refreshSession() {
        val healer = AuthSelfHealer(activity)
        val ep = healer.bundled("claude") ?: return
        WebViewSnifferDialog(activity, ep,
            onCaptured = { cap ->
                healer.saveSession("claude", cap.cookies, cap.userAgent, cap.orgId)
                BridgeService.stop(activity); BridgeService.start(activity)      // reload the hidden WebView with the new jar
                Bg.io { ProvidersStore.sync(activity); env.api.client.pushKeysBlocking(); Bg.ui { checkBanner() } }
                env.toast("Session refreshed")
            },
            onFallbackToKey = { env.onReconnect() }).show()
    }

    fun select(i: Int) {
        if (i == current) return
        tabs.getOrNull(current)?.onHide()
        current = i
        stage.removeAllViews()
        stage.addView(tabs[i].view, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        navItems.forEachIndexed { k, tv -> tv.setTextColor(if (k == i) Ui.ACCENT else Ui.MUTED) }
        tabs[i].onShow()
    }

    fun onResume() { if (current >= 0 && screens.isEmpty()) tabs[current].onShow(); checkBanner() }

    fun onPause() { tabs.getOrNull(current)?.onHide() }

    private fun pushScreen(v: View, onClosed: () -> Unit) {
        lateinit var handler: () -> Unit
        handler = { popScreen() }
        screens.add(Triple(v, onClosed, handler))
        // Screens go below the bottom sheet host layer but above the tabs.
        view.addView(v, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        back.push(handler)
    }

    private fun popScreen() {
        val top = screens.removeLastOrNull() ?: return
        view.removeView(top.first)
        back.remove(top.third)
        top.second()
    }
}
