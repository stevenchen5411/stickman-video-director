package com.near.stickmandirector.auth

import android.content.Context
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.model.ProviderCred

/**
 * Phone-side mirror of engine/llm.py failover: when a provider answers 429, put it in cooldown and hop to the
 * next usable one (claude -> gemini -> chatgpt by default). Cooldowns persist in SecureStore, so the
 * providers.json written for the daemon carries the same state.
 */
class ProviderFailoverPool(ctx: Context) {
    private val store = SecureStore.get(ctx)

    companion object {
        const val DEFAULT_COOLDOWN_MS = 15 * 60 * 1000L
        const val MAX_COOLDOWN_MS = 6 * 60 * 60 * 1000L
    }

    fun order(): List<String> = Defaults.PROVIDERS

    /** Usable providers not in cooldown, in failover order. */
    fun active(now: Long = System.currentTimeMillis()): List<ProviderCred> =
        order().mapNotNull { store.loadCred(it) }.filter { it.usable && it.cooldownUntilMs <= now }

    fun current(now: Long = System.currentTimeMillis()): ProviderCred? = active(now).firstOrNull()

    /** Record a 429 (retryAfterSec from the Retry-After header if any) and return the next provider to hop to. */
    fun report429(provider: String, retryAfterSec: Long? = null, now: Long = System.currentTimeMillis()): ProviderCred? {
        val c = store.loadCred(provider)
        if (c != null) {
            val ms = ((retryAfterSec ?: 0L) * 1000L).takeIf { it > 0 } ?: DEFAULT_COOLDOWN_MS
            store.saveCred(c.copy(cooldownUntilMs = now + ms.coerceAtMost(MAX_COOLDOWN_MS)))
        }
        return active(now).firstOrNull { it.name != provider }
    }

    fun clearCooldown(provider: String) {
        store.loadCred(provider)?.let { store.saveCred(it.copy(cooldownUntilMs = 0L)) }
    }

    /** Seconds until some provider becomes usable again, or 0 if one is available now. */
    fun secondsUntilAvailable(now: Long = System.currentTimeMillis()): Long {
        if (active(now).isNotEmpty()) return 0L
        val next = order().mapNotNull { store.loadCred(it) }.filter { it.usable }.minOfOrNull { it.cooldownUntilMs } ?: return -1L
        return ((next - now) / 1000L).coerceAtLeast(1L)
    }
}
