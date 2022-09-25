from typing import Any

from .utils import _type_repr

__all__ = ("WrongType",)

class WrongType(TypeError):
    """Raised if the value's type is incompatible with the type hint defined."""
    def __init__(self, *, value: Any, type_hint: Any):
        super().__init__(f"Invalid value {_type_repr(value)} (type {_type_repr(type(value))}) for type hint {_type_repr(type_hint)}!")