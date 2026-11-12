package com.near.stickmandirector.model

import org.json.JSONArray
import org.json.JSONObject

/** Plain org.json models mirroring engine/schemas.py (no serialization plugin). */
object Defaults {
    const val DAEMON_URL = "http://127.0.0.1:8775"
    const val STORAGE_DIR = "/storage/emulated/0/StickmanDirector"
    const val TERMUX_PKG = "com.termux"
    const val TERMUX_HOME = "/data/data/com.termux/files/home"
    const val TERMUX_BASH = "/data/data/com.termux/files/usr/bin/bash"
    const val LAUNCHER = "$TERMUX_HOME/.stickman/start_daemon.sh"
    const val DEFAULT_REPO = "stevenchen5411/stickman-video-director"
    const val SETUP_ONE_LINER =
        "pkg install -y git curl && git clone https://github.com/stevenchen5411/stickman-video-director " +
            "~/stickman-video-director && bash ~/stickman-video-director/bootstrap/setup_termux.sh"
    val PROVIDERS = listOf("claude", "gemini", "chatgpt")
}

enum class AuthMode(val wire: String) {
    OAUTH("oauth"), SESSION("cookie_session"), API_KEY("api_key"), NONE("none")
}

/** Per-provider credentials as held on the phone (encrypted at rest by SecureStore). */
data class ProviderCred(
    val name: String,
    val mode: AuthMode = AuthMode.NONE,
    val apiKey: String? = null,
    val accessToken: String? = null,
    val refreshToken: String? = null,
    val cookies: Map<String, String> = emptyMap(),
    val userAgent: String? = null,
    val expiresAtMs: Long = 0L,
    val cooldownUntilMs: Long = 0L,
    val enabled: Boolean = true,
    val orgId: String? = null,
) {
    val usable: Boolean
        get() = enabled && (!apiKey.isNullOrBlank() ||
            (!accessToken.isNullOrBlank() && (expiresAtMs == 0L || expiresAtMs > System.currentTimeMillis())) ||
            cookies.isNotEmpty())

    fun toJson(): JSONObject = JSONObject().apply {
        put("name", name); put("mode", mode.wire)
        put("apiKey", apiKey ?: JSONObject.NULL)
        put("accessToken", accessToken ?: JSONObject.NULL)
        put("refreshToken", refreshToken ?: JSONObject.NULL)
        put("cookies", JSONObject(cookies))
        put("userAgent", userAgent ?: JSONObject.NULL)
        put("expiresAtMs", expiresAtMs); put("cooldownUntilMs", cooldownUntilMs); put("enabled", enabled)
        put("orgId", orgId ?: JSONObject.NULL)
    }

    companion object {
        fun fromJson(o: JSONObject): ProviderCred {
            val ck = mutableMapOf<String, String>()
            o.optJSONObject("cookies")?.let { c -> c.keys().forEach { k -> ck[k] = c.optString(k) } }
            val wire = o.optString("mode", "none")
            return ProviderCred(
                name = o.getString("name"),
                mode = AuthMode.values().firstOrNull { it.wire == wire } ?: AuthMode.NONE,
                apiKey = o.optStringOrNull("apiKey"), accessToken = o.optStringOrNull("accessToken"),
                refreshToken = o.optStringOrNull("refreshToken"), cookies = ck,
                userAgent = o.optStringOrNull("userAgent"),
                expiresAtMs = o.optLong("expiresAtMs", 0L), cooldownUntilMs = o.optLong("cooldownUntilMs", 0L),
                enabled = o.optBoolean("enabled", true), orgId = o.optStringOrNull("orgId"),
            )
        }
    }
}

fun JSONObject.optStringOrNull(k: String): String? =
    if (isNull(k) || !has(k)) null else optString(k).ifBlank { null }

/** Endpoint spec from .github/auth_endpoints.json (Layer 2) or the bundled default. */
data class AuthEndpoints(
    val provider: String,
    val displayName: String,
    val metadataUrls: List<String>,
    val authorizationEndpoint: String?,
    val tokenEndpoint: String?,
    val clientId: String?,
    val scopes: List<String>,
    val redirectUri: String,
    val webLoginUrl: String,
    val apiBase: String?,
    val cookieDomains: List<String>,
    val sessionCookieNames: List<String>,
    val cloudflareCookieNames: List<String>,
    val apiKeyConsoleUrl: String?,
) {
    companion object {
        private fun JSONArray?.strings(): List<String> =
            if (this == null) emptyList() else (0 until length()).map { getString(it) }

        fun fromJson(name: String, o: JSONObject) = AuthEndpoints(
            provider = name,
            displayName = o.optString("display_name", name),
            metadataUrls = o.optJSONArray("metadata_urls").strings(),
            authorizationEndpoint = o.optStringOrNull("authorization_endpoint"),
            tokenEndpoint = o.optStringOrNull("token_endpoint"),
            clientId = o.optStringOrNull("client_id"),
            scopes = o.optJSONArray("scopes").strings(),
            redirectUri = o.optString("redirect_uri", "com.near.stickmandirector://oauth/$name"),
            webLoginUrl = o.optString("web_login_url", ""),
            apiBase = o.optStringOrNull("api_base"),
            cookieDomains = o.optJSONArray("cookie_domains").strings(),
            sessionCookieNames = o.optJSONArray("session_cookie_names").strings(),
            cloudflareCookieNames = o.optJSONArray("cloudflare_cookie_names").strings(),
            apiKeyConsoleUrl = o.optStringOrNull("api_key_console_url"),
        )

        fun parseAll(root: JSONObject): Map<String, AuthEndpoints> {
            val provs = root.optJSONObject("providers") ?: return emptyMap()
            return provs.keys().asSequence().associateWith { fromJson(it, provs.getJSONObject(it)) }
        }
    }
}

/** Result of one auth layer attempt. */
sealed class AuthResult {
    data class Success(val cred: ProviderCred, val layer: Int) : AuthResult()
    /** Waiting for the user (Custom Tab / WebView / key entry). */
    data class NeedsUser(val layer: Int, val message: String) : AuthResult()
    data class Failed(val layer: Int, val reason: String) : AuthResult()
}

/** Mirrors GET /health from the daemon. */
data class HealthReport(
    val reachable: Boolean,
    val status: String = "down",
    val flags: Map<String, Boolean> = emptyMap(),
    val aiProviders: List<String> = emptyList(),
    val authRequired: Boolean = false,
    val authOk: Boolean = true,
    val error: String? = null,
    /** provider -> ok | cooldown | needs_refresh | no_credentials (from the engine's failover state). */
    val aiStatus: Map<String, String> = emptyMap(),
    val claudeBridgeUp: Boolean = false,
) {
    val allFlagsOk: Boolean get() = flags.isNotEmpty() && flags.values.all { it }

    companion object {
        fun fromJson(o: JSONObject): HealthReport {
            val f = mutableMapOf<String, Boolean>()
            o.optJSONObject("flags")?.let { j -> j.keys().forEach { f[it] = j.optBoolean(it) } }
            val ai = o.optJSONArray("ai_providers")?.let { a -> (0 until a.length()).map { a.getString(it) } } ?: emptyList()
            val auth = o.optJSONObject("auth")
            val st = mutableMapOf<String, String>()
            o.optJSONObject("ai_status")?.let { j -> j.keys().forEach { k -> st[k] = j.optJSONObject(k)?.optString("state") ?: "" } }
            return HealthReport(true, o.optString("status", "ok"), f, ai,
                auth?.optBoolean("required") ?: false, auth?.optBoolean("ok", true) ?: true,
                null, st, o.optBoolean("claude_bridge", false))
        }
    }
}

data class GitHubStatus(val ok: Boolean, val login: String? = null, val canPush: Boolean = false, val message: String = "")

data class QueueItem(val packageId: String, val title: String, val status: String)
