package com.akaitigo.posvoice.auth

import io.quarkus.security.identity.AuthenticationRequestContext
import io.quarkus.security.identity.IdentityProvider
import io.quarkus.security.identity.SecurityIdentity
import io.quarkus.security.runtime.QuarkusSecurityIdentity
import io.smallrye.mutiny.Uni
import jakarta.enterprise.context.ApplicationScoped
import org.eclipse.microprofile.config.inject.ConfigProperty
import java.util.Optional

/**
 * APIキーを検証する IdentityProvider.
 *
 * 環境変数 `POS_VOICE_API_KEY` に設定されたキーと照合する。
 * キーが設定されていない場合、全リクエストを拒否する（安全側に倒す）。
 */
@ApplicationScoped
class ApiKeyIdentityProvider(
    @param:ConfigProperty(name = "pos-voice.api-key")
    private val configuredApiKey: Optional<String>,
) : IdentityProvider<ApiKeyAuthenticationRequest> {

    override fun getRequestType(): Class<ApiKeyAuthenticationRequest> {
        return ApiKeyAuthenticationRequest::class.java
    }

    override fun authenticate(
        request: ApiKeyAuthenticationRequest,
        context: AuthenticationRequestContext,
    ): Uni<SecurityIdentity> {
        return context.runBlocking {
            val expectedKey = configuredApiKey.orElse(null)
                ?: throw io.quarkus.security.AuthenticationFailedException(
                    "API key is not configured on the server",
                )

            if (!constantTimeEquals(request.apiKey, expectedKey)) {
                throw io.quarkus.security.AuthenticationFailedException("Invalid API key")
            }

            QuarkusSecurityIdentity.builder()
                .setPrincipal { "api-client" }
                .addRole("query-user")
                .build()
        }
    }

    /**
     * タイミング攻撃を防ぐための定数時間比較.
     */
    private fun constantTimeEquals(a: String, b: String): Boolean {
        val aBytes = a.toByteArray(Charsets.UTF_8)
        val bBytes = b.toByteArray(Charsets.UTF_8)
        return java.security.MessageDigest.isEqual(aBytes, bBytes)
    }
}
