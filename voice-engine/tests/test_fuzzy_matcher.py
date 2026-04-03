"""FuzzyMatcher のテスト."""

from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher


class TestFuzzyMatcher:
    """FuzzyMatcher のテストケース."""

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
