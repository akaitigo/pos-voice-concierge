"""商品名ファジーマッチングエンジン."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from rapidfuzz import fuzz, process, utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_MAX_SCORE: float = 100.0

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchResult:
    """マッチング結果."""

    product_name: str
    score: float
    product_id: str


@dataclass(frozen=True)
class AliasEntry:
    """表記ゆれ辞書エントリ."""

    alias: str
    product_name: str


class FuzzyMatcher:
    """商品名のファジーマッチングを行うエンジン.

    表記ゆれ辞書を使用して、音声認識結果から最も近い商品を検索する。
    rapidfuzz の WRatio スコアラーで日本語文字列に対して安定したマッチングを提供する。
    """

    def __init__(self, threshold: float = 80.0) -> None:
        """初期化.

        Args:
            threshold: マッチングの閾値（0-100）。これ以上のスコアの候補のみ返す。

        Raises:
            ValueError: 閾値が 0-100 の範囲外の場合。
        """
        if not 0.0 <= threshold <= _MAX_SCORE:
            msg = f"threshold must be between 0 and 100, got {threshold}"
            raise ValueError(msg)
        self._threshold = threshold
        self._products: dict[str, str] = {}
        self._aliases: dict[str, str] = {}

    @property
    def threshold(self) -> float:
        """現在のマッチング閾値を返す."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """マッチング閾値を設定する.

        Args:
            value: 新しい閾値（0-100）。

        Raises:
            ValueError: 閾値が 0-100 の範囲外の場合。
        """
        if not 0.0 <= value <= _MAX_SCORE:
            msg = f"threshold must be between 0 and 100, got {value}"
            raise ValueError(msg)
        self._threshold = value

    @property
    def product_count(self) -> int:
        """登録されている商品数を返す."""
        return len(self._products)

    @property
    def alias_count(self) -> int:
        """登録されているエイリアス数を返す."""
        return len(self._aliases)

    def register_product(self, product_id: str, product_name: str) -> None:
        """商品を登録する.

        Args:
            product_id: 商品ID
            product_name: 商品名
        """
        self._products[product_name] = product_id

    def register_products(self, products: Sequence[tuple[str, str]]) -> None:
        """商品を一括登録する.

        Args:
            products: (product_id, product_name) のタプルのシーケンス
        """
        for product_id, product_name in products:
            self._products[product_name] = product_id

    def register_alias(self, alias: str, product_name: str) -> None:
        """表記ゆれ（エイリアス）を登録する.

        Args:
            alias: エイリアス（表記ゆれ）
            product_name: 正式な商品名
        """
        self._aliases[alias] = product_name

    def register_aliases(self, aliases: Sequence[tuple[str, str]]) -> None:
        """表記ゆれ（エイリアス）を一括登録する.

        Args:
            aliases: (alias, product_name) のタプルのシーケンス
        """
        for alias, product_name in aliases:
            self._aliases[alias] = product_name

    def learn_alias(self, recognized_text: str, correct_product_name: str) -> None:
        """手動修正から表記ゆれを学習する.

        ユーザーが音声認識結果を手動で修正した場合、その対応を辞書に登録する。
        既に正式名が一致する場合は登録しない。

        Args:
            recognized_text: 音声認識で得られたテキスト
            correct_product_name: ユーザーが修正した正しい商品名
        """
        if recognized_text == correct_product_name:
            return
        if correct_product_name not in self._products:
            logger.warning(
                "learn_alias: '%s' is not a registered product name",
                correct_product_name,
            )
            return
        self._aliases[recognized_text] = correct_product_name
        logger.info(
            "Learned alias: '%s' -> '%s'",
            recognized_text,
            correct_product_name,
        )

    def get_aliases_for_product(self, product_name: str) -> list[str]:
        """指定商品名に紐づく全エイリアスを返す.

        Args:
            product_name: 商品名

        Returns:
            エイリアスのリスト
        """
        return [alias for alias, name in self._aliases.items() if name == product_name]

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
            processor=utils.default_process,
            limit=limit,
            score_cutoff=self._threshold,
        )

        seen_ids: set[str] = set()
        match_results: list[MatchResult] = []
        for name, score, _ in results:
            canonical_name = self._aliases.get(name, name)
            product_id = self._products.get(canonical_name, "")
            if product_id and product_id not in seen_ids:
                seen_ids.add(product_id)
                match_results.append(
                    MatchResult(
                        product_name=canonical_name,
                        score=score,
                        product_id=product_id,
                    )
                )

        return match_results

    def export_aliases(self, file_path: Path) -> int:
        """表記ゆれ辞書をJSON形式でエクスポートする.

        Args:
            file_path: 出力先のファイルパス

        Returns:
            エクスポートされたエントリ数
        """
        entries = [
            asdict(AliasEntry(alias=alias, product_name=product_name))
            for alias, product_name in sorted(self._aliases.items())
        ]
        file_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Exported %d aliases to %s", len(entries), file_path)
        return len(entries)

    def import_aliases(self, file_path: Path) -> int:
        """JSON形式の表記ゆれ辞書をインポートする.

        Args:
            file_path: 入力元のファイルパス

        Returns:
            インポートされたエントリ数

        Raises:
            FileNotFoundError: ファイルが存在しない場合。
            json.JSONDecodeError: JSONのパースに失敗した場合。
            KeyError: 必須フィールドが欠けている場合。
        """
        content = file_path.read_text(encoding="utf-8")
        entries: list[dict[str, str]] = json.loads(content)
        count = 0
        for entry in entries:
            alias = entry["alias"]
            product_name = entry["product_name"]
            self._aliases[alias] = product_name
            count += 1
        logger.info("Imported %d aliases from %s", count, file_path)
        return count

    def export_aliases_json(self) -> str:
        """表記ゆれ辞書をJSON文字列としてエクスポートする.

        Returns:
            JSON文字列
        """
        entries = [
            asdict(AliasEntry(alias=alias, product_name=product_name))
            for alias, product_name in sorted(self._aliases.items())
        ]
        return json.dumps(entries, ensure_ascii=False, indent=2)

    def import_aliases_json(self, json_str: str) -> int:
        """JSON文字列から表記ゆれ辞書をインポートする.

        Args:
            json_str: JSON文字列

        Returns:
            インポートされたエントリ数

        Raises:
            json.JSONDecodeError: JSONのパースに失敗した場合。
            KeyError: 必須フィールドが欠けている場合。
        """
        entries: list[dict[str, str]] = json.loads(json_str)
        count = 0
        for entry in entries:
            self._aliases[entry["alias"]] = entry["product_name"]
            count += 1
        logger.info("Imported %d aliases from JSON string", count)
        return count

    def clear(self) -> None:
        """全ての商品とエイリアスをクリアする."""
        self._products.clear()
        self._aliases.clear()
