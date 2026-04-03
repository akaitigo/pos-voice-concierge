"""quantity_parser のテスト."""

from pos_voice_concierge.quantity_parser import ParsedUtterance, parse_utterance


class TestBasicQuantityParsing:
    """基本的な数量パース."""

    def test_trailing_quantity_tsu(self) -> None:
        """「○○を3つ」パターン."""
        result = parse_utterance("コーラを3つ")
        assert result == ParsedUtterance(product_query="コーラ", quantity=3, unit="つ")

    def test_trailing_quantity_ko(self) -> None:
        """「○○ 5個」パターン."""
        result = parse_utterance("おにぎり 5個")
        assert result == ParsedUtterance(product_query="おにぎり", quantity=5, unit="個")

    def test_trailing_quantity_hon(self) -> None:
        """「○○2本」パターン."""
        result = parse_utterance("お茶2本")
        assert result == ParsedUtterance(product_query="お茶", quantity=2, unit="本")

    def test_trailing_quantity_fukuro(self) -> None:
        """「○○1袋」パターン."""
        result = parse_utterance("ポテチ1袋")
        assert result == ParsedUtterance(product_query="ポテチ", quantity=1, unit="袋")

    def test_trailing_quantity_hako(self) -> None:
        """「○○3箱」パターン."""
        result = parse_utterance("ティッシュ3箱")
        assert result == ParsedUtterance(product_query="ティッシュ", quantity=3, unit="箱")

    def test_trailing_quantity_pack(self) -> None:
        """「○○2パック」パターン."""
        result = parse_utterance("納豆2パック")
        assert result == ParsedUtterance(product_query="納豆", quantity=2, unit="パック")


class TestWeightVolumeUnits:
    """重さ・容量の単位テスト."""

    def test_quantity_kg(self) -> None:
        result = parse_utterance("りんご2kg")
        assert result == ParsedUtterance(product_query="りんご", quantity=2, unit="kg")

    def test_quantity_g(self) -> None:
        result = parse_utterance("ハム100g")
        assert result == ParsedUtterance(product_query="ハム", quantity=100, unit="g")

    def test_quantity_ml(self) -> None:
        result = parse_utterance("牛乳200ml")
        assert result == ParsedUtterance(product_query="牛乳", quantity=200, unit="ml")

    def test_quantity_l(self) -> None:
        result = parse_utterance("水1L")
        assert result == ParsedUtterance(product_query="水", quantity=1, unit="L")


class TestLeadingQuantity:
    """先頭数量パターンのテスト."""

    def test_leading_quantity(self) -> None:
        """「3つのコーラ」パターン."""
        result = parse_utterance("3つのコーラ")
        assert result == ParsedUtterance(product_query="コーラ", quantity=3, unit="つ")

    def test_leading_quantity_with_wo(self) -> None:
        """「5個をおにぎり」は不自然だが一応パースできる."""
        result = parse_utterance("5個をおにぎり")
        assert result.quantity == 5
        assert result.unit == "個"


class TestKanjiNumbers:
    """漢数字の数量テスト."""

    def test_kanji_hitotsu(self) -> None:
        result = parse_utterance("おにぎり一つ")
        assert result == ParsedUtterance(product_query="おにぎり", quantity=1, unit="つ")

    def test_kanji_mittsu(self) -> None:
        result = parse_utterance("パン三つ")
        assert result == ParsedUtterance(product_query="パン", quantity=3, unit="つ")

    def test_kanji_go_ko(self) -> None:
        result = parse_utterance("りんご五個")
        assert result == ParsedUtterance(product_query="りんご", quantity=5, unit="個")

    def test_kanji_ju(self) -> None:
        result = parse_utterance("たまご十個")
        assert result == ParsedUtterance(product_query="たまご", quantity=10, unit="個")


class TestNoQuantity:
    """数量指定なしのテスト."""

    def test_no_quantity(self) -> None:
        result = parse_utterance("コーラ")
        assert result == ParsedUtterance(product_query="コーラ", quantity=1, unit="")

    def test_empty_string(self) -> None:
        result = parse_utterance("")
        assert result == ParsedUtterance(product_query="", quantity=1, unit="")

    def test_whitespace_only(self) -> None:
        result = parse_utterance("  ")
        assert result == ParsedUtterance(product_query="", quantity=1, unit="")


class TestWithParticle:
    """助詞付きパターンのテスト."""

    def test_wo_particle(self) -> None:
        """「を」付き."""
        result = parse_utterance("コーラを3つ")
        assert result.product_query == "コーラ"
        assert result.quantity == 3

    def test_no_particle(self) -> None:
        """「の」付き."""
        result = parse_utterance("コーラの3つ")
        assert result.product_query == "コーラ"
        assert result.quantity == 3


class TestComplexProductNames:
    """複雑な商品名のテスト."""

    def test_product_with_size(self) -> None:
        result = parse_utterance("コカ・コーラ 500mlを2本")
        assert result.product_query == "コカ・コーラ 500ml"
        assert result.quantity == 2
        assert result.unit == "本"

    def test_product_with_spaces(self) -> None:
        result = parse_utterance("カルビー ポテトチップス 3袋")
        assert result.product_query == "カルビー ポテトチップス"
        assert result.quantity == 3
        assert result.unit == "袋"
