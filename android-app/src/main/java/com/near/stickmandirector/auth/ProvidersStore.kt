package com.near.stickmandirector.auth

import android.content.Context
import android.os.Build
import android.os.Environment
import com.near.stickmandirector.model.AuthMode
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.model.ProviderCred
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

/**
 * Writes shared-storage config/providers.json in the exact shape engine/schemas.py validates
 * (extra="forbid"). Secret values are Keystore ciphertext (`enc_v1:`), unreadable in Termux, so the
 * plaintext is ALSO pushed to the daemon's memory via POST /config/keys (see TermuxClient.pushKeys).
 */
object ProvidersStore {
    fun hasAllFilesAccess(): Boolean =
        Build.VERSION.SDK_INT < 30 || Environment.isExternalStorageManager()

    fun file(): File = File(Defaults.STORAGE_DIR, "config/providers.json")

    private fun iso(ms: Long): Any =
        if (ms <= 0L) JSONObject.NULL else SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
            .apply { timeZone = TimeZone.getTimeZone("UTC") }.format(Date(ms))

    private fun enc(v: String?): Any = if (v.isNullOrBlank()) JSONObject.NULL else KeystoreCrypto.encrypt(v)

    private fun wireMode(p: String, c: ProviderCred, hasOauth: Boolean): String = when (p) {
        "claude" -> when (c.mode) { AuthMode.API_KEY -> "api_key"; AuthMode.SESSION -> "cookie_session"; else -> "oauth_session" }
        "gemini" -> when {
            c.mode == AuthMode.API_KEY && !hasOauth -> "api_key"
            c.mode == AuthMode.OAUTH && c.apiKey.isNullOrBlank() -> "oauth"
            else -> "api_key_and_oauth"
        }
        else -> when (c.mode) { AuthMode.API_KEY -> "api_key"; AuthMode.SESSION -> "cookie_session"; else -> "oauth_pkce" }
    }

    fun build(creds: List<ProviderCred>, order: List<String> = Defaults.PROVIDERS): JSONObject {
        val provs = JSONObject()
        for (c in creds) {
            val o = JSONObject()
            o.put("enabled", c.enabled && c.usable)
            o.put("auth_mode", wireMode(c.name, c, !c.accessToken.isNullOrBlank()))
            o.put("api_key", enc(c.apiKey))
            o.put("access_token", enc(c.accessToken))
            if (c.name == "claude") o.put("endpoint", c.orgId?.let { "https://claude.ai/api/organizations/$it" } ?: JSONObject.NULL)
            if (c.name != "claude") o.put("refresh_token", enc(c.refreshToken))
            if (c.name != "gemini") {
                val ck = JSONObject(); c.cookies.forEach { (k, v) -> ck.put(k, KeystoreCrypto.encrypt(v)) }
                o.put("cookies", ck); o.put("user_agent", c.userAgent ?: JSONObject.NULL)
            }
            o.put("expires_at_utc", iso(c.expiresAtMs))
            o.put("cooldown_until_utc", iso(c.cooldownUntilMs))
            provs.put(c.name, o)
        }
        return JSONObject().put("schema_version", "1.0").put("failover_order", JSONArray(order)).put("providers", provs)
    }

    /** Returns null on success or a human-readable reason. */
    fun sync(ctx: Context, order: List<String> = Defaults.PROVIDERS): String? {
        if (!hasAllFilesAccess()) return "All-files access not granted"
        return try {
            val f = file(); f.parentFile?.mkdirs()
            val tmp = File(f.parentFile, "providers.json.tmp")
            tmp.writeText(build(SecureStore.get(ctx).allCreds(), order).toString(2))
            if (!tmp.renameTo(f)) { f.writeText(tmp.readText()); tmp.delete() }
            null
        } catch (t: Throwable) { t.message ?: t.javaClass.simpleName }
    }

    /** Plaintext keys for the in-memory daemon push: API keys, or OAuth access tokens as a fallback. */
    fun runtimeKeys(ctx: Context): Map<String, String> {
        val out = mutableMapOf<String, String>()
        for (c in SecureStore.get(ctx).allCreds()) {
            if (!c.usable) continue
            val k = c.apiKey?.takeIf { it.isNotBlank() }
            if (k != null) out[c.name] = k
        }
        return out
    }
}
