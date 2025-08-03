"""
Implement both multiple dispatch and "predicative" dispatch.

See README.md for an historical discussion of this topic.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Callable

namespace_detritus = [
    "_ipython_canary_method_should_not_exist_",
    "_ipython_display_",
    "_repr_mimebundle_",
]


class DispatcherMeta(type):
    def __repr__(cls):
        s = f"{cls.__name__} bound implementations:"
        for key, funcs in cls.funcs.items():  # type: ignore
            for fn in funcs:
                s += f"\n- {key}: {fn.__annotations__}"
                if key != fn.__name__:
                    s += f" (re-bound '{fn.__name__}')"
        return s

    def __str__(cls):
        n_names = sum(1 for f in cls.funcs if f not in namespace_detritus)
        n_impls = sum(len(funcs) for funcs in cls.funcs.values())
        return (
            f"{cls.__name__} with {n_names} function{'s' if n_names > 1 else ''} "
            f"bound to {n_impls} implementation{'s' if n_impls > 1 else ''}"
        )

    def __getattr__(cls, name):
        "Implements multiple and predicative dispatch, if bound name exists."
        try:
            return cls.funcs[name][0]
        except Exception as err:
            raise AttributeError(f"No function bound to {name} ({err})")


class Dispatcher(metaclass=DispatcherMeta):
    funcs = defaultdict(list)
    to_bind = None

    def __new__(cls, fn: Callable | None = None, *, name: str = ""):
        new = super().__new__(cls)

        if fn is not None:
            name = fn.__name__
            new.__class__.funcs[name].append(fn)
        elif not name:
            raise ValueError(
                f"{cls.__name__} must be used as a decorator, "
                "or to call a bound method"
            )
        elif name:
            new.__class__.to_bind = name

        return new

    def __repr__(self):
        cls = self.__class__
        n_names = len(cls.funcs)
        n_impls = sum(len(funcs) for funcs in cls.funcs.values())
        return (
            f"{cls.__name__} with {n_names} function{'s' if n_names > 1 else ''} "
            f"bound to {n_impls} implementation{'s' if n_impls > 1 else ''}"
        )

    def __call__(self, func):
        name = Dispatcher.to_bind or func.__name__
        Dispatcher.funcs[name].append(func)
        Dispatcher.to_bind = None  # Clear the binding after using it
        return Dispatcher


if __name__ == "__main__":
    # def foo(a: int | float & a > 42 & a < 500, b: str, c: str = "blah") -> str:
    #     print(f"foo({a}, {b})")
    #
    # print(foo.__annotations__)
    # for arg, annotation in foo.__annotations__.items():
    #     type_, *predicates = annotation.split("&")
    #     print(f"{arg}: {eval(type_)} (where {predicates})")

    @Dispatcher
    def say(s: str):
        print(f"String: say({s})")

    print(0, say)

    @Dispatcher(name="say")
    def say_two_things(s: str, n: int):
        print(f"String and int: {s}, {n}")

    print(1, Dispatcher)

    @Dispatcher
    def say(n: int & n > 100):
        print(f"Large int: {n}")

    print(2, say)

    print(3, repr(Dispatcher))
    Dispatcher.say("Hello")
