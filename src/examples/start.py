from __future__ import annotations
from dispatch.dispatch import get_dispatcher

Say = get_dispatcher('Say')
@Say
def foo(a: str):
    print(a)


Say.foo(123)

Say.describe()

