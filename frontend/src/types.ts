/** 商品マッチング結果 */
export interface ProductMatch {
	readonly productId: string;
	readonly productName: string;
	readonly score: number;
	readonly quantity: number;
}

/** 認識結果 */
export interface RecognitionResult {
	readonly transcript: string;
	readonly confidence: number;
	readonly isFinal: boolean;
	readonly matches: readonly ProductMatch[];
}

/** 音声認識の状態 */
export type VoiceState = "idle" | "listening" | "processing" | "error";

/** 表記ゆれ辞書登録リクエスト */
export interface AliasRegistration {
	readonly spokenForm: string;
	readonly productId: string;
	readonly productName: string;
}

/** 表記ゆれ辞書登録レスポンス */
export interface AliasRegistrationResponse {
	readonly success: boolean;
	readonly message: string;
}

/** 商品検索結果 */
export interface ProductSearchResult {
	readonly productId: string;
	readonly productName: string;
	readonly janCode: string;
	readonly price: number;
}

/** パース用の型定義 */
export interface RawRecognitionData {
	transcript?: unknown;
	confidence?: unknown;
	isFinal?: unknown;
	matches?: unknown;
}

/** パース用のマッチデータ */
export interface RawProductMatchData {
	productId?: unknown;
	productName?: unknown;
	score?: unknown;
	quantity?: unknown;
}

/** 商品検索APIレスポンス */
export interface RawProductSearchData {
	productId?: unknown;
	productName?: unknown;
	janCode?: unknown;
	price?: unknown;
}
