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
        private const val ACCESS_TOKEN_PARAM = "access_token"
        private const val WS_PATH_PREFIX = "/ws/"

        /**
         * リクエストからAPIキーを解決する.
         *
         * 優先順位:
         * 1. 全パス共通で `Authorization: Bearer <key>` ヘッダー。
         * 2. WebSocket パス（/ws/ 配下）に限り `access_token` クエリパラメータ。
         *    ブラウザの WebSocket ハンドシェイクは任意ヘッダーを設定できないため、
         *    クエリパラメータをフォールバックとして許可する（設計判断は ADR-0003 参照）。
         *
         * @param authHeader Authorization ヘッダーの値
         * @param path リクエストパス
         * @param accessToken access_token クエリパラメータの値
         * @return 解決したAPIキー。存在しない場合は null。
         */
        fun resolveApiKey(authHeader: String?, path: String?, accessToken: String?): String? {
            val fromHeader = authHeader
                ?.takeIf { it.startsWith(BEARER_PREFIX) }
                ?.substring(BEARER_PREFIX.length)
                ?.trim()
                ?.ifEmpty { null }
            val isWsPath = path != null && path.startsWith(WS_PATH_PREFIX)
            val fromQuery = if (isWsPath) {
                accessToken?.trim()?.ifEmpty { null }
            } else {
                null
            }
            return fromHeader ?: fromQuery
        }
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
        val authHeader: String? = context.request().getHeader(AUTHORIZATION_HEADER)
        val accessToken: String? = context.request().getParam(ACCESS_TOKEN_PARAM)
        return resolveApiKey(authHeader, context.normalizedPath(), accessToken)
    }

    override fun getCredentialTypes(): Set<Class<out AuthenticationRequest>> {
        return Collections.singleton(ApiKeyAuthenticationRequest::class.java)
    }
}
