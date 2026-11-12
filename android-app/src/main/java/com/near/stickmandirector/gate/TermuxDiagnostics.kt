package com.near.stickmandirector.gate

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import com.near.stickmandirector.auth.ProvidersStore
import com.near.stickmandirector.bridge.TermuxClient
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.model.HealthReport

enum class DiagState { OK, WARN, FAIL }

data class DiagRow(val id: String, val title: String, val state: DiagState, val detail: String, val fixable: Boolean = false)

/**
 * The 4-point Termux diagnostic (+ all-files access, which providers.json sync needs):
 *   1. RUN_COMMAND permission   2. daemon reachable (wake via RUN_COMMAND)
 *   3. /health flags            4. wake-lock / battery exemption
 *   (+ token accepted, + all-files access)
 * [run] blocks (network); call it off the main thread. [fix] applies the fix for one row.
 */
class TermuxDiagnostics(private val ctx: Context) {
    private val termux = TermuxClient(ctx)
    var lastHealth: HealthReport = HealthReport(false)
        private set

    companion object {
        const val RUN_COMMAND_PERMISSION = "com.termux.permission.RUN_COMMAND"
        const val REQ_RUN_COMMAND = 4101
    }

    fun run(): List<DiagRow> {
        val rows = ArrayList<DiagRow>()

        // 1. RUN_COMMAND permission
        val installed = termux.termuxInstalled()
        val granted = ctx.checkSelfPermission(RUN_COMMAND_PERMISSION) == PackageManager.PERMISSION_GRANTED
        rows += when {
            !installed -> DiagRow("perm", "Termux app", DiagState.FAIL, "Termux is not installed (install it from F-Droid or GitHub, not Play Store)")
            !granted -> DiagRow("perm", "RUN_COMMAND permission", DiagState.FAIL, "Not granted yet. Tap Fix to allow Stickman to start the daemon.", true)
            else -> DiagRow("perm", "RUN_COMMAND permission", DiagState.OK, "Granted")
        }

        // 2. daemon reachable
        val h = termux.health()
        lastHealth = h
        rows += if (h.reachable) DiagRow("daemon", "Daemon on 127.0.0.1:8765", DiagState.OK, "Reachable (${h.status})")
        else DiagRow("daemon", "Daemon on 127.0.0.1:8765", DiagState.FAIL,
            "Not reachable (${h.error ?: "no answer"}). Fix will send start_daemon.sh to Termux; if setup was never run, use 'Copy 1-Line Setup'.", installed && granted)

        // 2b. token
        if (h.reachable) rows += if (h.authOk) DiagRow("token", "Daemon token", DiagState.OK, "Accepted")
        else DiagRow("token", "Daemon token", DiagState.FAIL, "Daemon was started with a different token. Fix restarts it.", true)

        // 3. health flags
        if (h.reachable) {
            val bad = h.flags.filterValues { !it }.keys
            rows += when {
                h.flags.isEmpty() -> DiagRow("flags", "Engine health", DiagState.WARN, "No flags reported")
                bad.isEmpty() -> DiagRow("flags", "Engine health", DiagState.OK, "python, ffmpeg, pycairo, yt-dlp, rea-video, storage: all OK")
                else -> DiagRow("flags", "Engine health", DiagState.WARN, "Missing: ${bad.joinToString()}. Re-run the 1-line setup in Termux.")
            }
        }

        // Claude web bridge (only relevant when the Claude provider is a web session)
        val claude = com.near.stickmandirector.auth.SecureStore.get(ctx).loadCred("claude")
        if (h.reachable && claude != null && claude.mode == com.near.stickmandirector.model.AuthMode.SESSION && claude.cookies.isNotEmpty()) {
            val cs = h.aiStatus["claude"]
            rows += when {
                cs == "needs_refresh" -> DiagRow("claude", "Claude web session", DiagState.FAIL, "Rejected (401/403). Use Refresh Session; work is failing over to the next provider.")
                h.claudeBridgeUp -> DiagRow("claude", "Claude web session", DiagState.OK, "Bridge running (app Chromium). State: ${cs ?: "ok"}")
                else -> DiagRow("claude", "Claude web session", DiagState.WARN, "App bridge is not running; the engine falls back to curl_cffi if installed. Open the app to start the bridge.")
            }
        }

        // 4. wake-lock / battery
        val pm = ctx.getSystemService(Context.POWER_SERVICE) as PowerManager
        val exempt = runCatching { pm.isIgnoringBatteryOptimizations(Defaults.TERMUX_PKG) }.getOrDefault(false)
        rows += if (exempt) DiagRow("wake", "Wake-lock / battery", DiagState.OK, "Termux is exempt from battery optimisation")
        else DiagRow("wake", "Wake-lock / battery", DiagState.WARN,
            "Android may kill Termux mid-render. Fix acquires termux-wake-lock and opens battery settings.", true)

        // all-files access
        rows += if (ProvidersStore.hasAllFilesAccess()) DiagRow("storage", "All-files access", DiagState.OK, "Granted (shared StickmanDirector folder)")
        else DiagRow("storage", "All-files access", DiagState.FAIL, "Needed to write config/providers.json and read renders.", true)

        return rows
    }

    /** Apply the fix for a row. Network/IPC part runs on the calling thread; Settings screens launch on [activity]. */
    fun fix(activity: Activity, id: String): String = when (id) {
        "perm" -> { activity.requestPermissions(arrayOf(RUN_COMMAND_PERMISSION), REQ_RUN_COMMAND); "Permission dialog opened" }
        "daemon" -> termux.wake(false).message
        "token" -> termux.wake(true).message
        "wake" -> {
            val w = termux.wakeLock()
            runCatching { activity.startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)) }
            w.message + "; battery settings opened (set Termux to Unrestricted)"
        }
        "storage" -> {
            if (Build.VERSION.SDK_INT >= 30) {
                val i = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, Uri.parse("package:${ctx.packageName}"))
                runCatching { activity.startActivity(i) }.onFailure {
                    runCatching { activity.startActivity(Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)) }
                }
            }
            "All-files access settings opened"
        }
        else -> "Nothing to fix"
    }
}
