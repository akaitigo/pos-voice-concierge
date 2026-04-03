"""QueryService gRPC サーバー実装.

自然言語クエリの処理、表記ゆれ辞書管理を提供する。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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

        period_label = "今日"
        for slot in slots:
            if isinstance(slot, SlotValue) and slot.name == "date_range":
                period_map = {
                    "today": "今日",
                    "yesterday": "昨日",
                    "this_week": "今週",
                    "last_week": "先週",
                    "this_month": "今月",
                    "last_month": "先月",
                }
                period_label = period_map.get(slot.value, "今日")

        # 売上データの取得（MVPではモックデータ、実際にはDB経由）
        sales_data = SalesData(
            total_amount=0,
            period_label=period_label,
            item_count=0,
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

        inventory_data = InventoryData(
            product_name=product_name,
            stock_quantity=0,
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
        from pos_voice_concierge.response_generator import TopProductEntry  # noqa: PLC0415

        period_label = "今日"
        requested_n = 5

        for slot in slots:
            if not isinstance(slot, SlotValue):
                continue
            if slot.name == "date_range":
                period_map = {
                    "today": "今日",
                    "yesterday": "昨日",
                    "this_week": "今週",
                    "last_week": "先週",
                    "this_month": "今月",
                    "last_month": "先月",
                }
                period_label = period_map.get(slot.value, "今日")
            elif slot.name == "top_n":
                requested_n = int(slot.value)

        # MVPではデータなし（Backend が実際のデータを注入する）
        entries: list[TopProductEntry] = []
        # requested_n は将来 DB クエリの LIMIT に使用される
        entries = entries[:requested_n]

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
