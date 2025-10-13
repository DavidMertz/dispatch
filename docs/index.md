# About the Package

This package enables extensible and context-sensitive dispatch to different
code implementations that depend both on the annotated type of arguments and on
predicates that are fulfilled by arguments.

Specifically, these dispatch decisions are arranged in a manner different than
with blocks of `if/elif` or `match/case` statements, and also differently from
inheritance hierarchies that resolve to a narrowest descendant type containing
a given method.

Numerous developers have created a version of a multimethods for Python (see
[History of Dispatch Concepts](HISTORY.md)).  Most or all of those use
decorators, or other conventions, to attach multiple implementations to the
same global name, and switch between implentations at call time within an
ordinary-looking function.

I have decided here on a slightly different API.  A "dispatcher" is a
namespace in which multiple callable names may live, and calling each one
makes a runtime dispatch decision. The general intention in this design is
that these namespaces (classes, behind the scenes) can associate related
functionality, and the collection of names and implementations in a namespace
can all be imported by importing the one namespace object.

A default dispatcher named `Dispatcher` can be imported directly, but normally
a factory function will generate new ones.  In the [Usage example](EXAMPLE.md),
a namespace called `nums` is created (e.g. for numeric functions with multiple
implementations), but a real problem might create others called `events` or
`datasets` or `customers`.

The advantage of having a namespace object that maintains dispatchable
implementations is that that object itself is indefinitely extensible.  Within
your application code that imports, e.g., the `num` namespace object, you can
add many new function names and/or implementations for the already defined
names.

A full application might have multipe namespace objects, perhaps each imported
from a different upstream developer.  While a namespace can _do more_ than a
mere module, in many ways importing a namespace object resembles importing a
module (which _is_, after all, also just a namespace at heart).

## Resources

I gave a presentation on a beta version of `gnosis-dispatch` and the
background concepts that motivated creation of this package at [PyCon Africa
2025](https://za.pycon.org).  That talk was titled _Multiple and Predicative
Dispatch_ (the LibreOffice and PDF versions are retained in the repository):

> [Conference Talk](https://github.com/DavidMertz/dispatch/blob/main/presentations/PyCon-Africa-2025/Multiple-and-Predicative-Dispatch.pdf)


