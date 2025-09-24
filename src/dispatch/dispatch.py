"""
Implement both multiple dispatch and "predicative" dispatch.

See README.md for an historical discussion of this topic.
"""

from __future__ import annotations
from collections import defaultdict, namedtuple
from sys import maxsize
from types import UnionType
from typing import Any, Callable, Collection

namespace_detritus = [
    "_ipython_canary_method_should_not_exist_",
    "_ipython_display_",
    "_repr_mimebundle_",
]

AnnotationInfo = namedtuple("AnnotationInfo", "type predicate")
FunctionInfo = namedtuple("FunctionInfo", "fn annotation_info")


def function_info(
    fn: Callable, annotation_info: dict[str, AnnotationInfo]
) -> FunctionInfo:
    "Cleanup function object and aggregate with extracted annotation info."
    # TODO: Massage function object's __annotations__ attribute
    return FunctionInfo(fn, annotation_info)


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
    _locals = {}
    # In "normal operation" a Dispatcher will bind `extra_types` to each
    # function (often simply as an empty list). In unit tests or special
    # uses, this might be called with an unadorned function.
    if hasattr(fn, "extra_types"):
        for extra_type in fn.extra_types:  # type: ignore
            _locals[extra_type.__name__] = extra_type

    # Locals defined in the function scope are in `co_varnames`, but they come
    # _after_ the formal arguments whose count is `co_argcount`.
    for arg in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
        if arg not in fn.__annotations__:
            # No type annotation or predicate
            annotations[arg] = AnnotationInfo(Any, "True")  # No type annotation
            continue
        elif len(parts := fn.__annotations__[arg].split("&", maxsplit=1)) == 2:
            # Both type and predicate (maybe)
            type_, predicate = parts
            try:
                type_ = eval(type_, locals=_locals)  # type: ignore
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
                type_ = eval(parts[0], locals=_locals)  # type: ignore
                if isinstance(type_, (type, UnionType)):
                    annotations[arg] = AnnotationInfo(type_, "True")  # No predicate
                else:
                    # This is the odd case of non-contextual predicate (e.g. 2+2==5)
                    boolean_result = str(type_)
                    annotations[arg] = AnnotationInfo(Any, boolean_result)
            except (TypeError, NameError, Exception) as _err:
                # Not a type annotation, so it's a predicate (store as a string)
                predicate = parts[0].strip()
                annotations[arg] = AnnotationInfo(Any, predicate)

    return annotations


# =============================================================================
# Define at least one "MRO" resolver.
# =============================================================================
def weighted_resolver(
    implementations: list[FunctionInfo],
    *args,
    **kws,
) -> Callable:
    """
    Select an implementation by weighting satisfiable types and predicates.

    If any type or predicate is directly violated, exclude that implementation.
    If no matching implementation is found, raise an exception.

    Prior to PEP 484 and numerous compound types (Union[] specifically), it
    was possible to rank matches. That is no longer coherent.  For example:

      >>> class SpecialInt(int):
      ...     pass
      ...
      >>> n = SpecialInt(13)
      >>> type(n).mro()
      [<class '__main__.SpecialInt'>, <class 'int'>, <class 'object'>]

    In some sense, `n` is "most like" a SpecialInt, a bit less like an int,
    and just nominally like an object.  In this simple case, we can rank or
    weight such distances in evaluating several candidate implementations.

      >>> def add(a: int, b: int | float | complex):
      ...     return a + b
      ...
      >>> add(SpecialInt(13), SpecialInt(12))
      25

    We can sensibly measure the "fit" of the match of the first argument, but
    we cannot do so for the second argument.  It's simply a match or non-match.
    We weight types by the following rules:

      * If a type is incompatible with an argument, we subtract -sys.maxsize.
      * If a type is compatible with typing.Any, we add +5 to the score.
      * If a type is compatible with a UnionType, we add +10 to the score.
      * If a type is compatible with a simple type, we add +20 to the score.
      * If a type is compatible with a simple type, but farther removed in its
        MRO, subtract -1 for each step in the MRO.

    If two signatures match on types (or are equally weighted, in any case),
    then the predicates are weighted as follows:

      * If both predicates are satisfied, the first implementation is chosen.
      * If only one predicate is satisfied, that implementation is chosen.
      * If one predicate is absent, the more specific implementation is chosen.
    """
    _, _ = args, kws  # Quiet the over-eager linter

    def best_implementation(*args, **kws):
        best_score = 0
        implementation = None

        for imp in implementations:
            # Accumulate local vars as args are passed in, and extra_types if any
            _locals = {}
            for extra_type in imp.fn.extra_types:
                _locals[extra_type.__name__] = extra_type

            # More arguments is "better" than fewer arguments
            score = len(args)

            # An implementation with too few arguments is incompatible
            max_args = imp.fn.__code__.co_argcount 
            if len(args) > max_args:
                score -= maxsize
                continue

            # First add weights based on positional arguments
            for arg, info in zip(
                args,
                imp.annotation_info.items(),
            ):
                varname, (type_, predicate) = info
                _locals[varname] = arg

                # Based on type information
                if type_ == Any:
                    score += 5  # compatible with typing.Any
                elif not isinstance(arg, type_):
                    score -= maxsize  # incompatible type
                elif isinstance(type_, UnionType):
                    score += 10  # compatible with UnionType
                else:
                    score += 20  # compatible with a simple type
                    # Subtract distance in MRO
                    offset = type(arg).__mro__.index(type_)
                    mro_bonus = 10 - offset
                    score += mro_bonus

                # Based on predicates (the `True` predicate doesn't exclude
                # the implementation, but neither does it improve its score)
                if predicate == "True":
                    pass
                try:
                    result = eval(predicate, locals=_locals)  # type: ignore
                except Exception:
                    # If a predicate cannot be evaluated, stipulate False.
                    # E.g. Complex arg with predicate of inequality with an int
                    result = False  # Assume predicate is False
                if not result:
                    score -= maxsize  # incompatible predicate
                elif predicate != "True":
                    score += 3  # non-trivial predicate satisfied

            # Add weights based on keywords (similar to positional args)
            for varname, arg in kws.items():
                # An implementation might not have a given keyword argument
                if not (info := imp.annotation_info.get(varname)):
                    score -= maxsize
                    continue

                _locals[varname] = arg
                type_, predicate = info

                if type_ == Any:
                    score += 5  # compatible with typing.Any
                elif not isinstance(arg, type_):
                    score -= maxsize  # incompatible type
                elif isinstance(type_, UnionType):
                    score += 10  # compatible with UnionType
                else:
                    score += 20  # compatible with basic type
                    # Subtract distance in MRO
                    offset = type(arg).__mro__.index(type_)
                    mro_bonus = 10 - offset
                    score += mro_bonus

                # Based on predicates (the `True` predicate doesn't exclude
                # the implementation, but neither does it improve its score)
                result = eval(predicate, locals=_locals)  # type: ignore
                if not result:
                    score -= maxsize  # incompatible predicate
                elif predicate != "True":
                    score += 31  # non-trivial predicate satisfied

            if score > best_score:
                best_score = score
                implementation = imp

        if implementation is None:
            raise ValueError(f"No matching implementation for {args=}, {kws=}")

        return implementation.fn(*args, **kws)

    # Return the closure returning the best implementation
    return best_implementation


# =============================================================================
# The Dispatcher class and its metaclass
# =============================================================================
class DispatcherMeta(type):
    def __repr__(cls):
        s = f"{cls.__name__} bound implementations:"
        for key, funcs in cls.funcs.items():  # type: ignore
            for n, fi in enumerate(funcs):
                s += f"\n({n}) {key}"
                if key != fi.fn.__name__:
                    s += f" (re-bound '{fi.fn.__name__}')"
                for argname, info in fi.annotation_info.items():
                    pretty_type = (
                        info.type.__name__
                        if hasattr(info.type, "__name__")
                        else str(info.type)
                    )
                    s += f"\n    {argname}: {pretty_type} ∩ {info.predicate}"
        return s

    def __str__(cls):
        n_names = sum(1 for f in cls.funcs if f not in namespace_detritus)
        n_impls = sum(len(funcs) for funcs in cls.funcs.values())
        n_extra_types = len(cls.extra_types)
        return (
            f"{cls.__name__} with {n_names} function{'s' if n_names > 1 else ''} "
            f"bound to {n_impls} implementation{'s' if n_impls > 1 else ''} "
            f"({n_extra_types} extra types)"
        )

    def describe(cls):
        print(repr(cls))

    def __getattr__(cls, name):
        "Implements multiple and predicative dispatch, if bound name exists."
        if not (implementations := cls.funcs.get(name, [])):
            raise AttributeError(f"No implementations are bound to {name}")
        return cls.resolver(implementations)


def get_dispatcher(
    name: str = "Dispatcher",
    resolver: Callable = weighted_resolver,
    extra_types: Collection = set(),
):
    "Manufacuture as many Dispatcher objects as needed."

    class Dispatcher(metaclass=DispatcherMeta):
        funcs = defaultdict(list)
        to_bind = None

        def __new__(
            cls,
            fn: Callable | None = None,
            *,
            name: str = "",
        ):
            new = super().__new__(cls)
            new.resolver = resolver
            new.extra_types = set(extra_types)  # type: ignore

            if fn is not None:
                name = fn.__name__
                fn.extra_types = set(extra_types)  # type: ignore
                implementation = function_info(fn, annotation_info(fn))
                new.__class__.funcs[name].append(implementation)
            elif not name:
                raise ValueError(
                    f"{cls.__name__} must be used as a decorator, "
                    "or to call a bound method)"
                )
            elif name:
                new.__class__.to_bind = name

            return new

        def __repr__(self):
            return repr(self.__class__)

        def __str__(self):
            return str(self.__class__)

        def __call__(self, fn):
            name = self.__class__.to_bind or fn.__name__
            fn.extra_types = self.__class__.extra_types
            implementation = function_info(fn, annotation_info(fn))
            self.__class__.funcs[name].append(implementation)
            self.__class__.to_bind = None  # Clear the binding after using it
            return self.__class__

        @property
        def resolver(self):
            return self.__class__.resolver  # type: ignore

        @resolver.setter
        def resolver(self, resolver):
            self.__class__.resolver = resolver

        @property
        def extra_types(self):
            return self.__class__.extra_types  # type: ignore

        @extra_types.setter
        def extra_types(self, extra_types):
            self.__class__.extra_types = extra_types

    Dispatcher.__name__ = name
    return Dispatcher


# This is a default Dispatcher object, for common scenarios needing just one.
Dispatcher = get_dispatcher()
