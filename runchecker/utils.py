import types
import sys

__all__ = ("_type_repr",)

if sys.version_info >= (3, 9):
    # Taken from https://github.com/python/cpython/blob/3.9/Lib/typing.py#L170-L188
    def _type_repr(obj):
        if isinstance(obj, types.GenericAlias):
            return repr(obj)
        if isinstance(obj, type):
            if obj.__module__ == 'builtins':
                return obj.__qualname__
            return f'{obj.__module__}.{obj.__qualname__}'
        if obj is ...:
            return('...')
        if isinstance(obj, types.FunctionType):
            return obj.__name__
        return repr(obj)
else:
    # Taken from https://github.com/python/cpython/blob/3.7/Lib/typing.py#L146-L162
    def _type_repr(obj):
        if isinstance(obj, type):
            if obj.__module__ == 'builtins':
                return obj.__qualname__
            return f'{obj.__module__}.{obj.__qualname__}'
        if obj is ...:
            return('...')
        if isinstance(obj, types.FunctionType):
            return obj.__name__
        return repr(obj)
