"""PostgreSQL 商品マスタ・表記ゆれ辞書リポジトリ."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    import psycopg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Product:
    """商品マスタエンティティ."""

    id: str
    name: str
    barcode: str
    price: int


@dataclass(frozen=True)
class Alias:
    """表記ゆれ辞書エンティティ."""

    alias: str
    product_name: str
    created_at: datetime


class ProductRepository:
    """PostgreSQL を使った商品マスタ・表記ゆれ辞書の永続化.

    psycopg (v3) を使用してデータベースアクセスを行う。
    テーブル定義は Flyway マイグレーションで管理する。
    """

    def __init__(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """初期化.

        Args:
            conn: psycopg のデータベースコネクション
        """
        self._conn = conn

    def find_all_products(self) -> list[Product]:
        """全商品を取得する.

        Returns:
            商品のリスト
        """
        with self._conn.cursor() as cur:
            cur.execute("SELECT id, name, barcode, price FROM products ORDER BY name")
            return [
                Product(id=str(row[0]), name=str(row[1]), barcode=str(row[2]), price=int(row[3]))  # type: ignore[arg-type]
                for row in cur.fetchall()
            ]

    def find_product_by_name(self, name: str) -> Product | None:
        """商品名で商品を検索する.

        Args:
            name: 商品名

        Returns:
            商品。見つからない場合は None。
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, barcode, price FROM products WHERE name = %s",
                (name,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return Product(id=str(row[0]), name=str(row[1]), barcode=str(row[2]), price=int(row[3]))  # type: ignore[arg-type]

    def find_all_aliases(self) -> list[Alias]:
        """全表記ゆれエントリを取得する.

        Returns:
            表記ゆれエントリのリスト
        """
        with self._conn.cursor() as cur:
            cur.execute("SELECT alias, product_name, created_at FROM aliases ORDER BY alias")
            return [
                Alias(alias=str(row[0]), product_name=str(row[1]), created_at=row[2])  # type: ignore[arg-type]
                for row in cur.fetchall()
            ]

    def save_alias(self, alias: str, product_name: str) -> None:
        """表記ゆれエントリを保存する（UPSERT）.

        同じ alias が既に存在する場合は product_name を更新する。

        Args:
            alias: エイリアス（表記ゆれ）
            product_name: 正式な商品名
        """
        now = datetime.now(tz=UTC)
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO aliases (alias, product_name, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (alias) DO UPDATE SET product_name = EXCLUDED.product_name,
                                                  created_at = EXCLUDED.created_at
                """,
                (alias, product_name, now),
            )
        self._conn.commit()
        logger.info("Saved alias: '%s' -> '%s'", alias, product_name)

    def save_aliases_batch(self, aliases: Sequence[tuple[str, str]]) -> int:
        """表記ゆれエントリを一括保存する.

        Args:
            aliases: (alias, product_name) のタプルのシーケンス

        Returns:
            保存されたエントリ数
        """
        now = datetime.now(tz=UTC)
        with self._conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO aliases (alias, product_name, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (alias) DO UPDATE SET product_name = EXCLUDED.product_name,
                                                  created_at = EXCLUDED.created_at
                """,
                [(alias, product_name, now) for alias, product_name in aliases],
            )
        self._conn.commit()
        logger.info("Saved %d aliases in batch", len(aliases))
        return len(aliases)

    def delete_alias(self, alias: str) -> bool:
        """表記ゆれエントリを削除する.

        Args:
            alias: 削除するエイリアス

        Returns:
            削除された場合 True
        """
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM aliases WHERE alias = %s", (alias,))
            deleted = cur.rowcount > 0
        self._conn.commit()
        if deleted:
            logger.info("Deleted alias: '%s'", alias)
        return deleted

    def export_aliases_json(self) -> str:
        """全表記ゆれ辞書をJSON文字列としてエクスポートする.

        Returns:
            JSON文字列
        """
        aliases = self.find_all_aliases()
        entries = [
            {
                "alias": a.alias,
                "product_name": a.product_name,
            }
            for a in aliases
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
        aliases = [(entry["alias"], entry["product_name"]) for entry in entries]
        return self.save_aliases_batch(aliases)
