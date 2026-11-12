package com.near.stickmandirector.auth

import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.near.stickmandirector.model.Defaults
import com.near.stickmandirector.model.ProviderCred
import org.json.JSONObject
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Everything secret lives here: EncryptedSharedPreferences (AES256-GCM, Keystore master key). */
class SecureStore private constructor(ctx: Context) {
    private val prefs: SharedPreferences = run {
        val mk = MasterKey.Builder(ctx.applicationContext).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
        EncryptedSharedPreferences.create(
            ctx.applicationContext, "stickman_secure", mk,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    fun getString(k: String): String? = prefs.getString(k, null)
    fun putString(k: String, v: String?) { prefs.edit().apply { if (v == null) remove(k) else putString(k, v) }.apply() }

    var githubPat: String?
        get() = getString("github_pat")
        set(v) = putString("github_pat", v?.trim()?.ifBlank { null })

    var githubRepo: String
        get() = getString("github_repo") ?: Defaults.DEFAULT_REPO
        set(v) = putString("github_repo", v.trim().ifBlank { null })

    /** Per-install token shared with the Termux daemon (X-Stickman-Token). Generated once. */
    val daemonToken: String
        get() = getString("daemon_token") ?: run {
            val b = ByteArray(24).also { SecureRandom().nextBytes(it) }
            val t = Base64.encodeToString(b, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP)
            putString("daemon_token", t); t
        }

    fun loadCred(name: String): ProviderCred? =
        getString("cred_$name")?.let { runCatching { ProviderCred.fromJson(JSONObject(it)) }.getOrNull() }

    fun saveCred(c: ProviderCred) = putString("cred_${c.name}", c.toJson().toString())
    fun clearCred(name: String) = putString("cred_$name", null)

    fun allCreds(): List<ProviderCred> = Defaults.PROVIDERS.map { loadCred(it) ?: ProviderCred(it) }
    fun usableProviders(): List<String> = allCreds().filter { it.usable }.map { it.name }

    companion object {
        @Volatile private var inst: SecureStore? = null
        fun get(ctx: Context): SecureStore =
            inst ?: synchronized(this) { inst ?: SecureStore(ctx).also { inst = it } }
    }
}

/** Android-Keystore AES-GCM used for the `enc_v1:` values written into providers.json. */
object KeystoreCrypto {
    private const val ALIAS = "stickman_providers_v1"
    const val PREFIX = "enc_v1:"

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (ks.getKey(ALIAS, null) as? SecretKey)?.let { return it }
        val kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        kg.init(
            KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build(),
        )
        return kg.generateKey()
    }

    fun encrypt(plain: String): String {
        val c = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        val ct = c.doFinal(plain.toByteArray(Charsets.UTF_8))
        return PREFIX + Base64.encodeToString(c.iv + ct, Base64.NO_WRAP)
    }

    fun decrypt(enc: String): String? = runCatching {
        val raw = Base64.decode(enc.removePrefix(PREFIX), Base64.NO_WRAP)
        val c = Cipher.getInstance("AES/GCM/NoPadding")
            .apply { init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, raw.copyOfRange(0, 12))) }
        String(c.doFinal(raw, 12, raw.size - 12), Charsets.UTF_8)
    }.getOrNull()
}
