"""商品名ファジーマッチングエンジン."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rapidfuzz import fuzz, process

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class MatchResult:
    """マッチング結果."""

    product_name: str
    score: float
    product_id: str


class FuzzyMatcher:
    """商品名のファジーマッチングを行うエンジン.

    表記ゆれ辞書を使用して、音声認識結果から最も近い商品を検索する。
    """

    def __init__(self, threshold: float = 80.0) -> None:
        """初期化.

        Args:
            threshold: マッチングの閾値（0-100）。これ以上のスコアの候補のみ返す。
        """
        self._threshold = threshold
        self._products: dict[str, str] = {}
        self._aliases: dict[str, str] = {}

    def register_product(self, product_id: str, product_name: str) -> None:
        """商品を登録する.

        Args:
            product_id: 商品ID
            product_name: 商品名
        """
        self._products[product_name] = product_id

    def register_alias(self, alias: str, product_name: str) -> None:
        """表記ゆれ（エイリアス）を登録する.

        Args:
            alias: エイリアス（表記ゆれ）
            product_name: 正式な商品名
        """
        self._aliases[alias] = product_name

    def match(self, query: str, limit: int = 3) -> Sequence[MatchResult]:
        """クエリに対してファジーマッチングを実行する.

        Args:
            query: 検索クエリ（音声認識結果）
            limit: 返す候補の最大数

        Returns:
            マッチング結果のリスト（スコア降順）
        """
        all_names = list(self._products.keys()) + list(self._aliases.keys())
        if not all_names:
            return []

        results = process.extract(
            query,
            all_names,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=self._threshold,
        )

        match_results: list[MatchResult] = []
        for name, score, _ in results:
            canonical_name = self._aliases.get(name, name)
            product_id = self._products.get(canonical_name, "")
            if product_id:
                match_results.append(
                    MatchResult(
                        product_name=canonical_name,
                        score=score,
                        product_id=product_id,
                    )
                )

        return match_results
