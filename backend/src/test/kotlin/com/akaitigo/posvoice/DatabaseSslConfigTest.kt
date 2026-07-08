package com.akaitigo.posvoice

import io.quarkus.test.junit.QuarkusTest
import org.eclipse.microprofile.config.ConfigProvider
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

/**
 * DB の TLS 設定（Issue #31）の回帰テスト.
 *
 * `pos-voice.database.ssl-mode` が既定で `require` に解決されることを検証する。
 * 実際の `sslmode` JDBC プロパティは `%prod`/`%dev` プロファイルにのみ付与され、
 * H2 を使う test プロファイルには渡らない。
 */
@QuarkusTest
class DatabaseSslConfigTest {

    @Test
    fun `db ssl mode defaults to require`() {
        val sslMode = ConfigProvider.getConfig()
            .getValue("pos-voice.database.ssl-mode", String::class.java)
        assertEquals("require", sslMode)
    }
}
