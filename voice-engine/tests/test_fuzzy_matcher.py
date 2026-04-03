"""FuzzyMatcher のテスト."""

import json
import time
from pathlib import Path

import pytest

from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher


class TestFuzzyMatcherBasic:
    """FuzzyMatcher の基本テストケース."""

    def setup_method(self) -> None:
        self.matcher = FuzzyMatcher(threshold=70.0)
        self.matcher.register_product("P001", "コカ・コーラ 500ml")
        self.matcher.register_product("P002", "サントリー天然水 550ml")
        self.matcher.register_product("P003", "カルビーポテトチップス うすしお")

    def test_exact_match(self) -> None:
        results = self.matcher.match("コカ・コーラ 500ml")
        assert len(results) > 0
        assert results[0].product_id == "P001"
        assert results[0].score >= 90.0

    def test_fuzzy_match_without_separator(self) -> None:
        results = self.matcher.match("コカコーラ")
        assert len(results) > 0
        assert results[0].product_name == "コカ・コーラ 500ml"

    def test_alias_match(self) -> None:
        self.matcher.register_alias("コーラ", "コカ・コーラ 500ml")
        results = self.matcher.match("コーラ")
        assert len(results) > 0
        assert results[0].product_id == "P001"

    def test_no_match_below_threshold(self) -> None:
        results = self.matcher.match("完全に無関係な文字列")
        assert len(results) == 0

    def test_limit_results(self) -> None:
        results = self.matcher.match("コ", limit=2)
        assert len(results) <= 2

    def test_empty_products(self) -> None:
        empty_matcher = FuzzyMatcher()
        results = empty_matcher.match("何か")
        assert len(results) == 0


class TestFuzzyMatcherThreshold:
    """閾値カスタマイズのテスト."""

    def test_default_threshold(self) -> None:
        matcher = FuzzyMatcher()
        assert matcher.threshold == 80.0

    def test_custom_threshold(self) -> None:
        matcher = FuzzyMatcher(threshold=60.0)
        assert matcher.threshold == 60.0

    def test_update_threshold(self) -> None:
        matcher = FuzzyMatcher()
        matcher.threshold = 50.0
        assert matcher.threshold == 50.0

    def test_invalid_threshold_too_high(self) -> None:
        with pytest.raises(ValueError, match="threshold must be between"):
            FuzzyMatcher(threshold=101.0)

    def test_invalid_threshold_too_low(self) -> None:
        with pytest.raises(ValueError, match="threshold must be between"):
            FuzzyMatcher(threshold=-1.0)

    def test_invalid_threshold_setter(self) -> None:
        matcher = FuzzyMatcher()
        with pytest.raises(ValueError, match="threshold must be between"):
            matcher.threshold = 200.0

    def test_lower_threshold_returns_more_results(self) -> None:
        strict = FuzzyMatcher(threshold=95.0)
        lenient = FuzzyMatcher(threshold=50.0)
        strict.register_product("P001", "コカ・コーラ 500ml")
        lenient.register_product("P001", "コカ・コーラ 500ml")

        strict_results = strict.match("コーラ")
        lenient_results = lenient.match("コーラ")
        assert len(lenient_results) >= len(strict_results)


class TestJapaneseFuzzyVariations:
    """日本語表記ゆれパターンのテスト."""

    def setup_method(self) -> None:
        self.matcher = FuzzyMatcher(threshold=60.0)
        self.matcher.register_product("P001", "コカ・コーラ 500ml")
        self.matcher.register_product("P002", "サントリー天然水 550ml")
        self.matcher.register_product("P003", "カルビーポテトチップス うすしお")
        self.matcher.register_product("P004", "ファミリーマートのおにぎり")
        self.matcher.register_product("P005", "ヨーグルト")
        self.matcher.register_product("P006", "カップヌードル")
        self.matcher.register_product("P007", "ポッキー チョコレート")

    def test_nakaguro_variation(self) -> None:
        """中黒（・）の有無による表記ゆれ."""
        results = self.matcher.match("コカコーラ")
        assert len(results) > 0
        assert results[0].product_id == "P001"

    def test_long_vowel_variation(self) -> None:
        """長音記号（ー）の揺れ."""
        self.matcher.register_alias("ヨグルト", "ヨーグルト")
        results = self.matcher.match("ヨグルト")
        assert len(results) > 0
        assert results[0].product_id == "P005"

    def test_katakana_partial_match(self) -> None:
        """カタカナの部分一致."""
        results = self.matcher.match("ポテトチップス")
        assert len(results) > 0
        assert results[0].product_id == "P003"

    def test_alias_with_abbreviation(self) -> None:
        """略称エイリアス."""
        self.matcher.register_alias("ポテチ", "カルビーポテトチップス うすしお")
        results = self.matcher.match("ポテチ")
        assert len(results) > 0
        assert results[0].product_id == "P003"

    def test_alias_with_common_name(self) -> None:
        """通称エイリアス."""
        self.matcher.register_alias("カップ麺", "カップヌードル")
        results = self.matcher.match("カップ麺")
        assert len(results) > 0
        assert results[0].product_id == "P006"

    def test_with_space_variations(self) -> None:
        """スペースの有無による表記ゆれ."""
        results = self.matcher.match("ポッキーチョコレート")
        assert len(results) > 0
        assert results[0].product_id == "P007"

    def test_brand_name_only(self) -> None:
        """ブランド名のみで検索."""
        results = self.matcher.match("カルビー")
        assert len(results) > 0
        assert results[0].product_id == "P003"

    def test_deduplication_via_alias(self) -> None:
        """エイリアス経由の結果が重複しないこと."""
        self.matcher.register_alias("コーラ", "コカ・コーラ 500ml")
        self.matcher.register_alias("Cola", "コカ・コーラ 500ml")
        results = self.matcher.match("コカ・コーラ 500ml", limit=5)
        product_ids = [r.product_id for r in results]
        assert len(product_ids) == len(set(product_ids))


class TestAliasLearning:
    """表記ゆれ辞書の学習テスト."""

    def setup_method(self) -> None:
        self.matcher = FuzzyMatcher(threshold=60.0)
        self.matcher.register_product("P001", "コカ・コーラ 500ml")

    def test_learn_alias_from_correction(self) -> None:
        self.matcher.learn_alias("コーラ五百ミリ", "コカ・コーラ 500ml")
        results = self.matcher.match("コーラ五百ミリ")
        assert len(results) > 0
        assert results[0].product_id == "P001"

    def test_learn_alias_same_name_ignored(self) -> None:
        self.matcher.learn_alias("コカ・コーラ 500ml", "コカ・コーラ 500ml")
        assert self.matcher.alias_count == 0

    def test_learn_alias_unregistered_product(self) -> None:
        self.matcher.learn_alias("何か", "存在しない商品")
        assert self.matcher.alias_count == 0

    def test_get_aliases_for_product(self) -> None:
        self.matcher.register_alias("コーラ", "コカ・コーラ 500ml")
        self.matcher.register_alias("Cola", "コカ・コーラ 500ml")
        aliases = self.matcher.get_aliases_for_product("コカ・コーラ 500ml")
        assert set(aliases) == {"コーラ", "Cola"}


class TestBulkRegistration:
    """一括登録のテスト."""

    def test_register_products_bulk(self) -> None:
        matcher = FuzzyMatcher(threshold=60.0)
        matcher.register_products(
            [
                ("P001", "コカ・コーラ 500ml"),
                ("P002", "サントリー天然水 550ml"),
            ]
        )
        assert matcher.product_count == 2
        results = matcher.match("コカ・コーラ")
        assert len(results) > 0
        assert results[0].product_id == "P001"

    def test_register_aliases_bulk(self) -> None:
        matcher = FuzzyMatcher(threshold=60.0)
        matcher.register_product("P001", "コカ・コーラ 500ml")
        matcher.register_aliases(
            [
                ("コーラ", "コカ・コーラ 500ml"),
                ("Cola", "コカ・コーラ 500ml"),
            ]
        )
        assert matcher.alias_count == 2


class TestExportImport:
    """エクスポート/インポートのテスト."""

    def setup_method(self) -> None:
        self.matcher = FuzzyMatcher(threshold=60.0)
        self.matcher.register_product("P001", "コカ・コーラ 500ml")
        self.matcher.register_alias("コーラ", "コカ・コーラ 500ml")
        self.matcher.register_alias("Cola", "コカ・コーラ 500ml")

    def test_export_import_file(self, tmp_path) -> None:
        export_path = tmp_path / "aliases.json"
        count = self.matcher.export_aliases(export_path)
        assert count == 2
        assert export_path.exists()

        new_matcher = FuzzyMatcher(threshold=60.0)
        new_matcher.register_product("P001", "コカ・コーラ 500ml")
        imported = new_matcher.import_aliases(export_path)
        assert imported == 2
        results = new_matcher.match("コーラ")
        assert len(results) > 0
        assert results[0].product_id == "P001"

    def test_export_import_json_string(self) -> None:
        json_str = self.matcher.export_aliases_json()
        data = json.loads(json_str)
        assert len(data) == 2

        new_matcher = FuzzyMatcher(threshold=60.0)
        new_matcher.register_product("P001", "コカ・コーラ 500ml")
        imported = new_matcher.import_aliases_json(json_str)
        assert imported == 2
        results = new_matcher.match("Cola")
        assert len(results) > 0
        assert results[0].product_id == "P001"

    def test_export_sorted_order(self) -> None:
        json_str = self.matcher.export_aliases_json()
        data = json.loads(json_str)
        aliases = [entry["alias"] for entry in data]
        assert aliases == sorted(aliases)

    def test_import_invalid_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            self.matcher.import_aliases_json("not valid json")

    def test_import_missing_field(self) -> None:
        invalid_json = json.dumps([{"alias": "test"}])
        with pytest.raises(KeyError):
            self.matcher.import_aliases_json(invalid_json)

    def test_import_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            self.matcher.import_aliases(Path("/nonexistent/path.json"))


class TestMatchingPerformance:
    """マッチング処理のレイテンシテスト."""

    @pytest.mark.slow
    def test_latency_with_1000_products(self) -> None:
        """1000商品マスタでのマッチングが100ms以内に完了すること."""
        matcher = FuzzyMatcher(threshold=80.0)
        for i in range(1000):
            matcher.register_product(f"P{i:04d}", f"テスト商品{i:04d} カテゴリ{i % 10}")

        # ウォームアップ
        matcher.match("テスト商品0500")

        # 計測（10回の平均）
        iterations = 10
        total_time = 0.0
        for _ in range(iterations):
            start = time.perf_counter()
            matcher.match("テスト商品0500")
            elapsed = (time.perf_counter() - start) * 1000  # ms
            total_time += elapsed

        avg_latency = total_time / iterations
        assert avg_latency < 100.0, f"Average latency {avg_latency:.1f}ms exceeds 100ms threshold"

    @pytest.mark.slow
    def test_latency_with_1000_products_and_aliases(self) -> None:
        """1000商品+500エイリアスでのマッチングが100ms以内に完了すること."""
        matcher = FuzzyMatcher(threshold=80.0)
        for i in range(1000):
            matcher.register_product(f"P{i:04d}", f"テスト商品{i:04d} カテゴリ{i % 10}")
        for i in range(500):
            matcher.register_alias(
                f"別名{i:04d}",
                f"テスト商品{i:04d} カテゴリ{i % 10}",
            )

        # ウォームアップ
        matcher.match("テスト商品0500")

        # 計測
        iterations = 10
        total_time = 0.0
        for _ in range(iterations):
            start = time.perf_counter()
            matcher.match("テスト商品0500")
            elapsed = (time.perf_counter() - start) * 1000
            total_time += elapsed

        avg_latency = total_time / iterations
        assert avg_latency < 100.0, f"Average latency {avg_latency:.1f}ms exceeds 100ms threshold"


class TestClear:
    """クリア機能のテスト."""

    def test_clear_removes_all(self) -> None:
        matcher = FuzzyMatcher()
        matcher.register_product("P001", "テスト商品")
        matcher.register_alias("テスト", "テスト商品")
        matcher.clear()
        assert matcher.product_count == 0
        assert matcher.alias_count == 0
        assert len(matcher.match("テスト商品")) == 0
