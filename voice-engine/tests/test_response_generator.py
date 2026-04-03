"""レスポンス文生成のテスト."""

from __future__ import annotations

from pos_voice_concierge.response_generator import (
    InventoryData,
    SalesData,
    TopProductEntry,
    generate_error_response,
    generate_inventory_response,
    generate_sales_response,
    generate_top_products_response,
)


class TestGenerateSalesResponse:
    """売上レスポンス文のテスト."""

    def test_basic_sales(self):
        data = SalesData(total_amount=50000, period_label="今日")
        result = generate_sales_response(data)
        assert "50,000円" in result
        assert "今日" in result

    def test_sales_with_item_count(self):
        data = SalesData(total_amount=100000, period_label="今月", item_count=42)
        result = generate_sales_response(data)
        assert "100,000円" in result
        assert "42件" in result

    def test_zero_sales(self):
        data = SalesData(total_amount=0, period_label="昨日")
        result = generate_sales_response(data)
        assert "0円" in result


class TestGenerateInventoryResponse:
    """在庫レスポンス文のテスト."""

    def test_in_stock(self):
        data = InventoryData(product_name="コーラ", stock_quantity=24)
        result = generate_inventory_response(data)
        assert "コーラ" in result
        assert "24個" in result

    def test_out_of_stock(self):
        data = InventoryData(product_name="ポテチ", stock_quantity=0)
        result = generate_inventory_response(data)
        assert "ポテチ" in result
        assert "ありません" in result

    def test_negative_stock(self):
        data = InventoryData(product_name="お茶", stock_quantity=-1)
        result = generate_inventory_response(data)
        assert "ありません" in result


class TestGenerateTopProductsResponse:
    """トップ商品レスポンス文のテスト."""

    def test_top_products(self):
        entries = [
            TopProductEntry(rank=1, product_name="コーラ", total_amount=50000, quantity_sold=100),
            TopProductEntry(rank=2, product_name="お茶", total_amount=30000, quantity_sold=75),
        ]
        result = generate_top_products_response(entries, "今日")
        assert "トップ2" in result
        assert "コーラ" in result
        assert "お茶" in result
        assert "第1位" in result
        assert "第2位" in result

    def test_empty_top_products(self):
        result = generate_top_products_response([], "今月")
        assert "データがありません" in result


class TestGenerateErrorResponse:
    """エラーレスポンス文のテスト."""

    def test_unknown_intent(self):
        result = generate_error_response("unknown_intent")
        assert "わかりませんでした" in result

    def test_product_not_found(self):
        result = generate_error_response("product_not_found")
        assert "見つかりません" in result

    def test_unknown_error_type(self):
        result = generate_error_response("nonexistent_type")
        assert "エラー" in result
