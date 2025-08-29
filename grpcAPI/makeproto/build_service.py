from dataclasses import dataclass
from typing import Generator, Iterable, Mapping, Set

from typing_extensions import Any, Callable, Dict, List, Optional, Tuple

from grpcAPI.makeproto.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.compiler_passes import (
    CompilationError,
    default_format,
    make_setters,
    make_validators,
    run_compiler_passes,
)
from grpcAPI.makeproto.format_comment import format_comment
from grpcAPI.makeproto.interface import IProtoPackage, IService
from grpcAPI.makeproto.make_service_template import make_service_template
from grpcAPI.makeproto.template import (
    ProtoTemplate,
    ServiceTemplate,
    render_protofile_template,
)
from grpcAPI.makeproto.validators.name import check_valid, check_valid_filenames


def compile_service(
    services: Mapping[str, List[IService]],
    name_normalizer: Callable[[str], str] = lambda x: x,
    format_comment: Callable[[str], str] = default_format,
    custompassmethod: Callable[[Callable[..., Any]], List[str]] = lambda x: [],
    version: int = 3,
) -> Optional[Generator[IProtoPackage, None, None]]:

    validators = make_validators(custompassmethod)
    setters = make_setters(
        name_normalizer=name_normalizer, format_comment=format_comment
    )

    return compile_service_internal(
        services,
        [validators, setters],
        version,
    )


def compile_service_internal(
    services: Dict[str, List[IService]],
    compilerpasses: List[List[CompilerPass]],
    version: int = 3,
) -> Optional[Generator[IProtoPackage, None, None]]:

    all_templates, compiler_execution = prepare_modules(services, version)
    try:
        for compilerpass in compilerpasses:
            run_compiler_passes(compiler_execution, compilerpass)
    except CompilationError as e:
        for ctx in e.contexts:
            if ctx.has_errors():
                ctx.show()
        return None

    def generate_protos() -> Generator[IProtoPackage, None, None]:
        for template in all_templates:
            module_dict = template.to_dict()
            if not module_dict:  # pragma: no cover
                continue
            rendered = render_protofile_template(module_dict)
            yield ProtoPackage(
                template.package, template.module, rendered, template.imports
            )

    return generate_protos()


@dataclass
class ProtoPackage(IProtoPackage):
    package: str
    filename: str
    content: str
    depends: Set[str]

    @property
    def qual_name(self) -> str:  # pragma: no cover
        file_path = f"{self.filename}.proto"
        if self.package:
            pack = self.package.replace(".", "/")
            file_path = f"{pack}/{file_path}"
        return file_path


def prepare_modules(
    services: Dict[str, List[IService]],
    version: int = 3,
) -> Tuple[List[ProtoTemplate], List[Tuple[List[ServiceTemplate], CompilerContext]]]:

    all_templates: List[ProtoTemplate] = []
    compiler_execution: List[Tuple[List[ServiceTemplate], CompilerContext]] = []

    for _, service_list in services.items():
        compiler_ctx = make_compiler_context(service_list, version)
        if compiler_ctx is None:
            continue
        allmodules, ctx = compiler_ctx
        all_templates.extend(allmodules)
        templates = [
            make_service_template(service) for service in service_list if service.active
        ]
        compiler_execution.append((templates, ctx))

    return all_templates, compiler_execution


def extract_modules(
    packlist: List[IService],
) -> Mapping[str, Tuple[Iterable[str], Iterable[str], Iterable[str]]]:

    modules: Dict[str, Tuple[List[str], List[str], List[str]]] = {}
    for service in packlist:
        mod_name = service.module
        mod_opt = [opt.strip() for opt in service.module_level_options]
        mod_com = [serv.strip() for serv in service.module_level_comments]
        mod_imp = [imp.strip() for imp in service.module_level_imports]
        if mod_name not in modules:
            modules[mod_name] = (mod_opt, mod_com, mod_imp)
        else:
            option, comment, imports = modules[mod_name]
            option.extend(mod_opt)
            comment.extend(mod_com)
            imports.extend(mod_imp)
            modules[mod_name] = (
                list(dict.fromkeys(option)),  # Remove duplicates
                list(dict.fromkeys(comment)),
                list(dict.fromkeys(imports)),
            )

    return modules


def make_compiler_context(
    packlist: List[IService],
    version: int = 3,
) -> Optional[Tuple[List[ProtoTemplate], CompilerContext]]:

    if len(packlist) == 0:
        return None

    allmodules: List[ProtoTemplate] = []
    state: Dict[str, ProtoTemplate] = {}
    module_list = extract_modules(packlist)
    package_name = packlist[0].package

    for modulename, (options, comments, imports) in module_list.items():

        formated_comment = format_comment("\n".join(comments))
        module_template = ProtoTemplate(
            comments=formated_comment,
            syntax=version,
            module=modulename,
            package=package_name,
            imports=set(imports),
            services=[],
            options=list(options),
        )
        state[modulename] = module_template
        allmodules.append(module_template)

    ctx = CompilerContext(name=package_name, state=state)

    class PackageBlock:
        def __init__(self, name: str) -> None:
            self.name = f"Package<{name}>"

    report = ctx.get_report(PackageBlock(package_name))
    if package_name:
        check_valid(package_name, report, False)
    check_valid_filenames(module_list, report)

    return allmodules, ctx
