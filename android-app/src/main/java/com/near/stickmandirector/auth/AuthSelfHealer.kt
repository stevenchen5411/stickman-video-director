package com.near.stickmandirector.auth

import android.app.Activity
import android.content.Context
import android.net.Uri
import android.util.Base64
import androidx.browser.customtabs.CustomTabsIntent
import com.near.stickmandirector.model.AuthEndpoints
import com.near.stickmandirector.model.AuthMode
import com.near.stickmandirector.model.AuthResult
import com.near.stickmandirector.model.ProviderCred
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.concurrent.TimeUnit

/**
 * Four-layer sign-in that repairs itself when a provider changes its flow:
 *   1. RFC 8414 (/.well-known/oauth-authorization-server) discovery  -> OAuth + PKCE in a Chrome Custom Tab
 *   2. GitHub-hosted .github/auth_endpoints.json (hot-patchable)     -> same OAuth path with patched URLs
 *   3. WebView cookie sniffer (session cookie + cf_clearance + UA)   -> see WebViewSnifferDialog
 *   4. Manual API key entry
 * OAuth (layers 1-2) needs a client_id. The shipped auth_endpoints.json has client_id=null, so until the
 * owner fills one in, those layers report "no client_id" and the chain falls through to layer 3 / 4.
 */
class AuthSelfHealer(private val ctx: Context) {
    private val store = SecureStore.get(ctx)
    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS).readTimeout(15, TimeUnit.SECONDS).build()

    // ------------------------------------------------------------------ endpoint resolution
    fun bundled(provider: String): AuthEndpoints? = runCatching {
        val txt = ctx.assets.open("auth_endpoints.json").bufferedReader().use { it.readText() }
        AuthEndpoints.parseAll(JSONObject(txt))[provider]
    }.getOrNull()

    /** Layer 1: RFC 8414 / OIDC discovery. Returns endpoints with discovered URLs overlaid, or null. */
    fun discover(base: AuthEndpoints): AuthEndpoints? {
        for (u in base.metadataUrls) {
            val body = get(u) ?: continue
            val j = runCatching { JSONObject(body) }.getOrNull() ?: continue
            val a = j.optString("authorization_endpoint").ifBlank { null }
            val t = j.optString("token_endpoint").ifBlank { null }
            if (a != null && t != null) return base.copy(authorizationEndpoint = a, tokenEndpoint = t)
        }
        return null
    }

    /** Layer 2: .github/auth_endpoints.json from the repo (private repo -> uses the stored PAT). */
    fun fromGitHub(provider: String): AuthEndpoints? {
        val pat = store.githubPat ?: return null
        val req = Request.Builder()
            .url("https://api.github.com/repos/${store.githubRepo}/contents/.github/auth_endpoints.json")
            .header("Authorization", "Bearer $pat")
            .header("Accept", "application/vnd.github.raw+json")
            .header("X-GitHub-Api-Version", "2022-11-28").build()
        return runCatching {
            http.newCall(req).execute().use { r ->
                if (!r.isSuccessful) null else AuthEndpoints.parseAll(JSONObject(r.body!!.string()))[provider]
            }
        }.getOrNull()
    }

    private fun get(url: String): String? = runCatching {
        http.newCall(Request.Builder().url(url).header("Accept", "application/json").build()).execute()
            .use { if (it.isSuccessful) it.body?.string() else null }
    }.getOrNull()

    // ------------------------------------------------------------------ start / redirect
    /**
     * Runs layers 1-2. On success launches a Custom Tab and reports NeedsUser(layer=1|2).
     * If OAuth is unavailable reports NeedsUser(layer=3) so the UI opens the WebView sniffer
     * (the UI can fall back to layer 4 / manual key itself).
     */
    fun start(provider: String, activity: Activity, cb: (AuthResult) -> Unit) {
        Bg.io {
            val base = bundled(provider)
            if (base == null) { Bg.ui { cb(AuthResult.Failed(0, "No endpoint spec for $provider")) }; return@io }
            var layer = 1
            var ep = discover(base)
            if (ep == null || ep.clientId == null) {
                val gh = fromGitHub(provider)
                if (gh != null && gh.authorizationEndpoint != null && gh.tokenEndpoint != null) { ep = gh; layer = 2 }
            }
            val ready = ep
            if (ready == null || ready.clientId == null || ready.authorizationEndpoint == null || ready.tokenEndpoint == null) {
                val why = if (ready != null && ready.clientId == null) "no OAuth client_id configured" else "OAuth discovery failed"
                Bg.ui { cb(AuthResult.NeedsUser(3, "$why; falling back to web sign-in")) }
                return@io
            }
            val verifier = randomUrlSafe(48)
            val state = randomUrlSafe(16)
            store.putString("pkce_$provider", JSONObject()
                .put("verifier", verifier).put("state", state)
                .put("token_endpoint", ready.tokenEndpoint).put("client_id", ready.clientId)
                .put("redirect_uri", ready.redirectUri).toString())
            val uri = Uri.parse(ready.authorizationEndpoint).buildUpon()
                .appendQueryParameter("response_type", "code")
                .appendQueryParameter("client_id", ready.clientId)
                .appendQueryParameter("redirect_uri", ready.redirectUri)
                .appendQueryParameter("scope", ready.scopes.joinToString(" "))
                .appendQueryParameter("state", state)
                .appendQueryParameter("code_challenge", challenge(verifier))
                .appendQueryParameter("code_challenge_method", "S256")
                .apply { if (provider == "gemini") { appendQueryParameter("access_type", "offline"); appendQueryParameter("prompt", "consent") } }
                .build()
            Bg.ui {
                try {
                    CustomTabsIntent.Builder().build().launchUrl(activity, uri)
                    cb(AuthResult.NeedsUser(layer, "Complete sign-in in the browser tab"))
                } catch (t: Throwable) { cb(AuthResult.NeedsUser(3, "No browser available: ${t.message}")) }
            }
        }
    }

    /** Called from MainActivity for com.near.stickmandirector://oauth/<provider>?code=...&state=... */
    fun handleRedirect(uri: Uri, cb: (AuthResult) -> Unit) {
        val provider = uri.pathSegments.lastOrNull() ?: return cb(AuthResult.Failed(1, "Bad redirect"))
        val err = uri.getQueryParameter("error")
        if (err != null) return cb(AuthResult.Failed(1, "Provider returned: $err"))
        val code = uri.getQueryParameter("code") ?: return cb(AuthResult.Failed(1, "No code in redirect"))
        val pk = store.getString("pkce_$provider")?.let { runCatching { JSONObject(it) }.getOrNull() }
            ?: return cb(AuthResult.Failed(1, "No pending sign-in for $provider"))
        if (pk.optString("state") != uri.getQueryParameter("state")) return cb(AuthResult.Failed(1, "State mismatch"))
        Bg.io {
            val form = FormBody.Builder()
                .add("grant_type", "authorization_code").add("code", code)
                .add("redirect_uri", pk.getString("redirect_uri")).add("client_id", pk.getString("client_id"))
                .add("code_verifier", pk.getString("verifier")).build()
            val res = tokenRequest(pk.getString("token_endpoint"), form, provider, store.loadCred(provider))
            store.putString("pkce_$provider", null)
            Bg.ui { cb(res) }
        }
    }

    /** Layer 4: manual API key. */
    fun saveApiKey(provider: String, key: String): AuthResult {
        val k = key.trim()
        if (k.length < 12) return AuthResult.Failed(4, "That does not look like an API key")
        val c = ProviderCred(provider, AuthMode.API_KEY, apiKey = k)
        store.saveCred(c)
        return AuthResult.Success(c, 4)
    }

    /** Layer 3 result from the WebView sniffer. */
    fun saveSession(provider: String, cookies: Map<String, String>, userAgent: String, orgId: String? = null): AuthResult {
        if (cookies.isEmpty()) return AuthResult.Failed(3, "No session cookies captured")
        val c = ProviderCred(provider, AuthMode.SESSION, cookies = cookies, userAgent = userAgent, orgId = orgId)
        store.saveCred(c)
        return AuthResult.Success(c, 3)
    }

    // ------------------------------------------------------------------ refresh (used by TokenRefreshWorker; blocking)
    fun refresh(provider: String): AuthResult {
        val cred = store.loadCred(provider) ?: return AuthResult.Failed(0, "not signed in")
        if (cred.mode != AuthMode.OAUTH || cred.refreshToken.isNullOrBlank()) return AuthResult.Failed(0, "nothing to refresh")
        val base = bundled(provider) ?: return AuthResult.Failed(0, "no endpoint spec")
        val ep = discover(base) ?: fromGitHub(provider) ?: base
        val token = ep.tokenEndpoint ?: return AuthResult.Failed(1, "no token endpoint")
        val form = FormBody.Builder().add("grant_type", "refresh_token").add("refresh_token", cred.refreshToken)
            .apply { ep.clientId?.let { add("client_id", it) } }.build()
        return tokenRequest(token, form, provider, cred)
    }

    private fun tokenRequest(url: String, form: FormBody, provider: String, prev: ProviderCred?): AuthResult = try {
        http.newCall(Request.Builder().url(url).post(form).header("Accept", "application/json").build()).execute().use { r ->
            val body = r.body?.string().orEmpty()
            if (!r.isSuccessful) AuthResult.Failed(1, "Token endpoint ${r.code}")
            else {
                val j = JSONObject(body)
                val at = j.optString("access_token").ifBlank { null }
                if (at == null) AuthResult.Failed(1, "No access_token in response")
                else {
                    val exp = j.optLong("expires_in", 0L)
                    val c = (prev ?: ProviderCred(provider)).copy(
                        mode = AuthMode.OAUTH, accessToken = at,
                        refreshToken = j.optString("refresh_token").ifBlank { prev?.refreshToken },
                        expiresAtMs = if (exp > 0) System.currentTimeMillis() + exp * 1000 else 0L,
                    )
                    store.saveCred(c); AuthResult.Success(c, 1)
                }
            }
        }
    } catch (t: Throwable) { AuthResult.Failed(1, t.message ?: "network error") }

    private fun randomUrlSafe(n: Int): String =
        Base64.encodeToString(ByteArray(n).also { SecureRandom().nextBytes(it) }, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP)

    private fun challenge(verifier: String): String =
        Base64.encodeToString(MessageDigest.getInstance("SHA-256").digest(verifier.toByteArray(Charsets.US_ASCII)),
            Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP)
}
