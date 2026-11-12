package com.near.stickmandirector.bridge

import android.content.Context
import com.near.stickmandirector.auth.Bg
import com.near.stickmandirector.auth.SecureStore
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.ByteArrayOutputStream
import java.io.InputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * Loopback-only HTTP server (127.0.0.1:8766) that lets the Termux engine borrow the app's Chromium for claude.ai calls.
 *   GET  /ping            -> {"ok":true,"claude_session":bool}
 *   POST /claude/complete -> {"prompt": "...", "timeout_sec": 120}  =>  {status, text, error, retry_after, org}
 * Every request needs X-Stickman-Token (the same per-install token the daemon uses). One completion at a time.
 */
class LocalBridgeServer(private val ctx: Context, private val host: ClaudeWebHost) {
    private val store = SecureStore.get(ctx)
    private val lock = Any()
    @Volatile private var server: ServerSocket? = null

    companion object { const val PORT = 8766 }

    fun start() {
        if (server != null) return
        val ss = try { ServerSocket(PORT, 8, InetAddress.getByName("127.0.0.1")) } catch (t: Throwable) { return }
        server = ss
        Thread({
            while (!ss.isClosed) {
                val s = try { ss.accept() } catch (t: Throwable) { break }
                Thread({ handle(s) }, "bridge-conn").start()
            }
        }, "bridge-accept").start()
    }

    fun stop() { runCatching { server?.close() }; server = null }

    private fun handle(s: Socket) {
        s.use { sock ->
            sock.soTimeout = 15_000
            try {
                val inp = BufferedInputStream(sock.getInputStream())
                val reqLine = readLine(inp) ?: return
                val parts = reqLine.split(" ")
                if (parts.size < 2) return
                var len = 0; var token = ""
                while (true) {
                    val h = readLine(inp) ?: return
                    if (h.isEmpty()) break
                    val i = h.indexOf(':'); if (i < 0) continue
                    val k = h.substring(0, i).trim().lowercase(); val v = h.substring(i + 1).trim()
                    if (k == "content-length") len = v.toIntOrNull()?.coerceIn(0, 2_000_000) ?: 0
                    if (k == "x-stickman-token") token = v
                }
                if (!MessageDigest.isEqual(token.toByteArray(), store.daemonToken.toByteArray())) { reply(sock, 401, JSONObject().put("error", "bad token")); return }
                val body = if (len > 0) String(readN(inp, len), Charsets.UTF_8) else ""
                when {
                    parts[0] == "GET" && parts[1].startsWith("/ping") ->
                        reply(sock, 200, JSONObject().put("ok", true).put("claude_session", store.loadCred("claude")?.cookies?.isNotEmpty() == true))
                    parts[0] == "POST" && parts[1].startsWith("/claude/complete") -> reply(sock, 200, complete(JSONObject(body)))
                    else -> reply(sock, 404, JSONObject().put("error", "not found"))
                }
            } catch (t: Throwable) {
                runCatching { reply(sock, 500, JSONObject().put("status", 0).put("error", t.message ?: "bridge error")) }
            }
        }
    }

    private fun complete(req: JSONObject): JSONObject {
        val prompt = req.optString("prompt")
        if (prompt.isBlank()) return JSONObject().put("status", 0).put("error", "empty prompt")
        return synchronized(lock) { runCompletion(prompt, req) }
    }

    private fun runCompletion(prompt: String, req: JSONObject): JSONObject {
        val timeoutMs = (req.optInt("timeout_sec", 120).coerceIn(10, 300)) * 1000L
        val latch = CountDownLatch(1)
        var result: JSONObject = JSONObject().put("status", 0).put("error", "no result")
        val org = store.loadCred("claude")?.orgId
        Bg.ui { host.complete(prompt, org, timeoutMs) { r -> result = r; latch.countDown() } }
        if (!latch.await(timeoutMs + 15_000, TimeUnit.MILLISECONDS)) result = JSONObject().put("status", 0).put("error", "bridge timeout")
        return result
    }

    private fun reply(sock: Socket, code: Int, json: JSONObject) {
        val body = json.toString().toByteArray(Charsets.UTF_8)
        val head = "HTTP/1.1 $code ${if (code == 200) "OK" else "ERR"}\r\nContent-Type: application/json\r\nContent-Length: ${body.size}\r\nConnection: close\r\n\r\n"
        sock.getOutputStream().apply { write(head.toByteArray()); write(body); flush() }
    }

    private fun readLine(inp: InputStream): String? {
        val out = ByteArrayOutputStream()
        while (true) {
            val b = inp.read()
            if (b < 0) return if (out.size() == 0) null else out.toString("UTF-8")
            if (b == '\n'.code) return out.toString("UTF-8").trimEnd('\r')
            out.write(b)
            if (out.size() > 16_384) return null
        }
    }

    private fun readN(inp: InputStream, n: Int): ByteArray {
        val buf = ByteArray(n); var off = 0
        while (off < n) { val r = inp.read(buf, off, n - off); if (r < 0) break; off += r }
        return buf.copyOf(off)
    }
}
