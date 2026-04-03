"""発話テキストから数量を抽出するパーサー."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedUtterance:
    """発話テキストのパース結果.

    Attributes:
        product_query: 商品名部分（数量表現を除いたテキスト）
        quantity: 抽出された数量（数量指定がない場合は 1）
        unit: 抽出された単位（数量指定がない場合は空文字列）
    """

    product_query: str
    quantity: int
    unit: str


# 数量パターン: 「3つ」「5個」「2本」「1袋」「3箱」「2パック」「500g」「1kg」「200ml」「1L」
_QUANTITY_PATTERN = re.compile(
    r"[をの\s]*(\d+)\s*(つ|個|本|袋|箱|パック|kg|g|ml|L)\s*$",
)

# 先頭数量パターン: 「3つのコーラ」
_LEADING_QUANTITY_PATTERN = re.compile(
    r"^(\d+)\s*(つ|個|本|袋|箱|パック|kg|g|ml|L)\s*[のを]?\s*",
)

# 漢数字 → アラビア数字のマッピング
_KANJI_DIGITS: dict[str, str] = {
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
    "十": "10",
}

# 漢数字パターン: 「三つ」「五個」
_KANJI_QUANTITY_PATTERN = re.compile(
    r"[をの\s]*([一二三四五六七八九十]+)\s*(つ|個|本|袋|箱|パック)\s*$",
)


def _convert_kanji_number(kanji: str) -> int:
    """漢数字をアラビア数字に変換する.

    「十」を含む場合の処理:
    - 「十」 → 10
    - 「二十」 → 20
    - 「十五」 → 15
    - 「二十三」 → 23

    Args:
        kanji: 漢数字文字列

    Returns:
        変換後の整数値
    """
    if "十" not in kanji:
        # 「十」を含まない場合は単純な1桁
        return int(_KANJI_DIGITS.get(kanji, "0"))

    parts = kanji.split("十")
    tens = int(_KANJI_DIGITS.get(parts[0], "1")) if parts[0] else 1
    ones = int(_KANJI_DIGITS.get(parts[1], "0")) if len(parts) > 1 and parts[1] else 0
    return tens * 10 + ones


def parse_utterance(text: str) -> ParsedUtterance:
    """発話テキストから商品名と数量を分離する.

    以下のパターンに対応:
    - 「コーラを3つ」→ product_query="コーラ", quantity=3, unit="つ"
    - 「ポテチ 5個」→ product_query="ポテチ", quantity=5, unit="個"
    - 「お茶2本」→ product_query="お茶", quantity=2, unit="本"
    - 「3つのコーラ」→ product_query="コーラ", quantity=3, unit="つ"
    - 「おにぎり三つ」→ product_query="おにぎり", quantity=3, unit="つ"
    - 「コーラ」→ product_query="コーラ", quantity=1, unit=""

    Args:
        text: 発話テキスト

    Returns:
        パース結果
    """
    text = text.strip()
    if not text:
        return ParsedUtterance(product_query="", quantity=1, unit="")

    # 末尾の数量パターンを検出（「コーラを3つ」「ポテチ 5個」）
    match = _QUANTITY_PATTERN.search(text)
    if match:
        quantity = int(match.group(1))
        unit = match.group(2)
        product_query = text[: match.start()].strip()
        return ParsedUtterance(product_query=product_query, quantity=quantity, unit=unit)

    # 漢数字の数量パターン（「おにぎり三つ」）
    kanji_match = _KANJI_QUANTITY_PATTERN.search(text)
    if kanji_match:
        quantity = _convert_kanji_number(kanji_match.group(1))
        unit = kanji_match.group(2)
        product_query = text[: kanji_match.start()].strip()
        return ParsedUtterance(product_query=product_query, quantity=quantity, unit=unit)

    # 先頭の数量パターンを検出（「3つのコーラ」）
    leading_match = _LEADING_QUANTITY_PATTERN.match(text)
    if leading_match:
        quantity = int(leading_match.group(1))
        unit = leading_match.group(2)
        product_query = text[leading_match.end() :].strip()
        if product_query:
            return ParsedUtterance(product_query=product_query, quantity=quantity, unit=unit)

    # 数量指定なし
    return ParsedUtterance(product_query=text, quantity=1, unit="")
