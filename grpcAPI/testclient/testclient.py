import atexit
import inspect
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union

from grpcAPI.app import App, ProtoModel
from grpcAPI.commands.compile import build_protos
from grpcAPI.commands.run import load_services
from grpcAPI.commands.utils import combine_settings
from grpcAPI.proto_load import load_proto
from grpcAPI.singleton import SingletonMeta
from grpcAPI.testclient.contextmock import ContextMock
from grpcAPI.types import Context
from grpcAPI.types.method import Stream


def write_protos(protos_dict: Dict[str, Dict[str, str]], tempdir: Path) -> None:
    for package, modules_dict in protos_dict.items():
        package_path = tempdir / package
        package_path.mkdir(parents=True, exist_ok=True)
        for module, proto_str in modules_dict.items():
            file = package_path / f"{module}.proto"
            with open(file.absolute(), "w", encoding="utf-8") as f:
                f.write(proto_str)


class TestClient(metaclass=SingletonMeta):
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
        services_list = load_services(self.app, self.modules)

        self.services: Dict[Tuple[str, str, str], Any] = {}
        for serv_cls in services_list:
            package, module = serv_cls.label
            self.services[(package, module, serv_cls.__name__)] = serv_cls()

        atexit.register(self._cleanup)

    async def run(
        self, func: Callable[..., Any], request: Any, context: Optional[Context] = None
    ) -> Union[ProtoModel, Stream[ProtoModel]]:

        context = context or ContextMock()

        label = getattr(func, "__grpcAPI_label__", None)
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

    def _cleanup(self) -> None:
        # print("Temp folder clean up")
        self._tmpdir_obj.cleanup()
        # type(self)._instances.pop(type(self), None)
