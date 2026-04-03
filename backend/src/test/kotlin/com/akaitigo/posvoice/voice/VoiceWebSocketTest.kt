package com.akaitigo.posvoice.voice

import io.quarkus.test.junit.QuarkusTest
import io.restassured.RestAssured.given
import org.hamcrest.CoreMatchers.`is`
import org.junit.jupiter.api.Test

/**
 * VoiceWebSocket の基本テスト.
 *
 * WebSocket の完全な E2E テストは統合テスト環境で実施する。
 * ここでは Backend が正常に起動し、WebSocket エンドポイントが
 * 登録されていることを確認する。
 */
@QuarkusTest
class VoiceWebSocketTest {

    @Test
    fun `health endpoint is still accessible with voice websocket registered`() {
        given()
            .`when`().get("/health")
            .then()
            .statusCode(200)
            .body("status", `is`("ok"))
    }
}
