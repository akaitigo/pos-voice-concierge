package com.akaitigo.posvoice.voice

import com.akaitigo.posvoice.grpc.AudioChunk
import com.akaitigo.posvoice.grpc.MutinyVoiceServiceGrpc
import com.akaitigo.posvoice.grpc.RecognitionResult
import io.quarkus.grpc.GrpcClient
import io.smallrye.mutiny.Multi
import jakarta.enterprise.context.ApplicationScoped
import java.util.logging.Logger

/**
 * voice-engine gRPC クライアント.
 *
 * Backend から voice-engine への音声ストリーム転送を担当する。
 */
@ApplicationScoped
class VoiceEngineClient {

    @GrpcClient("voice-engine")
    lateinit var voiceService: MutinyVoiceServiceGrpc.MutinyVoiceServiceStub

    /**
     * 音声チャンクのストリームを voice-engine に転送し、認識結果のストリームを返す.
     *
     * @param audioChunks 音声チャンクの Multi ストリーム
     * @return 認識結果の Multi ストリーム
     */
    fun streamRecognize(audioChunks: Multi<AudioChunk>): Multi<RecognitionResult> {
        return voiceService.streamRecognize(audioChunks)
            .onFailure().invoke { e ->
                logger.warning("gRPC ストリーミング認識エラー: ${e.message}")
            }
    }

    /**
     * バイト配列から AudioChunk を生成する.
     *
     * @param data 音声データのバイト配列
     * @param format 音声フォーマット (webm, opus, wav)
     * @param sampleRate サンプルレート
     * @return AudioChunk プロトコルバッファメッセージ
     */
    fun createAudioChunk(
        data: ByteArray,
        format: String = "webm",
        sampleRate: Int = 16000,
    ): AudioChunk {
        return AudioChunk.newBuilder()
            .setData(com.google.protobuf.ByteString.copyFrom(data))
            .setFormat(format)
            .setSampleRate(sampleRate)
            .build()
    }

    companion object {
        private val logger: Logger = Logger.getLogger(VoiceEngineClient::class.java.name)
    }
}
