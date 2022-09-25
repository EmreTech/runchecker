from typing import Any, Protocol, runtime_checkable

__all__ = ("Validator",)

@runtime_checkable
class Validator(Protocol):
    """A Validator protocol class. Expected to be used on classes that are Generic."""

    @staticmethod
    def __validate__(type_hint: Any, value: Any) -> Any:
        ...