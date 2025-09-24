from __future__ import annotations
from dispatch.dispatch import get_dispatcher


class Quaternian:
    pass


class Matrix:
    pass


class Tensor:
    pass


def test_extra_types_list():
    math_ops = get_dispatcher("math_ops", extra_types=[Matrix, Tensor])

    @math_ops
    def add(a: int, b: int):
        return a + b

    _ = add

    assert str(math_ops) == (
        "math_ops with 1 function bound to 1 implementation (2 extra types)"
    )


def test_extra_types_repr():
    math_ops = get_dispatcher("math_ops", extra_types={Matrix, Tensor})

    @math_ops
    def add(a: int, b: int):
        return a + b

    _ = add

    assert repr(add) == (
        "math_ops bound implementations:\n"
        "(0) add\n"
        "    a: int ∩ True\n"
        "    b: int ∩ True"
    )


def test_extra_types_add():
    math_ops = get_dispatcher("math_ops", extra_types={Matrix, Tensor})

    @math_ops
    def add(a: int, b: int):
        return a + b

    _ = add

    math_ops.extra_types.add(Quaternian)  # type: ignore
    assert str(math_ops) == (
        "math_ops with 1 function bound to 1 implementation (3 extra types)"
    )


def test_extra_types_property():
    math_ops = get_dispatcher("math_ops", extra_types={Matrix, Tensor})

    @math_ops
    def add(a: int, b: int):
        return a + b

    _ = add

    assert set(math_ops.extra_types) == {Matrix, Tensor}  # type: ignore

    math_ops.extra_types.add(Quaternian)  # type: ignore
    assert math_ops.extra_types == {Matrix, Tensor, Quaternian}
