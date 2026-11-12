package com.near.stickmandirector.bridge

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.content.ContextCompat
import com.near.stickmandirector.auth.Bg

/**
 * Foreground service that keeps the claude.ai bridge alive while the engine works in Termux
 * (Android would otherwise freeze the app and the hidden WebView).
 */
class BridgeService : Service() {
    private var host: ClaudeWebHost? = null
    private var server: LocalBridgeServer? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.createNotificationChannel(NotificationChannel("bridge", "Claude bridge", NotificationManager.IMPORTANCE_LOW))
        val n = Notification.Builder(this, "bridge")
            .setContentTitle("Stickman Director")
            .setContentText("Claude web bridge on 127.0.0.1:${LocalBridgeServer.PORT}")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setOngoing(true).build()
        if (Build.VERSION.SDK_INT >= 34) startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE) else startForeground(7, n)
        Bg.ui {
            val h = ClaudeWebHost(this)
            host = h
            server = LocalBridgeServer(this, h).also { it.start() }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onDestroy() {
        server?.stop(); server = null
        Bg.ui { host?.destroy(); host = null }
        super.onDestroy()
    }

    companion object {
        fun start(ctx: Context) {
            runCatching { ContextCompat.startForegroundService(ctx, Intent(ctx, BridgeService::class.java)) }
        }
        fun stop(ctx: Context) { ctx.stopService(Intent(ctx, BridgeService::class.java)) }
    }
}
