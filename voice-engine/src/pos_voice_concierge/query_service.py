"""QueryService gRPC サーバー実装.

自然言語クエリの処理、表記ゆれ辞書管理を提供する。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pos_voice_concierge.generated import query_service_pb2, query_service_pb2_grpc
from pos_voice_concierge.intent_classifier import Intent, classify
from pos_voice_concierge.response_generator import (
    generate_error_response,
    generate_inventory_response,
    generate_sales_response,
    generate_top_products_response,
)

if TYPE_CHECKING:
    import grpc

    from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher
    from pos_voice_concierge.product_repository import ProductRepository

logger = logging.getLogger(__name__)

_JST = ZoneInfo("Asia/Tokyo")

_PERIOD_MAP: dict[str, str] = {
    "today": "今日",
    "yesterday": "昨日",
    "this_week": "今週",
    "last_week": "先週",
    "this_month": "今月",
    "last_month": "先月",
}


def _resolve_period(period_key: str) -> tuple[datetime, datetime]:
    """期間キーからUTC datetime の (from, to) を返す.

    Args:
        period_key: 期間キー（today, yesterday, this_week, etc.）

    Returns:
        (from_dt, to_dt) のタプル（両方 aware datetime, UTC）
    """
    now_jst = datetime.now(tz=_JST)
    today = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)

    if period_key == "today":
        from_dt = today
        to_dt = today + timedelta(days=1)
    elif period_key == "yesterday":
        from_dt = today - timedelta(days=1)
        to_dt = today
    elif period_key == "this_week":
        monday = today - timedelta(days=today.weekday())
        from_dt = monday
        to_dt = today + timedelta(days=1)
    elif period_key == "last_week":
        monday = today - timedelta(days=today.weekday())
        last_monday = monday - timedelta(weeks=1)
        from_dt = last_monday
        to_dt = monday
    elif period_key == "this_month":
        from_dt = today.replace(day=1)
        to_dt = today + timedelta(days=1)
    elif period_key == "last_month":
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        from_dt = last_month_end.replace(day=1)
        to_dt = first_this_month
    else:
        from_dt = today
        to_dt = today + timedelta(days=1)

    return (from_dt.astimezone(UTC), to_dt.astimezone(UTC))


class QueryServiceServicer(query_service_pb2_grpc.QueryServiceServicer):
    """QueryService gRPC サーバー実装."""

    def __init__(
        self,
        matcher: FuzzyMatcher,
        repository: ProductRepository | None = None,
    ) -> None:
        """初期化.

        Args:
            matcher: ファジーマッチャー
            repository: 商品リポジトリ（DB接続時）
        """
        self._matcher = matcher
        self._repository = repository

    def ExecuteQuery(  # noqa: N802
        self,
        request: query_service_pb2.QueryRequest,
        context: grpc.ServicerContext,  # noqa: ARG002
    ) -> query_service_pb2.QueryResponse:
        """自然言語クエリを実行する.

        Args:
            request: クエリリクエスト
            context: gRPC コンテキスト

        Returns:
            クエリ結果
        """
        classification = classify(request.text)
        logger.info(
            "クエリ分類: intent=%s, confidence=%.2f, text='%s'",
            classification.intent.value,
            classification.confidence,
            classification.original_text,
        )

        if classification.intent == Intent.UNKNOWN:
            return query_service_pb2.QueryResponse(
                intent=Intent.UNKNOWN.value,
                response_text=generate_error_response("unknown_intent"),
            )

        if classification.intent == Intent.SALES_INQUIRY:
            return self._handle_sales_inquiry(classification.slots)

        if classification.intent == Intent.INVENTORY_INQUIRY:
            return self._handle_inventory_inquiry(classification.slots)

        if classification.intent == Intent.TOP_PRODUCTS:
            return self._handle_top_products(classification.slots)

        if classification.intent == Intent.PRODUCT_REGISTRATION:
            return query_service_pb2.QueryResponse(
                intent=Intent.PRODUCT_REGISTRATION.value,
                response_text="商品登録は音声入力で行ってください。",
            )

        return query_service_pb2.QueryResponse(
            intent=Intent.UNKNOWN.value,
            response_text=generate_error_response("unknown_intent"),
        )

    def LearnAlias(  # noqa: N802
        self,
        request: query_service_pb2.LearnAliasRequest,
        context: grpc.ServicerContext,  # noqa: ARG002
    ) -> query_service_pb2.LearnAliasResponse:
        """表記ゆれを学習する.

        Args:
            request: 学習リクエスト
            context: gRPC コンテキスト

        Returns:
            学習結果
        """
        recognized = request.recognized_text
        correct = request.correct_product_name

        if not recognized or not correct:
            return query_service_pb2.LearnAliasResponse(
                success=False,
                message="recognized_text と correct_product_name は必須です。",
            )

        self._matcher.learn_alias(recognized, correct)

        if self._repository is not None:
            self._repository.save_alias(recognized, correct)

        logger.info("辞書学習: '%s' -> '%s'", recognized, correct)
        return query_service_pb2.LearnAliasResponse(
            success=True,
            message=f"「{recognized}」→「{correct}」を辞書に登録しました。",
        )

    def ExportAliases(  # noqa: N802
        self,
        request: query_service_pb2.ExportAliasesRequest,  # noqa: ARG002
        context: grpc.ServicerContext,  # noqa: ARG002
    ) -> query_service_pb2.ExportAliasesResponse:
        """表記ゆれ辞書をエクスポートする.

        Args:
            request: エクスポートリクエスト
            context: gRPC コンテキスト

        Returns:
            エクスポート結果
        """
        if self._repository is not None:
            json_data = self._repository.export_aliases_json()
        else:
            json_data = self._matcher.export_aliases_json()

        import json  # noqa: PLC0415

        count = len(json.loads(json_data))

        return query_service_pb2.ExportAliasesResponse(
            json_data=json_data,
            count=count,
        )

    def ImportAliases(  # noqa: N802
        self,
        request: query_service_pb2.ImportAliasesRequest,
        context: grpc.ServicerContext,  # noqa: ARG002
    ) -> query_service_pb2.ImportAliasesResponse:
        """表記ゆれ辞書をインポートする.

        Args:
            request: インポートリクエスト
            context: gRPC コンテキスト

        Returns:
            インポート結果
        """
        try:
            imported = self._matcher.import_aliases_json(request.json_data)

            if self._repository is not None:
                self._repository.import_aliases_json(request.json_data)

            return query_service_pb2.ImportAliasesResponse(
                imported_count=imported,
                success=True,
                message=f"{imported}件のエイリアスをインポートしました。",
            )
        except Exception as e:
            logger.exception("辞書インポートエラー")
            return query_service_pb2.ImportAliasesResponse(
                imported_count=0,
                success=False,
                message=f"インポートに失敗しました: {e}",
            )

    def _handle_sales_inquiry(
        self,
        slots: tuple[object, ...],
    ) -> query_service_pb2.QueryResponse:
        """売上照会を処理する.

        Args:
            slots: 抽出されたスロット

        Returns:
            クエリ結果
        """
        from pos_voice_concierge.intent_classifier import SlotValue  # noqa: PLC0415
        from pos_voice_concierge.response_generator import SalesData  # noqa: PLC0415

        period_key = "today"
        product_name: str | None = None
        for slot in slots:
            if isinstance(slot, SlotValue) and slot.name == "date_range":
                period_key = slot.value
            elif isinstance(slot, SlotValue) and slot.name == "product_name":
                product_name = slot.value

        period_label = _PERIOD_MAP.get(period_key, "今日")
        from_dt, to_dt = _resolve_period(period_key)

        total_amount = 0
        item_count = 0

        if self._repository is not None:
            try:
                if product_name is not None:
                    result = self._repository.product_sales_between(
                        product_name, from_dt, to_dt,
                    )
                else:
                    result = self._repository.total_sales_between(from_dt, to_dt)
                total_amount = result.total_amount
                item_count = result.item_count
            except Exception:
                logger.exception("売上データ取得エラー")

        sales_data = SalesData(
            total_amount=total_amount,
            period_label=period_label,
            item_count=item_count,
        )

        response_text = generate_sales_response(sales_data)

        return query_service_pb2.QueryResponse(
            intent=Intent.SALES_INQUIRY.value,
            response_text=response_text,
            data=query_service_pb2.QueryData(
                sales=query_service_pb2.SalesResult(
                    total_amount=sales_data.total_amount,
                    period_label=sales_data.period_label,
                    item_count=sales_data.item_count,
                ),
            ),
        )

    def _handle_inventory_inquiry(
        self,
        slots: tuple[object, ...],
    ) -> query_service_pb2.QueryResponse:
        """在庫照会を処理する.

        Args:
            slots: 抽出されたスロット

        Returns:
            クエリ結果
        """
        from pos_voice_concierge.intent_classifier import SlotValue  # noqa: PLC0415
        from pos_voice_concierge.response_generator import InventoryData  # noqa: PLC0415

        product_name = ""
        for slot in slots:
            if isinstance(slot, SlotValue) and slot.name == "product_name":
                product_name = slot.value

        if not product_name:
            return query_service_pb2.QueryResponse(
                intent=Intent.INVENTORY_INQUIRY.value,
                response_text=generate_error_response("product_not_found"),
            )

        stock_quantity = 0
        if self._repository is not None:
            try:
                inv_result = self._repository.find_stock_by_product_name(product_name)
                if inv_result is not None:
                    stock_quantity = inv_result.stock_quantity
            except Exception:
                logger.exception("在庫データ取得エラー")

        inventory_data = InventoryData(
            product_name=product_name,
            stock_quantity=stock_quantity,
        )

        response_text = generate_inventory_response(inventory_data)

        return query_service_pb2.QueryResponse(
            intent=Intent.INVENTORY_INQUIRY.value,
            response_text=response_text,
            data=query_service_pb2.QueryData(
                inventory=query_service_pb2.InventoryResult(
                    product_name=inventory_data.product_name,
                    stock_quantity=inventory_data.stock_quantity,
                ),
            ),
        )

    def _handle_top_products(
        self,
        slots: tuple[object, ...],
    ) -> query_service_pb2.QueryResponse:
        """売上トップN商品を処理する.

        Args:
            slots: 抽出されたスロット

        Returns:
            クエリ結果
        """
        from pos_voice_concierge.intent_classifier import SlotValue  # noqa: PLC0415
        from pos_voice_concierge.response_generator import (  # noqa: PLC0415
            TopProductEntry as ResponseTopProductEntry,
        )

        period_key = "today"
        requested_n = 5

        for slot in slots:
            if not isinstance(slot, SlotValue):
                continue
            if slot.name == "date_range":
                period_key = slot.value
            elif slot.name == "top_n":
                requested_n = int(slot.value)

        period_label = _PERIOD_MAP.get(period_key, "今日")
        from_dt, to_dt = _resolve_period(period_key)

        entries: list[ResponseTopProductEntry] = []
        if self._repository is not None:
            try:
                db_entries = self._repository.top_products_between(
                    from_dt, to_dt, requested_n,
                )
                entries = [
                    ResponseTopProductEntry(
                        rank=e.rank,
                        product_name=e.product_name,
                        total_amount=e.total_amount,
                        quantity_sold=e.quantity_sold,
                    )
                    for e in db_entries
                ]
            except Exception:
                logger.exception("トップ商品データ取得エラー")

        response_text = generate_top_products_response(entries, period_label)

        proto_entries = [
            query_service_pb2.TopProductEntry(
                rank=e.rank,
                product_name=e.product_name,
                total_amount=e.total_amount,
                quantity_sold=e.quantity_sold,
            )
            for e in entries
        ]

        return query_service_pb2.QueryResponse(
            intent=Intent.TOP_PRODUCTS.value,
            response_text=response_text,
            data=query_service_pb2.QueryData(
                top_products=query_service_pb2.TopProductsResult(
                    entries=proto_entries,
                    period_label=period_label,
                ),
            ),
        )
