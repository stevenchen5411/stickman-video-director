package com.near.stickmandirector.bridge

import android.content.Context
import android.util.Base64
import com.near.stickmandirector.auth.SecureStore
import com.near.stickmandirector.model.GitHubStatus
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

data class ReleaseAssets(val tag: String, val videoUrl: String?, val coverUrl: String?, val htmlUrl: String?)

/**
 * GitHub REST client (PAT auth). Blocking: call off the main thread.
 * Used to push queue/<package_id>.json, trigger render-hd via repository_dispatch, and poll the release
 * `render-<package_id>` for <id>.mp4 and <id>_cover.jpg.
 */
class GitHubApiClient(ctx: Context) {
    private val store = SecureStore.get(ctx)
    private val http = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS).readTimeout(60, TimeUnit.SECONDS).build()
    private val jsonType = "application/json".toMediaType()
    private val repo get() = store.githubRepo

    private fun req(path: String, accept: String = "application/vnd.github+json"): Request.Builder =
        Request.Builder().url(if (path.startsWith("http")) path else "https://api.github.com$path")
            .header("Authorization", "Bearer ${store.githubPat.orEmpty()}")
            .header("Accept", accept).header("X-GitHub-Api-Version", "2022-11-28")

    fun hasToken(): Boolean = !store.githubPat.isNullOrBlank()

    /** Gate #3: token valid, repo reachable, push permission. */
    fun verify(): GitHubStatus {
        if (!hasToken()) return GitHubStatus(false, message = "No token saved")
        return try {
            val login = http.newCall(req("/user").build()).execute().use { r ->
                if (r.code == 401) return GitHubStatus(false, message = "Token rejected (401)")
                if (!r.isSuccessful) return GitHubStatus(false, message = "GitHub ${r.code}")
                JSONObject(r.body!!.string()).optString("login")
            }
            http.newCall(req("/repos/$repo").build()).execute().use { r ->
                when {
                    r.code == 404 -> GitHubStatus(false, login, message = "Repo $repo not found or token lacks access")
                    !r.isSuccessful -> GitHubStatus(false, login, message = "GitHub ${r.code}")
                    else -> {
                        val push = JSONObject(r.body!!.string()).optJSONObject("permissions")?.optBoolean("push") ?: false
                        if (push) GitHubStatus(true, login, true, "Connected as $login")
                        else GitHubStatus(false, login, false, "Token has read-only access to $repo")
                    }
                }
            }
        } catch (t: Throwable) { GitHubStatus(false, message = t.message ?: "network error") }
    }

    /** Create or update a file through the Contents API. Returns null on success or an error message. */
    fun putFile(path: String, content: ByteArray, message: String, branch: String = "main"): String? = try {
        val url = "/repos/$repo/contents/$path"
        val sha = http.newCall(req("$url?ref=$branch").build()).execute().use { r ->
            if (r.isSuccessful) JSONObject(r.body!!.string()).optString("sha").ifBlank { null } else null
        }
        val body = JSONObject().put("message", message).put("branch", branch)
            .put("content", Base64.encodeToString(content, Base64.NO_WRAP)).apply { sha?.let { put("sha", it) } }
        http.newCall(req(url).put(body.toString().toRequestBody(jsonType)).build()).execute().use { r ->
            if (r.isSuccessful) null else "GitHub ${r.code}: ${r.body?.string()?.take(160)}"
        }
    } catch (t: Throwable) { t.message ?: "network error" }

    fun pushQueueFile(packageId: String, file: File): String? =
        putFile("queue/$packageId.json", file.readBytes(), "queue: $packageId")

    /** repository_dispatch -> render-hd.yml. Returns null on success or an error message. */
    fun dispatchRender(packageId: String): String? = try {
        val payload = JSONObject().put("event_type", "render-hd")
            .put("client_payload", JSONObject().put("package_path", "queue/$packageId.json"))
        http.newCall(req("/repos/$repo/dispatches").post(payload.toString().toRequestBody(jsonType)).build())
            .execute().use { r -> if (r.code == 204) null else "GitHub ${r.code}: ${r.body?.string()?.take(160)}" }
    } catch (t: Throwable) { t.message ?: "network error" }

    /** Release `render-<id>` -> asset API URLs, or null while the render is still running. */
    fun pollRelease(packageId: String): ReleaseAssets? = try {
        http.newCall(req("/repos/$repo/releases/tags/render-$packageId").build()).execute().use { r ->
            if (!r.isSuccessful) null else {
                val j = JSONObject(r.body!!.string())
                val assets = j.optJSONArray("assets")
                var video: String? = null; var cover: String? = null
                if (assets != null) for (i in 0 until assets.length()) {
                    val a = assets.getJSONObject(i)
                    when (a.optString("name")) {
                        "$packageId.mp4" -> video = a.optString("url")
                        "${packageId}_cover.jpg" -> cover = a.optString("url")
                    }
                }
                if (video == null) null else ReleaseAssets("render-$packageId", video, cover, j.optString("html_url"))
            }
        }
    } catch (t: Throwable) { null }

    /** Download a release asset (API URL + octet-stream accept) to [dest]. Returns null on success or an error. */
    fun downloadAsset(apiUrl: String, dest: File): String? = try {
        dest.parentFile?.mkdirs()
        http.newCall(req(apiUrl, "application/octet-stream").build()).execute().use { r ->
            if (!r.isSuccessful) "GitHub ${r.code}" else {
                val tmp = File(dest.parentFile, dest.name + ".part")
                r.body!!.byteStream().use { i -> tmp.outputStream().use { o -> i.copyTo(o) } }
                if (!tmp.renameTo(dest)) { dest.writeBytes(tmp.readBytes()); tmp.delete() }
                null
            }
        }
    } catch (t: Throwable) { t.message ?: "network error" }

    /** Latest workflow-run conclusion for the render workflow, for the UI status line. */
    fun renderRunStatus(): String? = try {
        http.newCall(req("/repos/$repo/actions/workflows/render-hd.yml/runs?per_page=1").build()).execute().use { r ->
            if (!r.isSuccessful) null else JSONObject(r.body!!.string()).optJSONArray("workflow_runs")?.optJSONObject(0)
                ?.let { it.optString("status") + (it.optString("conclusion").takeIf { c -> c.isNotBlank() && c != "null" }?.let { c -> "/$c" } ?: "") }
        }
    } catch (t: Throwable) { null }
}
