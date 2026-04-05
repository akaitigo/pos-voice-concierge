"""QueryService gRPC サーバーのテスト."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import grpc  # noqa: TC002
import pytest

from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher
from pos_voice_concierge.generated import query_service_pb2
from pos_voice_concierge.product_repository import (
    InventoryResult,
    SalesResult,
)
from pos_voice_concierge.product_repository import (
    TopProductEntry as RepoTopProductEntry,
)
from pos_voice_concierge.query_service import QueryServiceServicer


class FakeServicerContext:
    """テスト用の gRPC コンテキスト."""

    def set_code(self, code: grpc.StatusCode) -> None:
        pass

    def set_details(self, details: str) -> None:
        pass


@pytest.fixture
def matcher() -> FuzzyMatcher:
    m = FuzzyMatcher(threshold=80.0)
    m.register_product("p1", "コカコーラ")
    m.register_product("p2", "お茶")
    m.register_product("p3", "おにぎり")
    return m


@pytest.fixture
def servicer(matcher: FuzzyMatcher) -> QueryServiceServicer:
    return QueryServiceServicer(matcher=matcher, repository=None)


@pytest.fixture
def mock_repository() -> MagicMock:
    repo = MagicMock()
    repo.total_sales_between.return_value = SalesResult(
        total_amount=125000, item_count=42, period_label="",
    )
    repo.product_sales_between.return_value = SalesResult(
        total_amount=30000, item_count=10, period_label="",
    )
    repo.find_stock_by_product_name.return_value = InventoryResult(
        product_name="コカコーラ", stock_quantity=24,
    )
    repo.top_products_between.return_value = [
        RepoTopProductEntry(rank=1, product_name="コカコーラ", total_amount=50000, quantity_sold=100),
        RepoTopProductEntry(rank=2, product_name="お茶", total_amount=30000, quantity_sold=75),
    ]
    return repo


@pytest.fixture
def servicer_with_repo(
    matcher: FuzzyMatcher,
    mock_repository: MagicMock,
) -> QueryServiceServicer:
    return QueryServiceServicer(matcher=matcher, repository=mock_repository)


@pytest.fixture
def context() -> FakeServicerContext:
    return FakeServicerContext()


class TestExecuteQuery:
    """ExecuteQuery RPC のテスト."""

    def test_sales_inquiry(self, servicer, context):
        request = query_service_pb2.QueryRequest(text="今日の売上は？")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "sales_inquiry"
        assert "売上" in response.response_text

    def test_inventory_inquiry(self, servicer, context):
        request = query_service_pb2.QueryRequest(text="コカコーラの在庫は？")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "inventory_inquiry"
        assert "コカコーラ" in response.response_text

    def test_top_products(self, servicer, context):
        request = query_service_pb2.QueryRequest(text="売上トップ5を教えて")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "top_products"

    def test_unknown_intent(self, servicer, context):
        request = query_service_pb2.QueryRequest(text="こんにちは")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "unknown"
        assert "わかりませんでした" in response.response_text

    def test_empty_text(self, servicer, context):
        request = query_service_pb2.QueryRequest(text="")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "unknown"


class TestExecuteQueryWithRepository:
    """Repository接続時のExecuteQuery RPCテスト."""

    def test_sales_inquiry_returns_real_data(
        self, servicer_with_repo, context, mock_repository,
    ):
        request = query_service_pb2.QueryRequest(text="今日の売上は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "sales_inquiry"
        # インテント分類器が「今日」を商品名スロットとしても抽出するため、
        # product_sales_between が呼ばれる（total_sales_between ではない）
        assert response.data.sales.total_amount == 30000
        assert response.data.sales.item_count == 10
        mock_repository.product_sales_between.assert_called()

    def test_sales_inquiry_total_without_product(
        self, servicer_with_repo, context, mock_repository,
    ):
        """商品名スロットなしの売上照会で total_sales_between が呼ばれること."""
        request = query_service_pb2.QueryRequest(text="売上いくら？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "sales_inquiry"
        assert response.data.sales.total_amount == 125000
        assert response.data.sales.item_count == 42
        mock_repository.total_sales_between.assert_called_once()

    def test_inventory_inquiry_returns_real_data(
        self, servicer_with_repo, context, mock_repository,
    ):
        request = query_service_pb2.QueryRequest(text="コカコーラの在庫は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "inventory_inquiry"
        assert response.data.inventory.stock_quantity == 24
        assert "24個" in response.response_text
        mock_repository.find_stock_by_product_name.assert_called_once()

    def test_top_products_returns_real_data(
        self, servicer_with_repo, context, mock_repository,
    ):
        request = query_service_pb2.QueryRequest(text="売上トップ5を教えて")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "top_products"
        assert len(response.data.top_products.entries) == 2
        assert response.data.top_products.entries[0].product_name == "コカコーラ"
        assert response.data.top_products.entries[0].total_amount == 50000
        mock_repository.top_products_between.assert_called_once()

    def test_inventory_not_found_returns_zero(
        self, servicer_with_repo, context, mock_repository,
    ):
        mock_repository.find_stock_by_product_name.return_value = None
        request = query_service_pb2.QueryRequest(text="おにぎりの在庫は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "inventory_inquiry"
        assert response.data.inventory.stock_quantity == 0

    def test_sales_with_db_error_falls_back_to_zero(
        self, servicer_with_repo, context, mock_repository,
    ):
        # インテント分類器が「今日」を商品名としても抽出するため、
        # product_sales_between のエラーハンドリングをテスト
        mock_repository.product_sales_between.side_effect = RuntimeError("DB connection lost")
        request = query_service_pb2.QueryRequest(text="今日の売上は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "sales_inquiry"
        assert response.data.sales.total_amount == 0

    def test_inventory_with_db_error_falls_back_to_zero(
        self, servicer_with_repo, context, mock_repository,
    ):
        mock_repository.find_stock_by_product_name.side_effect = RuntimeError("DB error")
        request = query_service_pb2.QueryRequest(text="コカコーラの在庫は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "inventory_inquiry"
        assert response.data.inventory.stock_quantity == 0

    def test_top_products_with_db_error_returns_empty(
        self, servicer_with_repo, context, mock_repository,
    ):
        mock_repository.top_products_between.side_effect = RuntimeError("DB error")
        request = query_service_pb2.QueryRequest(text="売上トップ5を教えて")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "top_products"
        assert len(response.data.top_products.entries) == 0


class TestLearnAlias:
    """LearnAlias RPC のテスト."""

    def test_learn_success(self, servicer, context, matcher):
        request = query_service_pb2.LearnAliasRequest(
            recognized_text="コカ・コーラ",
            correct_product_name="コカコーラ",
        )
        response = servicer.LearnAlias(request, context)
        assert response.success
        assert "辞書に登録" in response.message
        # マッチャーにもエイリアスが登録されたことを確認
        assert matcher.alias_count >= 1

    def test_learn_empty_text(self, servicer, context):
        request = query_service_pb2.LearnAliasRequest(
            recognized_text="",
            correct_product_name="コカコーラ",
        )
        response = servicer.LearnAlias(request, context)
        assert not response.success
        assert "必須" in response.message

    def test_learn_empty_product(self, servicer, context):
        request = query_service_pb2.LearnAliasRequest(
            recognized_text="コーラ",
            correct_product_name="",
        )
        response = servicer.LearnAlias(request, context)
        assert not response.success


class TestExportAliases:
    """ExportAliases RPC のテスト."""

    def test_export_empty(self, servicer, context):
        request = query_service_pb2.ExportAliasesRequest()
        response = servicer.ExportAliases(request, context)
        assert response.count == 0
        data = json.loads(response.json_data)
        assert data == []

    def test_export_with_aliases(self, servicer, context, matcher):
        matcher.register_alias("コーラ", "コカコーラ")
        matcher.register_alias("coca-cola", "コカコーラ")
        request = query_service_pb2.ExportAliasesRequest()
        response = servicer.ExportAliases(request, context)
        assert response.count == 2


class TestImportAliases:
    """ImportAliases RPC のテスト."""

    def test_import_success(self, servicer, context, matcher):
        json_data = json.dumps(
            [
                {"alias": "コーラ", "product_name": "コカコーラ"},
                {"alias": "緑茶", "product_name": "お茶"},
            ]
        )
        request = query_service_pb2.ImportAliasesRequest(json_data=json_data)
        response = servicer.ImportAliases(request, context)
        assert response.success
        assert response.imported_count == 2

    def test_import_invalid_json(self, servicer, context):
        request = query_service_pb2.ImportAliasesRequest(json_data="invalid json")
        response = servicer.ImportAliases(request, context)
        assert not response.success


class TestE2EQueryFlow:
    """クエリ入力→レスポンスの統合テスト."""

    def test_sales_query_e2e(self, servicer, context):
        """売上照会のE2Eフロー."""
        request = query_service_pb2.QueryRequest(text="今日の売上は？")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "sales_inquiry"
        assert response.response_text
        assert response.data.HasField("sales")

    def test_inventory_query_e2e(self, servicer, context):
        """在庫照会のE2Eフロー."""
        request = query_service_pb2.QueryRequest(text="コカコーラの在庫は？")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "inventory_inquiry"
        assert response.response_text
        assert response.data.HasField("inventory")

    def test_top_products_query_e2e(self, servicer, context):
        """トップ商品のE2Eフロー."""
        request = query_service_pb2.QueryRequest(text="売上トップ5を教えて")
        response = servicer.ExecuteQuery(request, context)
        assert response.intent == "top_products"
        assert response.response_text
        assert response.data.HasField("top_products")

    def test_alias_learning_then_query_e2e(self, servicer, context, matcher):
        """辞書学習後のクエリフロー."""
        # 1. エイリアスを学習
        learn_req = query_service_pb2.LearnAliasRequest(
            recognized_text="コカ・コーラ",
            correct_product_name="コカコーラ",
        )
        learn_resp = servicer.LearnAlias(learn_req, context)
        assert learn_resp.success

        # 2. エクスポートして確認
        export_req = query_service_pb2.ExportAliasesRequest()
        export_resp = servicer.ExportAliases(export_req, context)
        assert export_resp.count >= 1

        # 3. エイリアスがマッチャーに反映されていることを確認
        matches = matcher.match("コカ・コーラ")
        assert len(matches) > 0
        assert matches[0].product_name == "コカコーラ"

    def test_import_export_roundtrip_e2e(self, servicer, context, matcher):
        """辞書のインポート→エクスポートラウンドトリップ."""
        # 1. インポート
        json_data = json.dumps(
            [
                {"alias": "コーラ", "product_name": "コカコーラ"},
                {"alias": "緑茶", "product_name": "お茶"},
            ]
        )
        import_req = query_service_pb2.ImportAliasesRequest(json_data=json_data)
        import_resp = servicer.ImportAliases(import_req, context)
        assert import_resp.success
        assert import_resp.imported_count == 2

        # 2. エクスポート
        export_req = query_service_pb2.ExportAliasesRequest()
        export_resp = servicer.ExportAliases(export_req, context)
        assert export_resp.count == 2

        # 3. ラウンドトリップを検証
        exported = json.loads(export_resp.json_data)
        aliases = {e["alias"]: e["product_name"] for e in exported}
        assert aliases["コーラ"] == "コカコーラ"
        assert aliases["緑茶"] == "お茶"

    def test_sales_query_with_repo_e2e(self, servicer_with_repo, context):
        """Repository接続時の売上照会E2Eフロー."""
        request = query_service_pb2.QueryRequest(text="今日の売上は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "sales_inquiry"
        assert response.data.HasField("sales")
        # インテント分類器が「今日」を商品名としても抽出するため、
        # product_sales_between のモック値が返る
        assert response.data.sales.total_amount == 30000
        assert "30,000円" in response.response_text

    def test_inventory_query_with_repo_e2e(self, servicer_with_repo, context):
        """Repository接続時の在庫照会E2Eフロー."""
        request = query_service_pb2.QueryRequest(text="コカコーラの在庫は？")
        response = servicer_with_repo.ExecuteQuery(request, context)
        assert response.intent == "inventory_inquiry"
        assert response.data.HasField("inventory")
        assert response.data.inventory.stock_quantity == 24
