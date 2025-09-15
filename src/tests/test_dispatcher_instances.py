from __future__ import annotations

from dispatch.dispatch import Dispatcher
from dispatch.dispatch import get_dispatcher


def test_distinct_class_objects():
    "Each Dispatcher object produced from factory should be distinct."
    MM = get_dispatcher()
    MM2 = get_dispatcher()

    assert MM is not MM2
    assert MM is not Dispatcher
    assert MM2 is not Dispatcher

    assert type(MM) == type(MM2)
    assert type(MM) == type(Dispatcher)


def test_multiple_implementations():
    """
    As we define implementations, their names should point to same Dispatcher

    Instances of a Dispatcher behave essentially the same as the class object,
    but are not identical in memory location or type.
    """

    # Make Pyright happy(ier) about the function redefintion"
    @Dispatcher
    def say(s: str):  # type: ignore
        print(f"String: say({s})")

    # From non-parameterized decorator we get an instance of Dispatcher
    assert say is not Dispatcher
    assert isinstance(say, Dispatcher)
    assert isinstance(type(say), type(Dispatcher))
    assert (
        str(Dispatcher)
        == "Dispatcher with 1 function bound to 1 implementation (0 extra types)"
    )
    assert (
        str(say)
        == "Dispatcher with 1 function bound to 1 implementation (0 extra types)"
    )
    first_say_id = id(say)

    @Dispatcher(name="say")
    def say_two_things(s: str, n: int):
        print(f"String and int: {s}, {n}")

    # From parameterized decorator we get the class object itself
    assert say_two_things is Dispatcher
    assert (
        str(say_two_things)
        == "Dispatcher with 1 function bound to 2 implementations (0 extra types)"
    )

    @Dispatcher
    def say(n: int & n > 100):  # type: ignore
        print(f"Large int: {n}")

    # From non-parameterized decorator we get an instance of Dispatcher
    assert say is not Dispatcher
    assert id(say) != first_say_id
    assert isinstance(type(say), type(Dispatcher))
    assert (
        str(say)
        == str(Dispatcher)
        == "Dispatcher with 1 function bound to 3 implementations (0 extra types)"
    )
