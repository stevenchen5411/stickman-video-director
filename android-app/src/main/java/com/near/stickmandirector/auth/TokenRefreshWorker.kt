package com.near.stickmandirector.auth

import android.content.Context
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Worker
import androidx.work.WorkerParameters
import com.near.stickmandirector.bridge.TermuxClient
import com.near.stickmandirector.model.AuthMode
import com.near.stickmandirector.model.AuthResult
import java.util.concurrent.TimeUnit

/**
 * Periodic (every 30 min) job: refresh OAuth tokens that expire within 20 min, re-sync the encrypted
 * providers.json, and re-push plaintext keys to the daemon's memory (best effort; the daemon may be asleep).
 */
class TokenRefreshWorker(ctx: Context, params: WorkerParameters) : Worker(ctx, params) {
    override fun doWork(): Result {
        val store = SecureStore.get(applicationContext)
        val healer = AuthSelfHealer(applicationContext)
        val soon = System.currentTimeMillis() + 20 * 60 * 1000L
        var retry = false
        for (c in store.allCreds()) {
            if (c.mode == AuthMode.OAUTH && c.expiresAtMs in 1..soon) {
                when (val r = healer.refresh(c.name)) {
                    is AuthResult.Success -> Unit
                    is AuthResult.Failed -> if (r.reason.contains("network", true)) retry = true
                    else -> Unit
                }
            }
        }
        ProvidersStore.sync(applicationContext)
        runCatching { TermuxClient(applicationContext).pushKeysBlocking() }
        return if (retry) Result.retry() else Result.success()
    }

    companion object {
        private const val NAME = "stickman_token_refresh"
        fun schedule(ctx: Context) {
            val req = PeriodicWorkRequestBuilder<TokenRefreshWorker>(30, TimeUnit.MINUTES)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build()
            WorkManager.getInstance(ctx).enqueueUniquePeriodicWork(NAME, ExistingPeriodicWorkPolicy.KEEP, req)
        }
    }
}
