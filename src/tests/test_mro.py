from __future__ import annotations
from dispatch.dispatch import get_dispatcher


class SpecialInt(int):
    "A subclass a step away from int; no special behavior for tests"

    pass


n_spec = SpecialInt(13)

disp = get_dispatcher(name="Dispatch", extra_types=[SpecialInt])


@disp(name="show")
def show_int_union(a: int, b: int | float | complex):  # type: ignore
    return f"{a}: int, {b}: int | float | complex"


@disp(name="show")
def show_int_int(a: int, b: int):  # type: ignore
    return f"{a}: int, {b}: int"


@disp(name="show")
def show_special_int(a: SpecialInt, b: int):  # type: ignore
    return f"{a}: SpecialInt, {b}: int"


@disp(name="show")
def show_int_special(a: int, b: SpecialInt):  # type: ignore
    return f"{a}: int, {b}: SpecialInt"


@disp(name="show")
def show_special_special(a: SpecialInt, b: SpecialInt):  # type: ignore
    return f"{a}: SpecialInt, {b}: SpecialInt"


def test_disp_str():
    assert (
        str(disp)
        == "Dispatch with 1 function bound to 5 implementations (1 extra types)"
    )


def test_resolver():
    assert disp.resolver.__name__ == "weighted_resolver"


def test_extra_types():
    assert disp.extra_types == [SpecialInt]


def test_show_int_union():
    assert disp.show(11, 3.14) == "11: int, 3.14: int | float | complex"


def test_show_special_int():
    assert disp.show(n_spec, 7) == "13: SpecialInt, 7: int"


def test_show_int_special():
    assert disp.show(11, n_spec) == "11: int, 13: SpecialInt"


def test_show_special_special():
    assert disp.show(n_spec, n_spec) == "13: SpecialInt, 13: SpecialInt"
