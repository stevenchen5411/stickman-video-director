package com.near.stickmandirector

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.widget.FrameLayout
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import com.near.stickmandirector.auth.SecureStore
import com.near.stickmandirector.bridge.BridgeService
import com.near.stickmandirector.gate.ConnectGateScreen
import com.near.stickmandirector.gate.TermuxDiagnostics
import com.near.stickmandirector.ui.BackScope
import com.near.stickmandirector.ui.Ui
import com.near.stickmandirector.workspace.MainWorkspaceView

/**
 * Single-activity host. Edge-to-edge shell, the mandatory connect gate, then the workspace.
 * Once the gate passes, the 4-tab workspace (Scout / Studio / Library / System) takes over.
 */
class MainActivity : Activity() {
    private lateinit var root: FrameLayout
    private lateinit var back: BackScope
    private var gate: ConnectGateScreen? = null
    private var workspace: MainWorkspaceView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)          // edge-to-edge (enforced on Android 16 anyway)
        window.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(Ui.BG))
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        WindowCompat.getInsetsController(window, window.decorView).apply {
            isAppearanceLightStatusBars = false; isAppearanceLightNavigationBars = false
        }

        back = BackScope(this)
        root = FrameLayout(this).apply { setBackgroundColor(Ui.BG) }
        ViewCompat.setOnApplyWindowInsetsListener(root) { v, wi ->
            val i = wi.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout() or WindowInsetsCompat.Type.ime())
            v.setPadding(i.left, i.top, i.right, i.bottom)
            WindowInsetsCompat.CONSUMED
        }
        setContentView(root)
        showGate()
        intent?.data?.let { gate?.handleAuthRedirect(it) }
    }

    private fun showGate(autoUnlock: Boolean = true) {
        back.release()
        workspace = null
        root.removeAllViews()
        val g = ConnectGateScreen(this, back, autoUnlock) { showWorkspace() }
        gate = g
        root.addView(g.view, FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
    }

    private fun showWorkspace() {
        back.release()
        gate = null
        root.removeAllViews()
        val w = MainWorkspaceView(this, back) { showGate(autoUnlock = false) }
        workspace = w
        // Claude web-session users need the loopback bridge alive for the Termux engine.
        if (SecureStore.get(this).loadCred("claude")?.cookies?.isNotEmpty() == true) {
            BridgeService.start(this)
            if (android.os.Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 4102)
            }
        }
        root.addView(w.view, FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        intent.data?.let { gate?.handleAuthRedirect(it) }
    }

    override fun onResume() {
        super.onResume()
        gate?.refreshAll()
        workspace?.onResume()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == TermuxDiagnostics.REQ_RUN_COMMAND && grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
            gate?.onPermissionResult()
        } else if (requestCode == TermuxDiagnostics.REQ_RUN_COMMAND) {
            gate?.onPermissionResult()
        }
    }

    @Deprecated("Used on API < 33; newer versions go through BackScope's OnBackInvokedCallback")
    override fun onBackPressed() {
        if (!back.handleBack()) super.onBackPressed()
    }

    override fun onDestroy() {
        back.release()
        super.onDestroy()
    }
}
