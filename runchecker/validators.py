import functools
import itertools
import inspect
import sys
from collections import abc
from collections import OrderedDict
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Mapping,
    Optional,
    Sequence,
    Tuple, 
    Type,
    TypeVar,
    Union,
    cast,
)

from .errors import WrongType, InvalidParameter
from .protocols import Validator

from typing_extensions import (
    Annotated,
    Literal,
    get_args,
    get_origin,
    TypedDict,
    is_typeddict,
)

if sys.version_info >= (3, 10):
    from types import UnionType

    union_types = (Union, UnionType)
else:
    union_types = (Union,)

OT = TypeVar("OT")

__all__ = ("validate",)

def make_validator(func: Callable[[Any, Any], Optional[Any]]):
    @functools.wraps(func)
    def wrapper(type_hint: Any, value: Any, parameter: Optional[str]) -> None:
        try:
            res = func(type_hint, value)
        except (WrongType, TypeError):
            res = None

        if not res:
            if parameter is not None:
                raise InvalidParameter(parameter=parameter, value=value, type_hint=type_hint)
            else:
                raise WrongType(value=value, type_hint=type_hint)
    return wrapper

@make_validator
def validate_any(type_hint: Any, value: Any) -> Any:
    return value

@make_validator
def validate_object(type_hint: Type[OT], value: Any) -> Optional[OT]:
    if isinstance(value, type_hint):
        return value

# we can't return None here because it's confusing to our decorator
@make_validator
def validate_none(type_hint: Any, value: Any) -> Optional[bool]:
    if value is None:
        return True

@make_validator
def validate_union(type_hint: Any, value: Any) -> Optional[Any]:
    for t in get_args(type_hint):
        try:
            validate(t, value)
        except WrongType:
            continue
        else:
            return value

@make_validator
def validate_mapping_alias(type_hint: Any, value: Any) -> Optional[Mapping[Any, Any]]:
    key_type, value_type = get_args(type_hint)
    value_dict = cast(abc.Mapping, value)

    for k, v in value_dict.items():
        validate(key_type, k)
        validate(value_type, v)

    return value_dict

_no_repeating_tuple_arg = object()

def _get_repeating_tuple_arg(alias: Any) -> Any:
    args = get_args(alias)

    if len(args) == 1 and args[0] is ...:
        raise TypeError(f"Invalid tuple alias {repr(alias)}!")

    if args[-1] is ...:
        return args[-2]
    
    return _no_repeating_tuple_arg

@make_validator
def validate_tuple_alias(type_hint: Any, value: Any) -> Optional[Tuple[Any, ...]]:
    tuple_args = get_args(type_hint)
    repeating_arg = _get_repeating_tuple_arg(type_hint)
    tuple_args = tuple([v for v in tuple_args if v is not ...])
    value_tuple = cast(tuple, value)

    if (repeating_arg is _no_repeating_tuple_arg and len(value_tuple) == len(tuple_args)) or repeating_arg is not _no_repeating_tuple_arg:
        for v_type, v_value in itertools.zip_longest(tuple_args, value_tuple, fillvalue=repeating_arg):
            validate(v_type, v_value)
        return value_tuple

@make_validator
def validate_sequence_alias(type_hint: Any, value: Any) -> Optional[Sequence[Any]]:
    value_arg = get_args(type_hint)
    value_sequence = cast(abc.Sequence, value)

    for v in value_sequence:
        validate(value_arg, v)

    return value_sequence

@make_validator
def validate_callable(type_hint: Any, value: Any) -> Optional[Callable[..., Any]]:
    if callable(value):
        callable_args, callable_return = get_args(type_hint)
        value_signature = inspect.signature(value)

        assert isinstance(callable_args, abc.Sequence) or callable_args is ..., f"Invalid callable alias {repr(type_hint)}!"

        if callable_args is ... and value_signature.return_annotation is callable_return:
            return cast(abc.Callable, value)

        elif callable_args is not ... and len(value_signature.parameters) == len(callable_args):
            value_signature_param_annos = [p.annotation for p in value_signature.parameters.values()]
            if value_signature_param_annos == callable_args and value_signature.return_annotation is callable_return:
                return cast(abc.Callable, value)

@make_validator
def validate_generic(type_hint: Any, value: Any) -> Optional[Any]:
    origin = get_origin(type_hint)
    if origin and isinstance(value, origin):
        if issubclass(origin, Validator):
            try:
                origin.__validate__(type_hint, value)
            except:
                raise
            else:
                return value
        else:
            return value

@make_validator
def validate_literal(type_hint: Any, value: Any) -> Optional[Any]:
    literal_args = get_args(type_hint)

    if value in literal_args:
        return value

@make_validator
def validate_typed_dict(type_hint: Any, value: Any) -> Optional[Dict[str, Any]]:
    typed_dict = cast(TypedDict, type_hint)
    value_dict: Dict[str, Any] = cast(dict, value)

    for k in value_dict.keys():
        validate(str, k)

    if sys.version_info >= (3, 9):
        if not typed_dict.__optional_keys__ and value_dict.keys() == typed_dict.__annotations__.keys():
            for k, v in typed_dict.__annotations__.items():
                v_from_dict = value_dict[k]
                validate(v, v_from_dict)

            return value_dict
        elif typed_dict.__optional_keys__:
            for k, v in typed_dict.__annotations__.items():
                try:
                    v_from_dict = value_dict[k]
                except KeyError:
                    if k in typed_dict.__optional_keys__:
                        continue
                    else:
                        raise TypeError(f"This dict provided does not match the Typed Dict!")

                validate(v, v_from_dict)

            return value_dict
    else:
        if typed_dict.__total__ and value_dict.keys() == typed_dict.__annotations__.keys():
            for k, v in typed_dict.__annotations__:
                v_from_dict = value_dict[k]
                validate(v, v_from_dict)

            return value_dict
        elif not typed_dict.__total__:
            for k, v in typed_dict.__annotations__:
                try:
                    v_from_dict = value_dict[k]
                except KeyError:
                    pass

                validate(v, v_from_dict)

            return value_dict

@make_validator
def validate_annotated(type_hint: Any, value: Any) -> Optional[Any]:
    annotated_type = get_args(type_hint)[0]

    try:
        validate(annotated_type, value)
    except:
        raise
    else:
        return value

def make_subclass_condition(type_to_check: Union[type, Tuple[type, ...]]) -> Callable[[Any], bool]:
    def wrapper(t: Any):
        if (origin := get_origin(t)) is not None and isinstance(origin, type):
            return issubclass(origin, type_to_check)
        return False
    return wrapper

all_validators: Mapping[Callable[[Any], bool], Callable[[Any, Any, Optional[str]], None]] = OrderedDict(
    {
        (lambda t: is_typeddict(t)): validate_typed_dict,
        make_subclass_condition(abc.Mapping): validate_mapping_alias,
        make_subclass_condition(tuple): validate_tuple_alias,
        make_subclass_condition(abc.Sequence): validate_sequence_alias,
        (lambda t: get_origin(t) is Annotated): validate_annotated,
        (lambda t: get_origin(t) is Literal): validate_literal,
        (lambda t: get_origin(t) in union_types): validate_union,
        make_subclass_condition(Generic): validate_generic,
        (lambda t: t is Any): validate_any,
        (lambda t: t is None): validate_none,
        (lambda _: True): validate_object,
    }
)

def validate(type_hint: Any, value: Any, parameter: Optional[str] = None):
    for condition, validator in all_validators.items():
        if condition(type_hint):
            return validator(type_hint, value, parameter)
