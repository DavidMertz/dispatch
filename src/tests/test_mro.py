from __future__ import annotations
from dispatch.dispatch import get_dispatcher


class SpecialInt(int):
    "A subclass a step away from int; no special behavior for tests"

    pass


N = SpecialInt(13)

Disp = get_dispatcher("Disp")

@Disp
def show(a: int, b: int | float | complex):  # type: ignore
    return f"{a}: int, {b}: int | float | complex"


@Disp
def show(a: int, b: int):  # type: ignore
    return f"{a}: int, {b}: int"


@Disp
def show(a: SpecialInt, b: int):  # type: ignore
    return f"{a}: SpecialInt, {b}: int | float | complex"


@Disp
def show(a: int, b: SpecialInt):  # type: ignore
    return f"{a}: int, {b}: SpecialInt"


def test_show_int_union():
    assert Disp.show(11, 3.1415) == "11: int, 3.1415: int | float | complex"
