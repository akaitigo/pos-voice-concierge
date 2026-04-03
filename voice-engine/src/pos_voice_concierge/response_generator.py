"""レスポンス文生成モジュール.

テンプレートベースでクエリ結果を自然な日本語レスポンスに変換する。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SalesData:
    """売上データ."""

    total_amount: int
    period_label: str
    item_count: int = 0


@dataclass(frozen=True)
class InventoryData:
    """在庫データ."""

    product_name: str
    stock_quantity: int


@dataclass(frozen=True)
class TopProductEntry:
    """売上トップ商品エントリ."""

    rank: int
    product_name: str
    total_amount: int
    quantity_sold: int


def generate_sales_response(data: SalesData) -> str:
    """売上照会のレスポンス文を生成する.

    Args:
        data: 売上データ

    Returns:
        レスポンス文
    """
    amount_str = f"{data.total_amount:,}"

    if data.item_count > 0:
        return f"{data.period_label}の売上は{amount_str}円です。合計{data.item_count}件の取引がありました。"
    return f"{data.period_label}の売上は{amount_str}円です。"


def generate_inventory_response(data: InventoryData) -> str:
    """在庫照会のレスポンス文を生成する.

    Args:
        data: 在庫データ

    Returns:
        レスポンス文
    """
    if data.stock_quantity <= 0:
        return f"{data.product_name}の在庫はありません。"

    return f"{data.product_name}の在庫は{data.stock_quantity}個です。"


def generate_top_products_response(
    entries: list[TopProductEntry],
    period_label: str,
) -> str:
    """売上トップ商品のレスポンス文を生成する.

    Args:
        entries: トップ商品リスト
        period_label: 期間ラベル

    Returns:
        レスポンス文
    """
    if not entries:
        return f"{period_label}の売上データがありません。"

    lines: list[str] = [f"{period_label}の売上トップ{len(entries)}です。"]
    for entry in entries:
        amount_str = f"{entry.total_amount:,}"
        lines.append(f"第{entry.rank}位、{entry.product_name}、{amount_str}円、{entry.quantity_sold}個販売。")

    return "".join(lines)


def generate_error_response(error_type: str) -> str:
    """エラーレスポンス文を生成する.

    Args:
        error_type: エラー種別

    Returns:
        エラーレスポンス文
    """
    error_messages: dict[str, str] = {
        "unknown_intent": "すみません、質問の意図がわかりませんでした。もう一度お願いします。",
        "product_not_found": "指定された商品が見つかりませんでした。",
        "no_data": "該当するデータがありませんでした。",
        "server_error": "サーバーエラーが発生しました。しばらくしてからもう一度お試しください。",
    }
    return error_messages.get(error_type, "エラーが発生しました。")
