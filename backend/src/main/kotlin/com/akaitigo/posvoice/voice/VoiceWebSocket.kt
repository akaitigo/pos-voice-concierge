package com.akaitigo.posvoice.voice

import com.akaitigo.posvoice.grpc.RecognitionResult
import io.smallrye.mutiny.Multi
import io.smallrye.mutiny.subscription.MultiEmitter
import jakarta.enterprise.context.ApplicationScoped
import jakarta.inject.Inject
import jakarta.websocket.OnClose
import jakarta.websocket.OnError
import jakarta.websocket.OnMessage
import jakarta.websocket.OnOpen
import jakarta.websocket.Session
import jakarta.websocket.server.ServerEndpoint
import java.nio.ByteBuffer
import java.util.concurrent.ConcurrentHashMap
import java.util.logging.Logger

/**
 * 音声入力 WebSocket エンドポイント.
 *
 * フロントエンドからの音声データ（バイナリ）を受信し、
 * voice-engine gRPC クライアント経由で認識結果を返す。
 * 音声データはメモリ上のストリーム処理のみで、ディスクには保存しない。
 */
@ServerEndpoint("/ws/voice")
@ApplicationScoped
class VoiceWebSocket {

    @Inject
    lateinit var voiceEngineClient: VoiceEngineClient

    private val sessions = ConcurrentHashMap<String, SessionContext>()

    @OnOpen
    fun onOpen(session: Session) {
        val context = SessionContext()
        sessions[session.id] = context

        val audioStream = Multi.createFrom().emitter<ByteArray> { emitter ->
            context.emitter = emitter
        }

        val audioChunks = audioStream.map { data ->
            voiceEngineClient.createAudioChunk(data)
        }

        voiceEngineClient.streamRecognize(audioChunks)
            .subscribe().with(
                { result -> sendResult(session, result) },
                { error ->
                    logger.warning("セッション ${session.id} のストリーミングエラー: ${error.message}")
                    closeSession(session)
                },
                { logger.info("セッション ${session.id} のストリーミング完了") },
            )

        logger.info("WebSocket セッション開始: ${session.id}")
    }

    @OnMessage
    fun onMessage(data: ByteBuffer, session: Session) {
        val context = sessions[session.id] ?: return
        val bytes = ByteArray(data.remaining())
        data.get(bytes)
        context.emitter?.emit(bytes)
    }

    @OnClose
    fun onClose(session: Session) {
        val context = sessions.remove(session.id) ?: return
        context.emitter?.complete()
        logger.info("WebSocket セッション終了: ${session.id}")
    }

    @OnError
    fun onError(session: Session, throwable: Throwable) {
        logger.warning("WebSocket エラー (${session.id}): ${throwable.message}")
        val context = sessions.remove(session.id)
        context?.emitter?.complete()
    }

    private fun sendResult(session: Session, result: RecognitionResult) {
        if (session.isOpen) {
            val json = buildResultJson(result)
            session.asyncRemote.sendText(json)
        }
    }

    private fun closeSession(session: Session) {
        val context = sessions.remove(session.id)
        context?.emitter?.complete()
        if (session.isOpen) {
            session.close()
        }
    }

    private fun buildResultJson(result: RecognitionResult): String {
        val matchesJson = result.matchesList.joinToString(",") { match ->
            """{"productId":"${escapeJson(match.productId)}",""" +
                """"productName":"${escapeJson(match.productName)}",""" +
                """"score":${match.score},""" +
                """"quantity":${match.quantity}}"""
        }
        return """{"transcript":"${escapeJson(result.transcript)}",""" +
            """"confidence":${result.confidence},""" +
            """"isFinal":${result.isFinal},""" +
            """"matches":[$matchesJson]}"""
    }

    private fun escapeJson(value: String): String {
        return value
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
    }

    private data class SessionContext(
        var emitter: MultiEmitter<in ByteArray>? = null,
    )

    companion object {
        private val logger: Logger = Logger.getLogger(VoiceWebSocket::class.java.name)
    }
}
