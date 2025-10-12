from collections import namedtuple

from .dispatch import weighted_resolver

Implementation = namedtuple("Implementation", "name id extra_types annotations")


def dry_run(dispatcher, func_name, *args, **kws):
    if not hasattr(dispatcher, func_name):
        raise AttributeError(
            f"The dispatcher {dispatcher} does not contain a binding for {func_name}"
        )
    func = getattr(dispatcher, func_name)
    impl = func(*args, _dry_run=True, **kws)

    return Implementation(
        impl.__name__, id(impl), impl.extra_types, impl.__annotations__
    )
