from __future__ import annotations
from dispatch.dispatch import get_dispatcher


def isLarge(n):
    return n > 100


def test_extra_func_str():
    sizer = get_dispatcher("sizer", extra_types=[isLarge])

    @sizer
    def about(a: int & isLarge(a)):
        return f"{a} is a large integer"

    @sizer
    def about(a: int):
        return f"{a} is some integer"

    assert str(sizer) == (
        "sizer with 1 function bound to 2 implementations (1 extra types)"
    )


def test_extra_func_repr():
    sizer = get_dispatcher("sizer", extra_types=[isLarge])

    @sizer
    def about(a: int & isLarge(a)):
        return f"{a} is a large integer"

    @sizer
    def about(a: int):
        return f"{a} is some integer"

    print(repr(sizer))
    assert repr(sizer) == (
        "sizer bound implementations:\n"
        "(0) about\n"
        "    a: int ∩ isLarge(a)\n"
        "(1) about\n"
        "    a: int ∩ True"
    )


def test_extra_func_call():
    sizer = get_dispatcher("sizer", extra_types=[isLarge])

    @sizer
    def about(a: int & isLarge(a)):
        return f"{a} is a large integer"

    @sizer
    def about(a: int):
        return f"{a} is some integer"

    assert sizer.about(5) == "5 is some integer"
    assert sizer.about(150) == "150 is a large integer"
