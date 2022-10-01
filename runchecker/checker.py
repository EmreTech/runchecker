import types
import functools
from typing import Any, Callable, Dict
import inspect

from runchecker.errors import InvalidParameter, WrongType

from .validators import validate

__all__ = ("check",)

def check(func: types.FunctionType) -> Callable[..., Any]:
    assert isinstance(func, types.FunctionType), f"obj parameter must be a function!"

    # functions with the @no_type_check decorator should not be using this
    # decorator anyways
    if getattr(func, "__no_type_check__", False):
        return func

    func_sig = inspect.signature(func)
    type_hints: Dict[str, Any] = {}
    for param in func_sig.parameters.values():
        anno = param.annotation
        if anno is param.empty:
            anno = Any

        type_hints[param.name] = anno

        if param.default is not param.empty:
            validate(anno, param.default, param.name)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        binded_args = func_sig.bind(*args, **kwargs)
        for arg_name, arg in binded_args.arguments.items():
            type_anno = type_hints[arg_name]
            param = func_sig.parameters[arg_name]

            if param.kind == param.VAR_POSITIONAL:
                for value in arg:
                    validate(type_anno, value, param.name)
            elif param.kind == param.VAR_KEYWORD:
                for _, value in arg.items():
                    validate(type_anno, value, param.name)
            else:
                validate(type_anno, arg, param.name)

        result = func(*binded_args.args, **binded_args.kwargs)

        return_type = func_sig.return_annotation
        if return_type is not func_sig.empty:
            try:
                validate(return_type, result)
            except InvalidParameter:
                raise WrongType(value=result, type_hint=return_type)

        return result

    return wrapper
