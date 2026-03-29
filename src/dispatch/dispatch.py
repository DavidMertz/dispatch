"""
Implement both multiple dispatch and "predicative" dispatch.

See README.md for an historical discussion of this topic.
"""

from __future__ import annotations
from collections import defaultdict, namedtuple
from sys import maxsize
from types import UnionType
from typing import Any, Callable, Collection, Mapping

namespace_detritus = [
    "_ipython_canary_method_should_not_exist_",
    "_ipython_display_",
    "_repr_mimebundle_",
]

AnnotationInfo = namedtuple("AnnotationInfo", "type predicate")
FunctionInfo = namedtuple("FunctionInfo", "fn annotation_info")
SimpleValue = namedtuple("SimpleValue", "name value")


def function_info(
    fn: Callable, annotation_info: dict[str, AnnotationInfo]
) -> FunctionInfo:
    "Cleanup function object and aggregate with extracted annotation info."
    # TODO: Massage function object's __annotations__ attribute
    return FunctionInfo(fn, annotation_info)


def annotation_info(fn: Callable) -> dict[str, AnnotationInfo]:
    """
    Extract args, types, and predicates from function annotations.

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
        for extra in fn.extra_types:
            # We might add simple values like x=42 to _locals
            if isinstance(extra, SimpleValue):
                key, val = extra
                _locals[key] = val
            # Otherwise it's a class, function, etc that has a name
            else:
                _locals[extra.__name__] = extra

    # Locals defined in the function scope are in `co_varnames`, but they come
    # _after_ the formal arguments whose count is `co_argcount`.
    for arg in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
        if arg not in fn.__annotations__:
            # No type annotation or predicate
            annotations[arg] = AnnotationInfo(Any, "True")  # No type annotation
            continue
            
        annotation_str = fn.__annotations__[arg]
        
        # Handle the case where there's both type and predicate (separated by &)
        if "&" in annotation_str:
            parts = annotation_str.split("&", maxsplit=1)
            type_part, predicate = parts[0].strip(), parts[1].strip()
            
            try:
                type_ = eval(type_part, locals=_locals)  # type: ignore
                if isinstance(type_, (type, UnionType)):
                    annotations[arg] = AnnotationInfo(type_, predicate)
                else:
                    # This is an edge case where the first part isn't a valid type
                    annotations[arg] = AnnotationInfo(Any, annotation_str.strip())
            except Exception:
                # If we can't evaluate the type part, treat entire annotation as predicate
                annotations[arg] = AnnotationInfo(Any, annotation_str.strip())
        else:
            # No predicate - just a type annotation
            try:
                # Try to evaluate as a type
                type_ = eval(annotation_str, locals=_locals)  # type: ignore
                if isinstance(type_, (type, UnionType)):
                    annotations[arg] = AnnotationInfo(type_, "True")  # No predicate
                else:
                    # This is the odd case of non-contextual predicate (e.g. 2+2==5)
                    boolean_result = str(type_)
                    annotations[arg] = AnnotationInfo(Any, boolean_result)
            except Exception:
                # Not a type annotation, so it's a predicate (store as a string)
                annotations[arg] = AnnotationInfo(Any, annotation_str.strip())

    return annotations


# =============================================================================
# Define at least one "MRO" resolver.
# =============================================================================
# Prior to PEP 484 and numerous compound types (Union[] specifically), it
# was possible to rank matches. That is no longer coherent.  For example:
#
#   >>> class SpecialInt(int):
#   ...     pass
#   ...
#   >>> n = SpecialInt(13)
#   >>> type(n).mro()
#   [<class '__main__.SpecialInt'>, <class 'int'>, <class 'object'>]
#
# In some sense, `n` is "most like" a SpecialInt, a bit less like an int,
# and just nominally like an object.  In this simple case, we can rank or
# weight such distances in evaluating several candidate implementations.
#
#   >>> def add(a: int, b: int | float | complex):
#   ...     return a + b
#   ...
#   >>> add(SpecialInt(13), SpecialInt(12))
#   25
#
# We can sensibly measure the "fit" of the match of the first argument, but
# we cannot do so for the second argument.  It's simply a match or non-match.
def weighted_resolver(
    implementations: list[FunctionInfo],
    *args,
    **kws,
) -> Callable:
    """
    Select an implementation by weighting satisfiable types and predicates.

    If any type or predicate is directly violated, exclude that implementation.
    If no matching implementation is found, raise an exception.

    The scoring mechanism works as follows:
    
    1. For each argument, calculate a score based on:
       - Type compatibility (higher scores for better matches)
       - Predicate satisfaction (higher scores for satisfied predicates)
    
    2. For type compatibility:
       - If a type is incompatible with an argument, we subtract -sys.maxsize.
       - If a type is compatible with typing.Any, we add +5 to the score.
       - If a type is compatible with a UnionType, we add +10 to the score.
       - If a type is compatible with a simple type, we add +20 to the score.
       - If a type is compatible with a simple type, but farther removed in its
         MRO, subtract -1 for each step in the MRO.

    3. For predicates:
       - If both predicates are satisfied, the first implementation is chosen.
       - If only one predicate is satisfied, that implementation is chosen.
       - If one predicate is absent, the more specific implementation is chosen.
       - If a predicate is satisfied, we add +3 for positional arguments or +31 
         for keyword arguments.
    """
    _, _ = args, kws  # Just feeding the linter

    def best_implementation(*args, **kws):
        best_score = 0
        implementation = None
        # Might be a dry-run; if so, note that but remove from kws
        dry_run = False
        if "_dry_run" in kws:
            dry_run = kws.pop("_dry_run")

        for imp in implementations:
            # Accumulate local vars as args are passed in, and extra_types if any
            _locals = {}
            for extra in imp.fn.extra_types:
                # We might add simple values like x=42 to _locals
                if isinstance(extra, SimpleValue):
                    key, val = extra
                    _locals[key] = val
                # Otherwise it's a class, function, etc that has a name
                else:
                    _locals[extra.__name__] = extra

            # More arguments is "better" than fewer arguments
            score = len(args)

            # An implementation with too few arguments is incompatible
            max_args = imp.fn.__code__.co_argcount
            if len(args) > max_args:
                score -= maxsize
                continue

            # Process positional arguments
            for arg, info in zip(
                args,
                imp.annotation_info.items(),
            ):
                score += _calculate_score_for_arg(arg, info, _locals, is_positional=True)

            # Add weights based on keywords (similar to positional args)
            for varname, arg in kws.items():
                # An implementation might not have a given keyword argument
                if not (info := imp.annotation_info.get(varname)):
                    score -= maxsize
                    continue

                score += _calculate_score_for_arg(arg, (varname, info), _locals, is_positional=False)

            if score > best_score:
                best_score = score
                implementation = imp

        if implementation is None:
            raise ValueError(f"No matching implementation for {args=}, {kws=}")

        return implementation.fn if dry_run else implementation.fn(*args, **kws)

    def _calculate_score_for_arg(arg, info, _locals, is_positional=True):
        """Helper function to calculate score for a single argument."""
        varname, (type_, predicate) = info
        _locals[varname] = arg

        # Based on type information
        score = 0
        if type_ == Any:
            score += 5  # compatible with typing.Any
        elif not isinstance(arg, type_):
            return -maxsize  # incompatible type
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
            return score
            
        try:
            result = eval(predicate, locals=_locals)  # type: ignore
        except Exception:
            # If a predicate cannot be evaluated, stipulate False.
            # E.g. Complex arg with predicate of inequality with an int
            result = False  # Assume predicate is False
        if not result:
            return -maxsize  # incompatible predicate
        elif predicate != "True":
            # Different weights for positional vs keyword arguments
            score += 3 if is_positional else 31  # non-trivial predicate satisfied

        return score

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
    "Manufacture as many Dispatcher objects as needed."

    class Dispatcher(metaclass=DispatcherMeta):
        funcs = defaultdict(list)
        to_bind = None
        using = []

        def __new__(
            cls, fn: Callable | None = None, *, name: str = "", using: list = []
        ):
            new = super().__new__(cls)
            new.resolver = resolver
            new.extra_types = set(extra_types)  # type: ignore

            if fn is not None:
                # Decorator usage - bind a function directly
                name = fn.__name__
                fn.extra_types = set(extra_types)  # type: ignore
                implementation = function_info(fn, annotation_info(fn))
                new.__class__.funcs[name].append(implementation)
            elif name:
                # Binding to a function name that will be bound later
                new.__class__.to_bind = name
                new.__class__.using = using
            elif using:
                # Using extra types but no function or name specified
                new.__class__.to_bind = None
                new.__class__.using = using
            else:
                raise ValueError(
                    f"{cls.__name__} must be used as a decorator, "
                    "or to call a bound method)"
                )

            return new

        def __repr__(self):
            return repr(self.__class__)

        def __str__(self):
            return str(self.__class__)

        def __call__(self, fn):
            # This is called when the dispatcher is used as a decorator
            name = self.__class__.to_bind or fn.__name__
            fn.extra_types = self.__class__.extra_types
            
            # Inject additional names needed for this implementation
            for extra in self.__class__.using:
                if hasattr(extra, "__name__"):
                    fn.extra_types.add(extra)
                elif isinstance(extra, dict):
                    for k, v in extra.items():
                        fn.extra_types.add(SimpleValue(k, v))
                elif isinstance(extra, tuple) and len(extra) == 2:
                    fn.extra_types.add(SimpleValue(*extra))
                else:
                    raise ValueError(
                        "Injected names must have a __name__ attribute or "
                        f"consist of a key/value pair ({extra})"
                    )

            implementation = function_info(fn, annotation_info(fn))
            self.__class__.funcs[name].append(implementation)
            self.__class__.to_bind = None  # Clear the binding after using it
            self.__class__.using = []  # Clear the extra exposed values
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
