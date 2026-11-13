package com.near.stickmandirector.bridge

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Typed-ish JSON wrapper over the daemon endpoints. Blocking; call off the main thread. Errors surface as exceptions. */
class DaemonApi(ctx: Context) {
    val client = TermuxClient(ctx)

    private fun arr(s: String) = JSONArray(s)
    private fun <T> JSONArray.map(f: (JSONObject) -> T): List<T> = (0 until length()).map { f(getJSONObject(it)) }

    fun queue(): List<JSONObject> = arr(client.get("/queue")).map { it }
    fun pkg(id: String): JSONObject = JSONObject(client.get("/queue/$id"))
    /** Validates + re-audits on the engine; returns {status, quality_audit, warnings}. Throws with the engine's message on 422. */
    fun savePkg(id: String, pkg: JSONObject): JSONObject = JSONObject(client.put("/queue/$id", pkg))

    fun startAuto(niche: String, queries: List<String>, channels: List<String>, minMultiplier: Double, offline: Boolean): String =
        JSONObject(client.post("/pipeline/auto", JSONObject()
            .put("niche", niche).put("queries", JSONArray(queries)).put("channels", JSONArray(channels))
            .put("min_multiplier", minMultiplier).put("offline", offline))).getString("job_id")

    fun job(id: String): JSONObject = JSONObject(client.get("/jobs/$id"))
    fun jobs(): List<JSONObject> = arr(client.get("/jobs")).map { it }
    fun renderDraft(id: String, keyframes: Boolean = false): String =
        JSONObject(client.post("/render/draft", JSONObject().put("package_id", id).put("mode", if (keyframes) "keyframes" else "draft")))
            .getString("job_id")

    fun library(): List<JSONObject> = JSONObject(client.get("/library")).getJSONArray("assets").map { it }
    fun forge(category: String, id: String, brief: String): String =
        JSONObject(client.post("/forge", JSONObject().put("category", category).put("id", id).put("brief", brief)))
            .getString("job_id")
    fun rebuildThumbs(): String = JSONObject(client.post("/forge/rebuild-thumbs")).getString("job_id")
    /** Installs the bundled 1,500-asset starter pack into the active library and renders its previews (long job). */
    fun installPack(): String =
        JSONObject(client.post("/library/install-pack", JSONObject().put("previews", true))).getString("job_id")
    fun curate(): JSONObject = JSONObject(client.post("/curate", JSONObject().put("use_ai", false)))

    // ---- review of forged assets
    fun reviewList(): List<JSONObject> = JSONObject(client.get("/library/review")).getJSONArray("pending").map { it }
    fun reviewPlan(ids: List<String>, repoIndex: JSONObject): JSONObject =
        JSONObject(client.post("/library/review/plan", JSONObject().put("ids", JSONArray(ids)).put("repo_index", repoIndex)))
    fun reviewApproved(ids: List<String>) { client.post("/library/review/approved", JSONObject().put("ids", JSONArray(ids))) }
    fun reviewReject(ids: List<String>): JSONObject =
        JSONObject(client.post("/library/review/reject", JSONObject().put("ids", JSONArray(ids))))
}
