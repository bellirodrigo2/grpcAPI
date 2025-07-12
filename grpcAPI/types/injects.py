from typing_extensions import Any, Optional, Type

from grpcAPI.config import DEPENDS_TYPE, MODELFIELDINJECT_TYPE
from grpcAPI.types import BaseContext, Message


class Depends(DEPENDS_TYPE):
    pass


class FromContext(MODELFIELDINJECT_TYPE):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=BaseContext, field=field, **meta)


class FromRequest(MODELFIELDINJECT_TYPE):
    def __init__(self, model: Type[Message], field: Optional[str] = None, **meta: Any):
        super().__init__(model=model, field=field, **meta)
