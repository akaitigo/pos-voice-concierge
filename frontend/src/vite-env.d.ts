/// <reference types="vite/client" />

interface ImportMetaEnv {
	/** WebSocket ハンドシェイク認証に使う API キー（ビルド時に注入） */
	readonly VITE_POS_VOICE_API_KEY?: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
