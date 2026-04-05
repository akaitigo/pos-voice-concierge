"""product_repository のテスト.

psycopg を使用した DB 連携テスト。
実際の PostgreSQL 接続が不要なよう、psycopg のモックを使用する。
"""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from pos_voice_concierge.product_repository import (
    Alias,
    InventoryResult,
    Product,
    ProductRepository,
    SalesResult,
    TopProductEntry,
)


def _make_mock_conn():
    """モックコネクションを作成する."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


class TestFindAllProducts:
    """全商品取得のテスト."""

    def test_returns_products(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchall.return_value = [
            ("P001", "コカ・コーラ 500ml", "4902102000001", 150),
            ("P002", "サントリー天然水 550ml", "4901777000001", 120),
        ]
        repo = ProductRepository(conn)
        products = repo.find_all_products()

        assert len(products) == 2
        assert products[0] == Product(id="P001", name="コカ・コーラ 500ml", barcode="4902102000001", price=150)

    def test_returns_empty_list(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchall.return_value = []
        repo = ProductRepository(conn)
        products = repo.find_all_products()
        assert products == []


class TestFindProductByName:
    """商品名検索のテスト."""

    def test_found(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = ("P001", "コカ・コーラ 500ml", "4902102000001", 150)
        repo = ProductRepository(conn)
        product = repo.find_product_by_name("コカ・コーラ 500ml")

        assert product is not None
        assert product.id == "P001"
        assert product.name == "コカ・コーラ 500ml"

    def test_not_found(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = None
        repo = ProductRepository(conn)
        product = repo.find_product_by_name("存在しない商品")
        assert product is None


class TestFindAllAliases:
    """全表記ゆれ取得のテスト."""

    def test_returns_aliases(self) -> None:
        conn, cursor = _make_mock_conn()
        now = datetime.now(tz=UTC)
        cursor.fetchall.return_value = [
            ("コーラ", "コカ・コーラ 500ml", now),
            ("天然水", "サントリー天然水 550ml", now),
        ]
        repo = ProductRepository(conn)
        aliases = repo.find_all_aliases()

        assert len(aliases) == 2
        assert aliases[0] == Alias(alias="コーラ", product_name="コカ・コーラ 500ml", created_at=now)


class TestSaveAlias:
    """表記ゆれ保存のテスト."""

    @patch("pos_voice_concierge.product_repository.datetime")
    def test_save_alias(self, mock_datetime) -> None:
        mock_now = datetime(2026, 4, 3, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        conn, cursor = _make_mock_conn()
        repo = ProductRepository(conn)
        repo.save_alias("コーラ", "コカ・コーラ 500ml")

        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()


class TestSaveAliasesBatch:
    """一括保存のテスト."""

    @patch("pos_voice_concierge.product_repository.datetime")
    def test_save_batch(self, mock_datetime) -> None:
        mock_now = datetime(2026, 4, 3, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        conn, cursor = _make_mock_conn()
        repo = ProductRepository(conn)
        count = repo.save_aliases_batch(
            [
                ("コーラ", "コカ・コーラ 500ml"),
                ("天然水", "サントリー天然水 550ml"),
            ]
        )

        assert count == 2
        cursor.executemany.assert_called_once()
        conn.commit.assert_called_once()


class TestDeleteAlias:
    """表記ゆれ削除のテスト."""

    def test_delete_existing(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.rowcount = 1
        repo = ProductRepository(conn)
        result = repo.delete_alias("コーラ")
        assert result is True

    def test_delete_nonexistent(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.rowcount = 0
        repo = ProductRepository(conn)
        result = repo.delete_alias("存在しない")
        assert result is False


class TestExportImportJson:
    """JSON エクスポート/インポートのテスト."""

    def test_export_json(self) -> None:
        conn, cursor = _make_mock_conn()
        now = datetime.now(tz=UTC)
        cursor.fetchall.return_value = [
            ("コーラ", "コカ・コーラ 500ml", now),
        ]
        repo = ProductRepository(conn)
        json_str = repo.export_aliases_json()
        data = json.loads(json_str)
        assert len(data) == 1
        assert data[0]["alias"] == "コーラ"
        assert data[0]["product_name"] == "コカ・コーラ 500ml"

    @patch("pos_voice_concierge.product_repository.datetime")
    def test_import_json(self, mock_datetime) -> None:
        mock_now = datetime(2026, 4, 3, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        conn, _cursor = _make_mock_conn()
        repo = ProductRepository(conn)
        json_str = json.dumps(
            [
                {"alias": "コーラ", "product_name": "コカ・コーラ 500ml"},
                {"alias": "天然水", "product_name": "サントリー天然水 550ml"},
            ]
        )
        count = repo.import_aliases_json(json_str)
        assert count == 2

    def test_import_invalid_json(self) -> None:
        conn, _ = _make_mock_conn()
        repo = ProductRepository(conn)
        with pytest.raises(json.JSONDecodeError):
            repo.import_aliases_json("invalid")

    def test_import_missing_key(self) -> None:
        conn, _ = _make_mock_conn()
        repo = ProductRepository(conn)
        json_str = json.dumps([{"alias": "test"}])
        with pytest.raises(KeyError):
            repo.import_aliases_json(json_str)


class TestTotalSalesBetween:
    """売上合計取得のテスト."""

    def test_returns_sales_result(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = (125000, 42)
        repo = ProductRepository(conn)
        from_dt = datetime(2026, 4, 5, 0, 0, 0, tzinfo=UTC)
        to_dt = datetime(2026, 4, 6, 0, 0, 0, tzinfo=UTC)
        result = repo.total_sales_between(from_dt, to_dt)

        assert result == SalesResult(total_amount=125000, item_count=42, period_label="")
        cursor.execute.assert_called_once()

    def test_returns_zero_when_no_data(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = (0, 0)
        repo = ProductRepository(conn)
        from_dt = datetime(2026, 4, 5, 0, 0, 0, tzinfo=UTC)
        to_dt = datetime(2026, 4, 6, 0, 0, 0, tzinfo=UTC)
        result = repo.total_sales_between(from_dt, to_dt)

        assert result.total_amount == 0
        assert result.item_count == 0

    def test_returns_zero_when_none_row(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = None
        repo = ProductRepository(conn)
        from_dt = datetime(2026, 4, 5, 0, 0, 0, tzinfo=UTC)
        to_dt = datetime(2026, 4, 6, 0, 0, 0, tzinfo=UTC)
        result = repo.total_sales_between(from_dt, to_dt)

        assert result.total_amount == 0
        assert result.item_count == 0


class TestProductSalesBetween:
    """商品別売上取得のテスト."""

    def test_returns_product_sales(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = (30000, 10)
        repo = ProductRepository(conn)
        from_dt = datetime(2026, 4, 5, 0, 0, 0, tzinfo=UTC)
        to_dt = datetime(2026, 4, 6, 0, 0, 0, tzinfo=UTC)
        result = repo.product_sales_between("コカコーラ", from_dt, to_dt)

        assert result.total_amount == 30000
        assert result.item_count == 10


class TestFindStockByProductName:
    """在庫照会のテスト."""

    def test_found(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = ("コカコーラ", 24)
        repo = ProductRepository(conn)
        result = repo.find_stock_by_product_name("コカコーラ")

        assert result is not None
        assert result == InventoryResult(product_name="コカコーラ", stock_quantity=24)

    def test_not_found(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchone.return_value = None
        repo = ProductRepository(conn)
        result = repo.find_stock_by_product_name("存在しない商品")

        assert result is None


class TestTopProductsBetween:
    """売上トップN取得のテスト."""

    def test_returns_top_products(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchall.return_value = [
            ("コカコーラ", 50000, 100),
            ("お茶", 30000, 75),
        ]
        repo = ProductRepository(conn)
        from_dt = datetime(2026, 4, 5, 0, 0, 0, tzinfo=UTC)
        to_dt = datetime(2026, 4, 6, 0, 0, 0, tzinfo=UTC)
        result = repo.top_products_between(from_dt, to_dt, 5)

        assert len(result) == 2
        assert result[0] == TopProductEntry(rank=1, product_name="コカコーラ", total_amount=50000, quantity_sold=100)
        assert result[1] == TopProductEntry(rank=2, product_name="お茶", total_amount=30000, quantity_sold=75)

    def test_returns_empty_when_no_data(self) -> None:
        conn, cursor = _make_mock_conn()
        cursor.fetchall.return_value = []
        repo = ProductRepository(conn)
        from_dt = datetime(2026, 4, 5, 0, 0, 0, tzinfo=UTC)
        to_dt = datetime(2026, 4, 6, 0, 0, 0, tzinfo=UTC)
        result = repo.top_products_between(from_dt, to_dt, 5)

        assert result == []
