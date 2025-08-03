"""
Implement both multiple dispatch and "predicative" dispatch.

See README.md for an historical discussion of this topic.
"""

from __future__ import annotations
from collections import defaultdict, namedtuple
from types import UnionType
from typing import Any, Callable

namespace_detritus = [
    "_ipython_canary_method_should_not_exist_",
    "_ipython_display_",
    "_repr_mimebundle_",
]

AnnotationInfo = namedtuple("AnnotationInfo", "type predicate")


def annotation_info(fn: Callable) -> dict[str, AnnotationInfo]:
    """
    Extract args, types, and predicates

    The complication is that each annotation can have any of several formats:

      - <nothing>               # No type annotation or predicate
      - int | float             # Bare type annotation
      - int & 3 <= a <= 17      # A type annotation with a predicate
      - a > 42 & a < 500        # Bare predicate (perhaps with several bitwise operators)
      - str | bytes & 2+2==4    # Type annotation and non-contextual predicate
      - 4 > 5                   # Only a non-contextual predicate

      We can assume, however, that anything after an ampersand is a predicate.
    """
    annotations = {}
    for arg in fn.__code__.co_varnames:
        if arg not in fn.__annotations__:
            # No type annotation or predicate
            annotations[arg] = AnnotationInfo(Any, "True")  # No type annotation
            continue
        elif len(parts := fn.__annotations__[arg].split("&", maxsplit=1)) == 2:
            # Both type and predicate (maybe)
            type_, predicate = parts
            try:
                type_ = eval(type_)
                if isinstance(type_, (type, UnionType)):
                    annotations[arg] = AnnotationInfo(type_, predicate.strip())
            except (TypeError, NameError, Exception) as _err:
                # This could be a compound predicate containing an ampersand
                all_parts = fn.__annotations__[arg].strip()
                annotations[arg] = AnnotationInfo(Any, all_parts)
        else:
            try:
                # Is first thing a type annotation?
                # We will usually raise an exception if not a valid type
                type_ = eval(parts[0])
                if isinstance(type_, (type, UnionType)):
                    annotations[arg] = AnnotationInfo(type_, "True")  # No predicate
                else:
                    # This is the odd case of non-contextual predicate (e.g. 2+2==5)
                    boolean_result = str(type_)
                    annotations[arg] = AnnotationInfo(Any, boolean_result)
            except (TypeError, NameError, Exception) as _err:
                # Not a type annotation, so it's a predicate (store as a string)
                annotations[arg] = AnnotationInfo(
                    Any, parts[0].strip()
                )  # No type annotation

    return annotations


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
        funcs = cls.funcs.get(name, [])
        if not funcs:
            raise AttributeError(f"No implementations are bound to {name}")
        return funcs[0]  # TODO: Now just first implementation


def get_dispatcher():
    "Manufacuture as many Dispatcher objects as needed."

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
            return repr(self.__class__)

        def __str__(self):
            return str(self.__class__)

        def __call__(self, fn):
            name = Dispatcher.to_bind or fn.__name__
            Dispatcher.funcs[name].append(fn)
            Dispatcher.to_bind = None  # Clear the binding after using it
            return Dispatcher

    return Dispatcher


# This is a default Dispatcher object, for common scenarios needing just one.
Dispatcher = get_dispatcher()
