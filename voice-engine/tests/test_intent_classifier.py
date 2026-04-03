"""インテント分類器のテスト.

20パターン以上で90%以上の精度を要求。
"""

from __future__ import annotations

from typing import ClassVar

from pos_voice_concierge.intent_classifier import Intent, classify


class TestIntentClassification:
    """インテント分類のテスト."""

    # --- 売上照会 ---

    def test_sales_today(self):
        result = classify("今日の売上は？")
        assert result.intent == Intent.SALES_INQUIRY

    def test_sales_today_variant(self):
        result = classify("本日の売上を教えて")
        assert result.intent == Intent.SALES_INQUIRY

    def test_sales_this_month(self):
        result = classify("今月の売上はいくら？")
        assert result.intent == Intent.SALES_INQUIRY

    def test_sales_yesterday(self):
        result = classify("昨日の売上は？")
        assert result.intent == Intent.SALES_INQUIRY

    def test_sales_last_week(self):
        result = classify("先週の売上を確認したい")
        assert result.intent == Intent.SALES_INQUIRY

    def test_sales_last_month(self):
        result = classify("先月の売り上げはどれくらい？")
        assert result.intent == Intent.SALES_INQUIRY

    # --- 在庫照会 ---

    def test_inventory_product(self):
        result = classify("コカコーラの在庫は？")
        assert result.intent == Intent.INVENTORY_INQUIRY

    def test_inventory_remaining(self):
        result = classify("おにぎりは残りいくつある？")
        assert result.intent == Intent.INVENTORY_INQUIRY

    def test_inventory_stock(self):
        result = classify("ポテトチップスの在庫を確認")
        assert result.intent == Intent.INVENTORY_INQUIRY

    def test_inventory_how_many(self):
        result = classify("お茶は何個ある？")
        assert result.intent == Intent.INVENTORY_INQUIRY

    # --- トップ商品 ---

    def test_top_products_basic(self):
        result = classify("売上トップ5を教えて")
        assert result.intent == Intent.TOP_PRODUCTS

    def test_top_products_ranking(self):
        result = classify("今月のランキングは？")
        assert result.intent == Intent.TOP_PRODUCTS

    def test_top_products_best_selling(self):
        result = classify("一番売れている商品は？")
        assert result.intent == Intent.TOP_PRODUCTS

    def test_top_products_popular(self):
        result = classify("人気商品を教えて")
        assert result.intent == Intent.TOP_PRODUCTS

    def test_top_products_uresiji(self):
        result = classify("売れ筋は何？")
        assert result.intent == Intent.TOP_PRODUCTS

    # --- 商品登録 ---

    def test_registration_add_to_cart(self):
        result = classify("コーラを3つ追加してください")
        assert result.intent == Intent.PRODUCT_REGISTRATION

    def test_registration_register(self):
        result = classify("おにぎりを登録して")
        assert result.intent == Intent.PRODUCT_REGISTRATION

    # --- 不明 ---

    def test_unknown_greeting(self):
        result = classify("こんにちは")
        assert result.intent == Intent.UNKNOWN

    def test_unknown_empty(self):
        result = classify("")
        assert result.intent == Intent.UNKNOWN

    def test_unknown_random(self):
        result = classify("天気はどうですか")
        assert result.intent == Intent.UNKNOWN


class TestSlotExtraction:
    """スロット抽出のテスト."""

    def test_date_slot_today(self):
        result = classify("今日の売上は？")
        date_slots = [s for s in result.slots if s.name == "date_range"]
        assert len(date_slots) == 1
        assert date_slots[0].value == "today"

    def test_date_slot_yesterday(self):
        result = classify("昨日の売上は？")
        date_slots = [s for s in result.slots if s.name == "date_range"]
        assert len(date_slots) == 1
        assert date_slots[0].value == "yesterday"

    def test_date_slot_this_month(self):
        result = classify("今月の売上は？")
        date_slots = [s for s in result.slots if s.name == "date_range"]
        assert len(date_slots) == 1
        assert date_slots[0].value == "this_month"

    def test_date_slot_this_week(self):
        result = classify("今週の売上を教えて")
        date_slots = [s for s in result.slots if s.name == "date_range"]
        assert len(date_slots) == 1
        assert date_slots[0].value == "this_week"

    def test_top_n_explicit(self):
        result = classify("売上トップ3を教えて")
        n_slots = [s for s in result.slots if s.name == "top_n"]
        assert len(n_slots) == 1
        assert n_slots[0].value == "3"

    def test_top_n_default(self):
        result = classify("売れ筋は何？")
        n_slots = [s for s in result.slots if s.name == "top_n"]
        assert len(n_slots) == 1
        assert n_slots[0].value == "5"

    def test_product_name_extraction(self):
        result = classify("コカコーラの在庫は？")
        product_slots = [s for s in result.slots if s.name == "product_name"]
        assert len(product_slots) == 1
        assert product_slots[0].value == "コカコーラ"

    def test_product_name_extraction_onigiri(self):
        result = classify("おにぎりの在庫は？")
        product_slots = [s for s in result.slots if s.name == "product_name"]
        assert len(product_slots) == 1
        assert product_slots[0].value == "おにぎり"


class TestAccuracyRequirement:
    """インテント分類の精度テスト.

    20パターン以上で90%以上の精度を要求する。
    """

    INTENT_TEST_CASES: ClassVar[list[tuple[str, Intent]]] = [
        # 売上照会 (7パターン)
        ("今日の売上は？", Intent.SALES_INQUIRY),
        ("本日の売上はいくらですか", Intent.SALES_INQUIRY),
        ("今月の売上を教えて", Intent.SALES_INQUIRY),
        ("昨日の売上は？", Intent.SALES_INQUIRY),
        ("先週の売り上げはどうだった？", Intent.SALES_INQUIRY),
        ("先月の売上はいくらですか？", Intent.SALES_INQUIRY),
        ("売上を確認したい", Intent.SALES_INQUIRY),
        # 在庫照会 (5パターン)
        ("コカコーラの在庫は？", Intent.INVENTORY_INQUIRY),
        ("おにぎりは残りいくつある？", Intent.INVENTORY_INQUIRY),
        ("ポテトチップスの在庫を確認", Intent.INVENTORY_INQUIRY),
        ("お茶は何個ある？", Intent.INVENTORY_INQUIRY),
        ("サンドイッチの在庫は？", Intent.INVENTORY_INQUIRY),
        # トップ商品 (5パターン)
        ("売上トップ5を教えて", Intent.TOP_PRODUCTS),
        ("今月のランキングは？", Intent.TOP_PRODUCTS),
        ("一番売れている商品は？", Intent.TOP_PRODUCTS),
        ("人気商品を教えて", Intent.TOP_PRODUCTS),
        ("売れ筋は何？", Intent.TOP_PRODUCTS),
        # 商品登録 (2パターン)
        ("コーラを3つ追加してください", Intent.PRODUCT_REGISTRATION),
        ("おにぎりを登録して", Intent.PRODUCT_REGISTRATION),
        # 不明 (3パターン)
        ("こんにちは", Intent.UNKNOWN),
        ("天気はどうですか", Intent.UNKNOWN),
        ("明日の予定は？", Intent.UNKNOWN),
    ]

    def test_accuracy_above_90_percent(self):
        """22パターンのテストセットで90%以上の精度を確認."""
        total = len(self.INTENT_TEST_CASES)
        correct = 0

        for text, expected_intent in self.INTENT_TEST_CASES:
            result = classify(text)
            if result.intent == expected_intent:
                correct += 1

        accuracy = correct / total
        assert accuracy >= 0.9, f"精度 {accuracy:.1%} ({correct}/{total}) は要件の90%を満たしていません"

    def test_at_least_20_patterns(self):
        """テストセットが20パターン以上あることを確認."""
        assert len(self.INTENT_TEST_CASES) >= 20


class TestConfidence:
    """信頼度スコアのテスト."""

    def test_confidence_positive(self):
        result = classify("今日の売上は？")
        assert result.confidence > 0.0

    def test_confidence_max_1(self):
        result = classify("今日の売上は？")
        assert result.confidence <= 1.0

    def test_unknown_confidence_zero(self):
        result = classify("こんにちは")
        assert result.confidence == 0.0
