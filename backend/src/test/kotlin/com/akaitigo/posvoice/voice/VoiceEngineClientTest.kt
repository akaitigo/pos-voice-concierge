package com.akaitigo.posvoice.voice

import com.akaitigo.posvoice.grpc.AudioChunk
import org.junit.jupiter.api.Assertions.assertArrayEquals
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

/**
 * VoiceEngineClient の単体テスト.
 *
 * gRPC 接続を必要としないユーティリティメソッドのテスト。
 */
class VoiceEngineClientTest {

    @Test
    fun `createAudioChunk builds correct protobuf message`() {
        val client = VoiceEngineClient()
        val testData = byteArrayOf(0x01, 0x02, 0x03, 0x04)

        val chunk: AudioChunk = client.createAudioChunk(
            data = testData,
            format = "webm",
            sampleRate = 16000,
        )

        assertArrayEquals(testData, chunk.data.toByteArray())
        assertEquals("webm", chunk.format)
        assertEquals(16000, chunk.sampleRate)
    }

    @Test
    fun `createAudioChunk uses default format and sample rate`() {
        val client = VoiceEngineClient()
        val testData = byteArrayOf(0x00)

        val chunk: AudioChunk = client.createAudioChunk(data = testData)

        assertEquals("webm", chunk.format)
        assertEquals(16000, chunk.sampleRate)
    }

    @Test
    fun `createAudioChunk handles empty data`() {
        val client = VoiceEngineClient()

        val chunk: AudioChunk = client.createAudioChunk(data = byteArrayOf())

        assertEquals(0, chunk.data.size())
        assertEquals("webm", chunk.format)
    }

    @Test
    fun `createAudioChunk with wav format`() {
        val client = VoiceEngineClient()
        val testData = byteArrayOf(0x52, 0x49, 0x46, 0x46)

        val chunk: AudioChunk = client.createAudioChunk(
            data = testData,
            format = "wav",
            sampleRate = 44100,
        )

        assertEquals("wav", chunk.format)
        assertEquals(44100, chunk.sampleRate)
    }
}
