from typing import Any

from .utils import _type_repr

__all__ = ("WrongType", "InvalidParameter")

class WrongType(TypeError):
    """Raised if the value's type is incompatible with the type hint defined."""
    def __init__(self, *, value: Any, type_hint: Any):
        super().__init__(f"Invalid value {_type_repr(value)} (type {_type_repr(type(value))}) for type hint {_type_repr(type_hint)}!")

class InvalidParameter(WrongType):
    """Raised if the parameter in a function is incompatible with the type hint defined."""
    def __init__(self, *, parameter: str, value: Any, type_hint: Any):
        super(TypeError, self).__init__(f"Parameter {parameter} with value {_type_repr(value)} (type {_type_repr(type(value))}) is incompatible with {_type_repr(type_hint)}!")
