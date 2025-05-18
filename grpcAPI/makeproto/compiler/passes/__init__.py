__all__ = [
    "IndexValidator",
    "NameValidator",
    "NameNormalizer",
    "FieldTypeValidator"
]

from grpcAPI.makeproto.compiler.passes.index import IndexValidator
from grpcAPI.makeproto.compiler.passes.name import NameValidator, NameNormalizer
from grpcAPI.makeproto.compiler.passes.type import FieldTypeValidator

testar type validator com method