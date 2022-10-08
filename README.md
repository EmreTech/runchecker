# runchecker

A dynamic, runtime type checker for Python 3.7+!

## Example

```python
>>> import runchecker
>>> @runchecker.check
... def hey_there(name: str, greeting: str) -> str:
...     return greeting + " " + name + "!"
...
>>> hey_there("John", "Hello")
"Hello John!"
>>> hey_there(487, "Hello")
Traceback (most recent call last):
    ...
runchecker.errors.InvalidParameter: Parameter name with value 487 (type int) is incompatible with str!
```

## What Currently Works

runchecker currently supports the following type hints:

- object
- Any
- None
- collections.abc.Mapping
- collections.abc.Sequence
- tuple
- Union
- Generic
- TypedDict
- Literal
- Annotated

runchecker plans to support the following type hints in the future:

- TypeVar
- Forward References
- and more to come!

## Validating a Custom Generic

If you have a custom Generic class that doesn't follow any of the protocols runchecker currently supports, no problem!

runchecker allows you to make a custom validator for your custom Generic class. Instance checks will already be done for you automatically.

All you have to do is inherit from `runchecker.Validator`, which is a protocol class that defines a dunder function (not method) called `__validate__`.

`__validate__` takes in two parameters: the `type_hint` (typed as `Any`) and the `value` (typed as `Any`). The `type_hint` will be the type hint that called this validator, and the `value` will be the value to validate.

`__validate__` has a return type of anything. All you have to do in your `__validate__` implementation is raise `runchecker.WrongType` if the `value` parameter violates `type_hint`!

## Licensing

runchecker is licensed under the MIT License. Read the LICENSE file for more information.
