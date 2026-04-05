package com.akaitigo.posvoice.auth

import io.quarkus.security.identity.IdentityProviderManager
import io.quarkus.security.identity.SecurityIdentity
import io.quarkus.security.identity.request.AuthenticationRequest
import io.quarkus.vertx.http.runtime.security.ChallengeData
import io.quarkus.vertx.http.runtime.security.HttpAuthenticationMechanism
import io.smallrye.mutiny.Uni
import io.vertx.ext.web.RoutingContext
import jakarta.enterprise.context.ApplicationScoped
import java.util.Collections

/**
 * Bearer Token (API Key) 認証メカニズム.
 *
 * Authorization: Bearer <api-key> ヘッダーからAPIキーを抽出し、
 * [ApiKeyIdentityProvider] で検証する。
 */
@ApplicationScoped
class ApiKeyAuthMechanism : HttpAuthenticationMechanism {

    companion object {
        private const val BEARER_PREFIX = "Bearer "
        private const val AUTHORIZATION_HEADER = "Authorization"
        private const val UNAUTHORIZED_STATUS = 401
    }

    override fun authenticate(
        context: RoutingContext,
        identityProviderManager: IdentityProviderManager,
    ): Uni<SecurityIdentity> {
        val apiKey = extractApiKey(context)
            ?: return Uni.createFrom().nullItem()

        val request = ApiKeyAuthenticationRequest(apiKey)
        return identityProviderManager.authenticate(request)
    }

    override fun getChallenge(context: RoutingContext): Uni<ChallengeData> {
        return Uni.createFrom().item(
            ChallengeData(UNAUTHORIZED_STATUS, "WWW-Authenticate", "Bearer"),
        )
    }

    private fun extractApiKey(context: RoutingContext): String? {
        val authHeader = context.request().getHeader(AUTHORIZATION_HEADER)
        return authHeader
            ?.takeIf { it.startsWith(BEARER_PREFIX) }
            ?.substring(BEARER_PREFIX.length)
            ?.trim()
            ?.ifEmpty { null }
    }

    override fun getCredentialTypes(): Set<Class<out AuthenticationRequest>> {
        return Collections.singleton(ApiKeyAuthenticationRequest::class.java)
    }
}
