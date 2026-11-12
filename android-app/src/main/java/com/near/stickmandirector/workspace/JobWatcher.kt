package com.near.stickmandirector.workspace

import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.bridge.DaemonApi
import org.json.JSONObject

/** Polls GET /jobs/{id} every 1.5 s until done/failed. Callbacks run on the main thread. */
class JobWatcher(private val api: DaemonApi) {
    @Volatile private var cancelled = false
    fun cancel() { cancelled = true }

    fun watch(jobId: String, onUpdate: (JSONObject) -> Unit, onDone: (JSONObject) -> Unit, onError: (String) -> Unit) {
        Bg.io {
            var misses = 0
            while (!cancelled) {
                try {
                    val j = api.job(jobId)
                    misses = 0
                    val st = j.optString("status")
                    if (st == "done" || st == "failed") { Bg.ui { if (!cancelled) onDone(j) }; return@io }
                    Bg.ui { if (!cancelled) onUpdate(j) }
                } catch (t: Throwable) {
                    if (++misses >= 5) { Bg.ui { if (!cancelled) onError(t.message ?: "daemon unreachable") }; return@io }
                }
                Thread.sleep(1500)
            }
        }
    }

    companion object {
        fun lastLog(job: JSONObject, n: Int = 4): String {
            val log = job.optJSONArray("log") ?: return ""
            val from = (log.length() - n).coerceAtLeast(0)
            return (from until log.length()).joinToString("\n") { log.optString(it) }
        }
    }
}
