package com.akaitigo.posvoice.auth

import io.quarkus.security.identity.request.BaseAuthenticationRequest

/**
 * APIキー認証リクエスト.
 *
 * @property apiKey クライアントから送信されたAPIキー
 */
class ApiKeyAuthenticationRequest(
    val apiKey: String,
) : BaseAuthenticationRequest()
