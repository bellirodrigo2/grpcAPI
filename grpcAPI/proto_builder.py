from typing import Any, Dict, Optional

from grpcAPI.app import App
from grpcAPI.makeproto import make_protos
from grpcAPI.proto_inject import define_validation_function, extract_request


def build_protos(
    app: App, settings: Dict[str, Any]
) -> Optional[Dict[str, Dict[str, str]]]:

    validate_function = define_validation_function(app.casting_dict.keys())
    packs = app.packages
    return make_protos(packs, settings, validate_function, extract_request)
