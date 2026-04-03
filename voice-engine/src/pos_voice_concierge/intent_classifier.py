"""インテント分類器.

ルールベース（キーワードマッチング）で発話テキストのインテントを分類する。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Intent(Enum):
    """発話インテントの種類."""

    SALES_INQUIRY = "sales_inquiry"
    INVENTORY_INQUIRY = "inventory_inquiry"
    PRODUCT_REGISTRATION = "product_registration"
    TOP_PRODUCTS = "top_products"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SlotValue:
    """スロット値."""

    name: str
    value: str


@dataclass(frozen=True)
class ClassificationResult:
    """インテント分類結果."""

    intent: Intent
    confidence: float
    slots: tuple[SlotValue, ...]
    original_text: str


# --- キーワードパターン定義 ---

# 売上照会パターン
_SALES_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"売上|売り上げ|うりあげ|ウリアゲ"),
    re.compile(r"売れた|売れ行き"),
    re.compile(r"いくら.*(売|稼)"),
    re.compile(r"(本日|今日|今月|今週|先月|先週|昨日|きのう|きょう).*売上"),
    re.compile(r"売上.*(本日|今日|今月|今週|先月|先週|昨日|きのう|きょう)"),
    re.compile(r"レジ.*合計"),
]

# 在庫照会パターン
_INVENTORY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"在庫|ざいこ|ザイコ"),
    re.compile(r"(ある|ない|残り|残って|残数|何個|いくつ|何本|何袋).*(ある|ない|残|在)"),
    re.compile(r"(在|残|ストック).*ある"),
    re.compile(r"あと.*(何|いくつ|どれ)"),
]

# 商品登録パターン
_REGISTRATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(登録|追加|入れ|いれ|カート|かーと).*(して|する|お願い|ください)"),
    re.compile(r"(を|、)\d*(つ|個|本|袋|箱|パック)$"),
    re.compile(r"^\d*(つ|個|本|袋|箱|パック)の"),
]

# トップ商品パターン
_TOP_PRODUCTS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(トップ|ランキング|一番|人気|よく売れ|ベスト|上位)"),
    re.compile(r"売上.*(トップ|ランキング|上位|ベスト)"),
    re.compile(r"(何|なに|どれ).*一番.*売れ"),
    re.compile(r"売れ筋"),
]

# --- スロット抽出パターン ---

# 日付スロット
_DATE_SLOT_PATTERNS: dict[str, str] = {
    "today": r"今日|本日|きょう",
    "yesterday": r"昨日|きのう",
    "this_week": r"今週",
    "last_week": r"先週",
    "this_month": r"今月",
    "last_month": r"先月",
}

# 数量スロット（トップN）
_TOP_N_PATTERN = re.compile(r"(トップ|上位|ベスト)\s*(\d+)")
_TOP_N_KANJI_MAP: dict[str, int] = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}
_TOP_N_KANJI_PATTERN = re.compile(r"(トップ|上位|ベスト)\s*([一二三四五六七八九十]+)")

# 商品名抽出パターン
_PRODUCT_NAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(.+?)の(在庫|売上|売り上げ|残り|残数|ストック)"),
    re.compile(r"(在庫|売上|売り上げ).*[はが].*?(.+?)(は|が|って|$)"),
]

# 期間指定パターン
_DATE_RANGE_PATTERN = re.compile(r"(\d{1,2})月(\d{1,2})日?から(\d{1,2})月(\d{1,2})日?")
_SINGLE_DATE_PATTERN = re.compile(r"(\d{1,2})月(\d{1,2})日")


def classify(text: str) -> ClassificationResult:
    """発話テキストのインテントを分類する.

    ルールベースのキーワードマッチングで分類を行う。
    複数のインテントに該当する場合は、優先度が高いものを返す。

    優先度: トップ商品 > 売上照会 > 在庫照会 > 商品登録 > UNKNOWN

    Args:
        text: 発話テキスト

    Returns:
        分類結果
    """
    text = text.strip()
    if not text:
        return ClassificationResult(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            slots=(),
            original_text=text,
        )

    # スコア計算
    scores: dict[Intent, float] = {
        Intent.TOP_PRODUCTS: _calculate_score(text, _TOP_PRODUCTS_PATTERNS),
        Intent.SALES_INQUIRY: _calculate_score(text, _SALES_PATTERNS),
        Intent.INVENTORY_INQUIRY: _calculate_score(text, _INVENTORY_PATTERNS),
        Intent.PRODUCT_REGISTRATION: _calculate_score(text, _REGISTRATION_PATTERNS),
    }

    # トップ商品と売上の両方にヒットする場合、トップ商品を優先
    best_intent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent]

    if best_score == 0.0:
        return ClassificationResult(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            slots=(),
            original_text=text,
        )

    # スロット抽出
    slots = _extract_slots(text, best_intent)

    return ClassificationResult(
        intent=best_intent,
        confidence=min(best_score, 1.0),
        slots=tuple(slots),
        original_text=text,
    )


def _calculate_score(text: str, patterns: list[re.Pattern[str]]) -> float:
    """パターンマッチのスコアを計算する.

    Args:
        text: 入力テキスト
        patterns: 正規表現パターンのリスト

    Returns:
        マッチスコア (0.0 - 1.0)
    """
    match_count = sum(1 for p in patterns if p.search(text))
    if match_count == 0:
        return 0.0
    # 1パターンマッチで0.7、追加マッチで+0.1ずつ（最大1.0）
    return min(0.7 + (match_count - 1) * 0.1, 1.0)


def _extract_slots(text: str, intent: Intent) -> list[SlotValue]:
    """インテントに応じたスロットを抽出する.

    Args:
        text: 入力テキスト
        intent: 分類されたインテント

    Returns:
        抽出されたスロット値のリスト
    """
    slots: list[SlotValue] = []

    # 日付スロット（売上照会・トップ商品で使用）
    if intent in (Intent.SALES_INQUIRY, Intent.TOP_PRODUCTS):
        date_slot = _extract_date_slot(text)
        if date_slot is not None:
            slots.append(date_slot)

        # 期間指定
        range_slots = _extract_date_range(text)
        slots.extend(range_slots)

    # トップN
    if intent == Intent.TOP_PRODUCTS:
        n_slot = _extract_top_n(text)
        if n_slot is not None:
            slots.append(n_slot)

    # 商品名（在庫照会・売上照会で使用）
    if intent in (Intent.INVENTORY_INQUIRY, Intent.SALES_INQUIRY):
        product_slot = _extract_product_name(text)
        if product_slot is not None:
            slots.append(product_slot)

    return slots


def _extract_date_slot(text: str) -> SlotValue | None:
    """日付関連のスロットを抽出する.

    Args:
        text: 入力テキスト

    Returns:
        日付スロット。見つからない場合は None。
    """
    for slot_value, pattern_str in _DATE_SLOT_PATTERNS.items():
        if re.search(pattern_str, text):
            return SlotValue(name="date_range", value=slot_value)
    return None


def _extract_date_range(text: str) -> list[SlotValue]:
    """明示的な期間指定を抽出する.

    Args:
        text: 入力テキスト

    Returns:
        期間スロットのリスト
    """
    match = _DATE_RANGE_PATTERN.search(text)
    if match:
        return [
            SlotValue(name="start_date", value=f"{match.group(1)}/{match.group(2)}"),
            SlotValue(name="end_date", value=f"{match.group(3)}/{match.group(4)}"),
        ]
    return []


def _extract_top_n(text: str) -> SlotValue | None:
    """トップN の数値を抽出する.

    Args:
        text: 入力テキスト

    Returns:
        N のスロット値。見つからない場合はデフォルト 5。
    """
    match = _TOP_N_PATTERN.search(text)
    if match:
        return SlotValue(name="top_n", value=match.group(2))

    kanji_match = _TOP_N_KANJI_PATTERN.search(text)
    if kanji_match:
        kanji_str = kanji_match.group(2)
        n_value = _TOP_N_KANJI_MAP.get(kanji_str, 5)
        return SlotValue(name="top_n", value=str(n_value))

    # デフォルトは5
    return SlotValue(name="top_n", value="5")


def _extract_product_name(text: str) -> SlotValue | None:
    """商品名を抽出する.

    Args:
        text: 入力テキスト

    Returns:
        商品名スロット。見つからない場合は None。
    """
    for pattern in _PRODUCT_NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            product_name = match.group(1).strip()
            # 不要な助詞やキーワードを除去
            product_name = re.sub(r"^(の|は|が|って|を|で)\s*", "", product_name)
            product_name = re.sub(r"\s*(の|は|が|って|を|で)$", "", product_name)
            if product_name and len(product_name) >= 1:
                return SlotValue(name="product_name", value=product_name)
    return None
