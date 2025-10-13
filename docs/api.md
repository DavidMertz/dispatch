# Package API

The main concerns in using `gnosis-dispatch` are:

* Creating a dispatcher.
* Defining/binding implementatons to function names.
* Exposing needed objects and names to the dispatcher namespace.
* Debugging and introspecting a dispatcher namespace

## When are annotations evaluated?

PEP 649 proposed "Deferred Evaluation Of Annotations Using Descriptors" way
back in 2021.  This actually followed an unfulfilled discussion of the same
topic in 2017.  The treatment of annotations has been discussed for a long
while.

However, there were unforseen complications in the full implementation of
deferred evaluation. The current status is described at:

  https://docs.python.org/3/reference/compound_stmts.html#annotations

Code that uses `gnosis-dispatch` should simply always include the "future"
behavior by including a first line in your files that define function
implementations of:

```python
from __future__ import annotations
```

This future statement will be deprecated and removed in a future version of
Python, but not before Python 3.13 reaches its end of life in late 2029.  At
that time, the deferred evaluation will simply be the only behavior.

My hunch is that even after 2029, the `__future__` statement will be retained
as a no-op; but even if it needs to be removed later, it is a single line that
can be commented out or deleted.

## Creating a dispatcher

One dispatcher is provided by default if your program only wishes to use one
namespace.  You may import this simply as:

```python
from dispatch.dispatch import Dispatcher
```

Or with a custom name,

```python
from dispatch.dispatch import Dispatcher as MyNameSpace
```

While this approach is perhaps useful for initial experimentation, it has
pitfalls for larger scale use.  For one thing, simply importing an object
under different names does not actually create different namespace
dispatchers.

```python
assert Dispatcher is MyNameSpace  # True
```

The more important limitation in using the pre-created `Dispatcher` is that
there is only one such object across all libraries that utilize
`gnosis-dispatch`.  If each library author were to use this approach, when you
import these many dispatchers, you would simply have one large namespace with
all the functions and implementations defined by diverse authors in different
libraries.

### A dispatcher factory

The usual mechanism for creating a dispatcher is with the _dispatcher
factory_.  Using this, you can create as many distinct namespaces as you wish,
and use any of them as decorators for whichever function implementations are
appropriate.

For example, let's create two dispatchers and attach functions to each of
them:

```python
from __future__ import annoations
from dispatch.dispatch import get_dispatcher

disp1 = get_dispatcher()
disp2 = get_dispatcher()

@disp1
def foo(x: int): pass

@disp1
def foo(x: float): pass

@disp2
def foo(x: str): pass
```

The above example is trivial, but we can examine the bound implementations to
see that we have bound implementations in the expected manner:

```python
>>> disp1
Dispatcher bound implementations:
(0) foo
    x: int ∩ True
(1) foo
    x: float ∩ True

>>> disp2
Dispatcher bound implementations:
(0) foo
    x: str ∩ True
```

### Customizing factory-made dispatchers

The default name "Dispatcher" attached to both `disp1` and `disp2` is not very
descriptive. We can specify a better name when we create a new dispatcher.  As
well, if the type signatures of functions use custom types, we must expose
those types to the dispatcher so that implementations may utilize them.

Let's combine these several concepts.

```python
from __future__ import annoations
from collections import namedtuple

Person = namedtuple("Person", "name age income")
class Employer(str): pass

hr = get_dispatcher(name="HR_Department", extra_types=[Person, Employer])

@hr
def hire(company: Employer, person: Person): ...

@hr
def hire(person_name: str): ...

@hr
def hire(person_id: int, company: Employer = "default_co"): ...
```

Here we provided three (skeletal) implementations, each bound to the function
name `hire()`.  Let's look at the summary:

```python
>>> hr
HR_Department bound implementations:
(0) hire
    company: Employer ∩ True
    person: Person ∩ True
(1) hire
    person_name: str ∩ True
(2) hire
    person_id: int ∩ True
    company: Employer ∩ True
```

