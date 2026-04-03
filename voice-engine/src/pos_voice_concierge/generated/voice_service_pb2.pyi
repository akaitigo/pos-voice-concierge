from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class AudioChunk(_message.Message):
    __slots__ = ("data", "format", "sample_rate")
    DATA_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    format: str
    sample_rate: int
    def __init__(self, data: bytes | None = ..., format: str | None = ..., sample_rate: int | None = ...) -> None: ...

class AudioData(_message.Message):
    __slots__ = ("data", "format", "sample_rate")
    DATA_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    format: str
    sample_rate: int
    def __init__(self, data: bytes | None = ..., format: str | None = ..., sample_rate: int | None = ...) -> None: ...

class RecognitionResult(_message.Message):
    __slots__ = ("confidence", "is_final", "matches", "transcript")
    TRANSCRIPT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    transcript: str
    confidence: float
    matches: _containers.RepeatedCompositeFieldContainer[ProductMatch]
    is_final: bool
    def __init__(
        self,
        transcript: str | None = ...,
        confidence: float | None = ...,
        matches: _Iterable[ProductMatch | _Mapping] | None = ...,
        is_final: bool = ...,
    ) -> None: ...

class ProductMatch(_message.Message):
    __slots__ = ("product_id", "product_name", "quantity", "score")
    PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    product_id: str
    product_name: str
    score: float
    quantity: int
    def __init__(
        self,
        product_id: str | None = ...,
        product_name: str | None = ...,
        score: float | None = ...,
        quantity: int | None = ...,
    ) -> None: ...
