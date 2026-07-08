package com.akaitigo.posvoice.auth

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

/**
 * [ApiKeyAuthMechanism.resolveApiKey] の単体テスト.
 *
 * ヘッダー優先・WebSocket パス限定の access_token フォールバックを検証する。
 */
class ApiKeyAuthMechanismTest {

    @Test
    fun `bearer header is extracted for any path`() {
        assertEquals("abc123", ApiKeyAuthMechanism.resolveApiKey("Bearer abc123", "/api/query/sales", null))
    }

    @Test
    fun `access_token query param is accepted on ws paths`() {
        assertEquals("wskey", ApiKeyAuthMechanism.resolveApiKey(null, "/ws/voice", "wskey"))
    }

    @Test
    fun `access_token query param is ignored on non-ws paths`() {
        assertNull(ApiKeyAuthMechanism.resolveApiKey(null, "/api/query/sales", "wskey"))
    }

    @Test
    fun `header takes precedence over query param on ws path`() {
        assertEquals("headerkey", ApiKeyAuthMechanism.resolveApiKey("Bearer headerkey", "/ws/voice", "querykey"))
    }

    @Test
    fun `blank bearer token resolves to null`() {
        assertNull(ApiKeyAuthMechanism.resolveApiKey("Bearer   ", "/ws/voice", null))
    }

    @Test
    fun `blank access_token resolves to null`() {
        assertNull(ApiKeyAuthMechanism.resolveApiKey(null, "/ws/voice", "   "))
    }

    @Test
    fun `no credentials resolves to null`() {
        assertNull(ApiKeyAuthMechanism.resolveApiKey(null, "/ws/voice", null))
    }
}
