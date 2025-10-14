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

The above example is trivial, but we can examine the two dispatchers to see
that we have bound implementations in the expected manner:

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

hr = get_dispatcher(name="HR_Department", 
                    extra_types=[Person, Employer])

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

## Binding implementations

A few binding examples were shown already when we saw how to create
dispatchers.  In those simplest examples, only type information was
demonstrated.  Let us create additional bound implementations that utilize both
types and predicates.  Here we also show that these dispatch decisions are, in
fact, being honored by the dispatcher.

```python
from __future__ import annotations
from dispatch.dispatch import get_dispatcher
Greet = get_dispatcher(name="Greet")

@Greet
def hello(name: str, lang: str & lang == "English"):
    print(f"Hello {name}!")

@Greet
def hello(name, lang: lang == "Swahili"):
    print(f"Habari {name}!")

@Greet
def hello(name: str & len(name) > 20):
    print(f"You have a very long name, {name}")

@Greet
def hello(n: int):
    print(f"Hey {n:,}, you are my favorite number!")
```

Let us examine these several implementations that were created.  Notice that
the function signatures used various type annoations, some arguments have no
type annotation at all, and some arguments contain predicates.  These
heterogeneous forms of function definition are generally handled gracefully to
select the most appropriate code path.

```python
>>> Greet.describe()
Greet bound implementations:
(0) hello
    name: str ∩ True
    lang: str ∩ lang == 'English'
(1) hello
    name: Any ∩ True
    lang: Any ∩ lang == 'Swahili'
(2) hello
    name: str ∩ len(name) > 20
(3) hello
    n: int ∩ True
```

The method `.describe()` is reserved, and simply prints out the `repr()` of the
dispatcher object.  If users find a need to define a bound function with that
exact name, we may reconsider that API detail.

Let's utilize this function that is bound to several implementations:

```python
>>> Greet.hello("David", "English")
Hello David!

>>> Greet.hello("David", lang="Swahili")
Habari David!

>>> Greet.hello("Maria Rosalia Isabella")
You have a very long name, Maria Rosalia Isabella

>>> Greet.hello(3_141_592)
Hey 3,141,592, you are my favorite number!
```

The implementations we defined here are somewhat incomplete.  For example, we
only know how to handle two languages for "short" names.  We will get an
exception if we cannot find any implementation matching the types and
predicates required for the arguments:

```python
>>> Greet.hello("David", lang="Mandarin")
Traceback (most recent call last):
  Cell In[20], line 1
    Greet.hello("David", lang="Mandarin")
  File ~/git/dispatch/src/dispatch/dispatch.py:254 in best_implementation
    raise ValueError(f"No matching implementation for {args=}, {kws=}")
ValueError: No matching implementation for 
    args=('David',), kws={'lang': 'Mandarin'}
```

Our dispatcher is extensible, however, and we can easily add a more generic
fallback without needing to change any existing implementations.

```python
>>> @Greet
... def hello(name: str, lang="Unknown"):
...     print(f"-> {name} (lang={lang})")
...
>>> Greet.hello("David", "Mandarin")
-> David (lang=Mandarin)
```

## Customizing bindings

* Exposing needed objects and names to the dispatcher namespace.
* Renaming bound functions.

## Debugging a dispatcher

When many different implementations of a function have been bound, it may
become difficult to reason about which implementation will actually be called.

For example, arguments having inherited types are "compatible" with type
signatures indicating ancestors.  But the _resolver_ will prefer to match a
type closer to the argument actually passed in.  This is similar to the
`__mro__()` used in Python inheritance, but there are additional wrinkles when
we dispatch based on multiple arguments (i.e. multiple dispatch).

As a simple example, we create some children and a grandchild of `int`, and
define some function signatures involving these descendents.

```python
from __future__ import annotations
from dispatch.dispatch import get_dispatcher

class RedInt(int): pass
class CrimsonInt(RedInt): pass
class BlueInt(int): pass

colors = get_dispatcher("ColoredNumbers", 
                        extra_types=[RedInt, BlueInt, CrimsonInt])

@colors
def add(a: int, b: int):
    print(f"Int sum {a+b}")

@colors
def add(a: RedInt, b: RedInt):
    print(f"RedInt sum {a+b}")

@colors
def add(a: RedInt, b: BlueInt):
    print(f"Purple sum {a+b}")

@colors
def add(a: RedInt, b: int):
    print(f"Pink sum {a+b}")

```

With various combinations of arguments, it might not be obvious which
implementation will be chosen.  We can ask that before actually calling the
function.

```python
>>> from dispatch.debug import dry_run
>>> dry_run(colors, "add", CrimsonInt(17), 19)
Implementation(
    name='add', 
    id=4426660352, 
    extra_types={<class '__main__.BlueInt'>, 
                 <class '__main__.RedInt'>, 
                 <class '__main__.CrimsonInt'>},
    annotations={'a': 'RedInt', 'b': 'int'}
)
>>> colors.add(CrimsonInt(17), 19)
Pink sum 36

>>> dry_run(colors, "add", CrimsonInt(17), BlueInt(21)).annotations
{'a': 'RedInt', 'b': 'BlueInt'}
>>> colors.add(CrimsonInt(17), BlueInt(21))
Purple sum 38
```

The same `dry_run()` capability will also choose among predicates that are
satisfiable.  For example, arguments might match multiple predicates, but have
some data types match more closely than others.  If any predicate fails, that
implementation is completely ruled out.
