from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class QueryRequest(_message.Message):
    __slots__ = ("text",)
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class QueryResponse(_message.Message):
    __slots__ = ("intent", "response_text", "data")
    INTENT_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_TEXT_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    intent: str
    response_text: str
    data: QueryData
    def __init__(
        self,
        intent: _Optional[str] = ...,
        response_text: _Optional[str] = ...,
        data: _Optional[_Union[QueryData, _Mapping]] = ...,
    ) -> None: ...

class QueryData(_message.Message):
    __slots__ = ("sales", "inventory", "top_products")
    SALES_FIELD_NUMBER: _ClassVar[int]
    INVENTORY_FIELD_NUMBER: _ClassVar[int]
    TOP_PRODUCTS_FIELD_NUMBER: _ClassVar[int]
    sales: SalesResult
    inventory: InventoryResult
    top_products: TopProductsResult
    def __init__(
        self,
        sales: _Optional[_Union[SalesResult, _Mapping]] = ...,
        inventory: _Optional[_Union[InventoryResult, _Mapping]] = ...,
        top_products: _Optional[_Union[TopProductsResult, _Mapping]] = ...,
    ) -> None: ...

class SalesResult(_message.Message):
    __slots__ = ("total_amount", "period_label", "item_count")
    TOTAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    PERIOD_LABEL_FIELD_NUMBER: _ClassVar[int]
    ITEM_COUNT_FIELD_NUMBER: _ClassVar[int]
    total_amount: int
    period_label: str
    item_count: int
    def __init__(
        self, total_amount: _Optional[int] = ..., period_label: _Optional[str] = ..., item_count: _Optional[int] = ...
    ) -> None: ...

class InventoryResult(_message.Message):
    __slots__ = ("product_name", "stock_quantity")
    PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    STOCK_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    product_name: str
    stock_quantity: int
    def __init__(self, product_name: _Optional[str] = ..., stock_quantity: _Optional[int] = ...) -> None: ...

class TopProductsResult(_message.Message):
    __slots__ = ("entries", "period_label")
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    PERIOD_LABEL_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[TopProductEntry]
    period_label: str
    def __init__(
        self, entries: _Optional[_Iterable[_Union[TopProductEntry, _Mapping]]] = ..., period_label: _Optional[str] = ...
    ) -> None: ...

class TopProductEntry(_message.Message):
    __slots__ = ("rank", "product_name", "total_amount", "quantity_sold")
    RANK_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    TOTAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_SOLD_FIELD_NUMBER: _ClassVar[int]
    rank: int
    product_name: str
    total_amount: int
    quantity_sold: int
    def __init__(
        self,
        rank: _Optional[int] = ...,
        product_name: _Optional[str] = ...,
        total_amount: _Optional[int] = ...,
        quantity_sold: _Optional[int] = ...,
    ) -> None: ...

class ExportAliasesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExportAliasesResponse(_message.Message):
    __slots__ = ("json_data", "count")
    JSON_DATA_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    json_data: str
    count: int
    def __init__(self, json_data: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class ImportAliasesRequest(_message.Message):
    __slots__ = ("json_data",)
    JSON_DATA_FIELD_NUMBER: _ClassVar[int]
    json_data: str
    def __init__(self, json_data: _Optional[str] = ...) -> None: ...

class ImportAliasesResponse(_message.Message):
    __slots__ = ("imported_count", "success", "message")
    IMPORTED_COUNT_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    imported_count: int
    success: bool
    message: str
    def __init__(
        self, imported_count: _Optional[int] = ..., success: bool = ..., message: _Optional[str] = ...
    ) -> None: ...

class LearnAliasRequest(_message.Message):
    __slots__ = ("recognized_text", "correct_product_name")
    RECOGNIZED_TEXT_FIELD_NUMBER: _ClassVar[int]
    CORRECT_PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    recognized_text: str
    correct_product_name: str
    def __init__(self, recognized_text: _Optional[str] = ..., correct_product_name: _Optional[str] = ...) -> None: ...

class LearnAliasResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
