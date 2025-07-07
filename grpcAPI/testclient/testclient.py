import atexit
import inspect
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union

from grpcAPI.app import App, ProtoModel, get_label
from grpcAPI.proto_builder import build_protos
from grpcAPI.proto_load import load_proto
from grpcAPI.proto_schema import make_path_content_list
from grpcAPI.service_provider import load_services
from grpcAPI.settings.utils import combine_settings
from grpcAPI.singleton import SingletonMeta
from grpcAPI.testclient import ContextMock
from grpcAPI.types import Context, Stream


def write_protos(protos_dict: Dict[str, Dict[str, str]], tempdir: Path) -> None:

    content_path = make_path_content_list(protos_dict)
    for content, path in content_path:
        file = tempdir / path
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file.absolute(), "w", encoding="utf-8") as f:
            f.write(content)


class ModuleLoader(metaclass=SingletonMeta):
    def __init__(self, app: App, settings: Optional[Dict[str, Any]] = None) -> None:
        self.app = app
        settings = settings or {}

        combine_settings(settings, "compile")

        protos_dict = build_protos(app, settings)
        if protos_dict is None:
            raise Exception("Proto File building error")
        self._tmpdir_obj = tempfile.TemporaryDirectory()
        self.tempdir = Path(self._tmpdir_obj.name)

        protos_path = self.tempdir / "proto"
        protos_path.mkdir(parents=True, exist_ok=True)

        write_protos(protos_dict, protos_path)

        compiled_path = self.tempdir / "compiled"
        compiled_path.mkdir(parents=True, exist_ok=True)
        self.modules = load_proto(protos_path, compiled_path)

        atexit.register(self._cleanup)

    def _cleanup(self) -> None:
        # print("Temp folder clean up")
        self._tmpdir_obj.cleanup()
        # type(self)._instances.pop(type(self), None)


class TestClient:
    def __init__(self, app: App, settings: Optional[Dict[str, Any]] = None) -> None:

        module_loader = ModuleLoader(app, settings)

        services_list = load_services(module_loader.app, module_loader.modules)

        self.services: Dict[Tuple[str, str, str], Any] = {}
        for serv_cls in services_list:
            package, module = serv_cls.label
            self.services[(package, module, serv_cls.__name__)] = serv_cls()

    async def run(
        self, func: Callable[..., Any], request: Any, context: Optional[Context] = None
    ) -> Union[ProtoModel, Stream[ProtoModel]]:

        context = context or ContextMock()

        label = get_label(func)
        if label is None:
            raise Exception(
                f'Function "{func.__name__}" is not linked to a grpcAPI module'
            )
        package, module, service = label
        service = self.services.get((package, module, service), None)
        if service is None:
            raise KeyError(f'No service found: "{package}/{module}/{service}"')

        method = getattr(service, func.__name__)

        response = method(request, context)
        if inspect.isawaitable(response):
            response = await response

        return response
