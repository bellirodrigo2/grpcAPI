import inspect
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from grpcAPI.ctxinject.model import ArgsInjectable, CallableInjectable, ModelFieldInject
from grpcAPI.typemapping import VarTypeInfo, get_func_args


class UnresolvedInjectableError(Exception):
    """Raised when a dependency cannot be resolved in the injection context."""

    ...


def resolve_by_name(context: Mapping[Union[str, type], Any], arg: str) -> Any:
    return context[arg]


def resolve_from_model(
    context: Mapping[Union[str, type], Any], model: type[Any], field: str
) -> Any:
    method = getattr(context[model], field)
    return method() if callable(method) else method


def resolve_by_type(context: Mapping[Union[str, type], Any], bt: type[Any]) -> Any:
    return context[bt]


def resolve_by_default(context: Mapping[Union[str, type], Any], default_: Any) -> Any:
    return default_


def wrap_validate(
    context: Mapping[Union[str, type], Any],
    func: Callable[..., Any],
    instance: ArgsInjectable,
    bt: type[Any],
    name: str,
) -> Any:

    value = func(context)
    validated = instance.validate(value, bt)
    if validated is None:
        raise ValueError(f"Validation for {name} returned None")
    return validated


def map_ctx(
    args: Iterable[VarTypeInfo],
    context: Mapping[Union[str, type], Any],
    allow_incomplete: bool,
    validate: bool = True,
) -> Mapping[str, Any]:
    ctx: dict[str, Any] = {}

    for arg in args:
        instance = arg.getinstance(ArgsInjectable)
        default_ = instance.default if instance else None
        bt = arg.basetype
        value = None

        # by name
        if arg.name in context:
            value = partial(resolve_by_name, arg=arg.name)
        # by model field/method
        elif instance is not None:
            if isinstance(instance, ModelFieldInject):
                tgtmodel = instance.model
                tgt_field = instance.field or arg.name
                if tgtmodel in context:
                    value = partial(resolve_from_model, model=tgtmodel, field=tgt_field)
        # by type
        if value is None and bt is not None and bt in context:
            value = partial(resolve_by_type, bt=bt)
        # by default
        if value is None and default_ is not None and default_ is not Ellipsis:
            value = partial(resolve_by_default, default_=default_)

        if value is None and not allow_incomplete:
            raise UnresolvedInjectableError(
                f"Argument '{arg.name}' is incomplete or missing a valid injectable context."
            )
        if value is not None:
            if validate and instance is not None and arg.basetype is not None:
                value = partial(
                    wrap_validate,
                    func=value,
                    instance=instance,
                    bt=arg.basetype,
                    name=arg.name,
                )
            ctx[arg.name] = value
    return ctx


def resolve_mapped_ctx(
    input_ctx: Mapping[Union[str, type], Any], mapped_ctx: Mapping[str, Any]
) -> Dict[Any, Any]:
    results = {}

    for k, v in mapped_ctx.items():
        results[k] = v(input_ctx)
    return results


def inject_args(
    func: Callable[..., Any],
    context: Mapping[Union[str, type], Any],
    allow_incomplete: bool = True,
    validate: bool = True,
    transform_func_args: Optional[
        Callable[
            [Sequence[VarTypeInfo], Mapping[Union[str, type], Any]],
            Sequence[VarTypeInfo],
        ]
    ] = None,
) -> partial[Any]:
    funcargs = get_func_args(func)
    if transform_func_args is not None:
        funcargs = transform_func_args(funcargs, context)
    mapped_ctx = map_ctx(funcargs, context, allow_incomplete, validate)
    ctx = resolve_mapped_ctx(context, mapped_ctx)

    return partial(func, **ctx)


def map_depends(func: Callable[..., Any]) -> List[tuple[str, Any]]:
    argsfunc = get_func_args(func)
    deps: List[tuple[str, Any]] = [
        (arg.name, arg.getinstance(CallableInjectable).default)  # type: ignore
        for arg in argsfunc
        if arg.hasinstance(CallableInjectable)
    ]
    return deps


async def inject_dependencies(
    func: Callable[..., Any],
    context: Mapping[Union[str, type], Any],
    overrides: Mapping[Callable[..., Any], Callable[..., Any]],
) -> Callable[..., Any]:
    depfunc = overrides.get(func, func)
    deps = map_depends(depfunc)
    if not deps:
        return depfunc
    dep_ctx: dict[Union[str, type], Any] = {}
    for name, dep in deps:
        dep_ctx[name] = await resolve(dep, context, overrides)
    resolved = inject_args(depfunc, dep_ctx, allow_incomplete=True)
    return resolved


async def resolve(
    func: Callable[..., Any],
    context: Mapping[Union[str, type], Any],
    overrides: Mapping[Callable[..., Any], Callable[..., Any]],
    validate: bool = True,
) -> Any:
    depfunc = overrides.get(func, func)
    injdepfunc = inject_args(depfunc, context, allow_incomplete=True, validate=validate)
    resolved_func = await inject_dependencies(injdepfunc, context, overrides)
    args = get_func_args(resolved_func)
    if args:
        raise UnresolvedInjectableError(
            f"Arguments unresolved in '{func.__name__}': {[a.name for a in args]}"
        )

    async def _run(partial_fn: Callable[..., Any]) -> Any:
        result = partial_fn()
        return await result if inspect.isawaitable(result) else result

    return await _run(resolved_func)
