package com.near.stickmandirector.bridge

import android.webkit.JavascriptInterface
import android.webkit.WebView
import com.near.stickmandirector.auth.Bg
import org.json.JSONObject
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

/**
 * JavaScript run INSIDE a WebView that is on https://claude.ai (real Chromium TLS + live cookie jar, so Cloudflare sees
 * normal browser traffic). Scripts report back through window.StickmanBridge.done(tag, json).
 * UNOFFICIAL private endpoints: they can change without notice.
 */
object ClaudeWebJs {
    /** GET /api/organizations. Success also makes Cloudflare issue cf_clearance if it wants one. */
    fun listOrgs(tag: String): String = """
(async function () {
  try {
    const r = await fetch('/api/organizations', {credentials: 'include',
      headers: {'anthropic-client-platform': 'web_claude_ai', 'Accept': 'application/json'}});
    const t = await r.text();
    StickmanBridge.done('$tag', JSON.stringify({status: r.status, body: t.slice(0, 20000)}));
  } catch (e) { StickmanBridge.done('$tag', JSON.stringify({status: 0, error: String(e)})); }
})();
"""

    /** Full flow: (org) -> create conversation -> stream completion -> delete conversation. */
    fun complete(tag: String, prompt: String, orgId: String?): String = """
(async function () {
  const H = {'anthropic-client-platform': 'web_claude_ai', 'Content-Type': 'application/json', 'Accept': 'application/json'};
  const PROMPT = ${JSONObject.quote(prompt)};
  function fin(o) { StickmanBridge.done('$tag', JSON.stringify(o)); }
  try {
    let org = ${JSONObject.quote(orgId ?: "")};
    if (!org) {
      const r0 = await fetch('/api/organizations', {credentials: 'include', headers: H});
      if (!r0.ok) { fin({status: r0.status, error: (await r0.text()).slice(0, 200), retry_after: r0.headers.get('retry-after')}); return; }
      const os = await r0.json();
      const chat = os.filter(function (o) { return (o.capabilities || []).indexOf('chat') >= 0; });
      org = ((chat[0] || os[0]) || {}).uuid;
      if (!org) { fin({status: 403, error: 'no organization on this account'}); return; }
    }
    const conv = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
      : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); });
    const base = '/api/organizations/' + org + '/chat_conversations';
    const r1 = await fetch(base, {method: 'POST', credentials: 'include', headers: H, body: JSON.stringify({uuid: conv, name: ''})});
    if (!r1.ok) { fin({status: r1.status, error: (await r1.text()).slice(0, 200), retry_after: r1.headers.get('retry-after')}); return; }
    let text = '', status = 200, err = '', retry = '';
    try {
      const r2 = await fetch(base + '/' + conv + '/completion', {method: 'POST', credentials: 'include',
        headers: Object.assign({}, H, {'Accept': 'text/event-stream'}),
        body: JSON.stringify({prompt: PROMPT, timezone: (Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'), attachments: [], files: []})});
      status = r2.status;
      if (!r2.ok) { err = (await r2.text()).slice(0, 200); retry = r2.headers.get('retry-after') || ''; }
      else {
        const rd = r2.body.getReader(), dec = new TextDecoder(); let buf = '';
        for (;;) {
          const chunk = await rd.read(); if (chunk.done) break;
          buf += dec.decode(chunk.value, {stream: true});
          let i;
          while ((i = buf.indexOf('\n')) >= 0) {
            const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
            if (line.indexOf('data:') !== 0) continue;
            const b = line.slice(5).trim(); if (!b || b === '[DONE]') continue;
            let o; try { o = JSON.parse(b); } catch (e) { continue; }
            if (o.type === 'error' || (o.error && typeof o.error === 'object')) { err = (o.error && o.error.message) || 'error'; status = 500; }
            else if (typeof o.completion === 'string') text += o.completion;
            else if (o.type === 'content_block_delta' && o.delta && typeof o.delta.text === 'string') text += o.delta.text;
          }
        }
      }
    } finally { try { await fetch(base + '/' + conv, {method: 'DELETE', credentials: 'include', headers: H}); } catch (e) {} }
    fin({status: status, text: text, error: err, retry_after: retry, org: org});
  } catch (e) { fin({status: 0, error: String(e)}); }
})();
"""
}

/** Runs ClaudeWebJs scripts in a WebView and delivers the JSON result on the main thread. Call [run] on the main thread. */
class WebRunner(private val web: WebView) {
    private val pending = ConcurrentHashMap<String, (JSONObject) -> Unit>()
    private val counter = AtomicInteger()

    private inner class Js {
        @JavascriptInterface
        fun done(tag: String, json: String) {
            val cb = pending.remove(tag) ?: return
            val obj = runCatching { JSONObject(json) }.getOrElse { JSONObject().put("status", 0).put("error", "bad result") }
            Bg.ui { cb(obj) }
        }
    }

    init { web.addJavascriptInterface(Js(), "StickmanBridge") }

    fun run(script: (String) -> String, timeoutMs: Long, cb: (JSONObject) -> Unit) {
        val tag = "t" + counter.incrementAndGet()
        pending[tag] = cb
        web.evaluateJavascript(script(tag), null)
        Bg.uiDelayed(timeoutMs) { pending.remove(tag)?.invoke(JSONObject().put("status", 0).put("error", "timeout")) }
    }
}
