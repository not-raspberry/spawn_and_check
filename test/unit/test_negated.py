"""Unit tests for checks - mostly helpers."""
from itertools import cycle

from spawn_and_check.executor import negated


def test_negated():
    """
    Test ``negated`` function/decorator.

    Check if a negated function returns negated value, casts to bool and negates consecutive function calls - not
    the return value of the first call.
    """
    def get_return_mixed_fn():
        """Return a function that returns True or False."""
        iterator = cycle([True, False, True])
        return lambda: iterator.next()

    assert negated(lambda: True)() is False
    assert negated(lambda: False)() is True

    return_mixed = get_return_mixed_fn()
    return_mixed_negated = negated(get_return_mixed_fn())
    for i in xrange(3):
        assert return_mixed_negated() is not return_mixed()

    # Check casts to bool:
    assert negated(lambda: '')() is True
    assert negated(lambda: 'not empty')() is False

    def identity(val):
        return val

    # Check if arguments get passed:
    assert negated(identity)(True) is False
    assert negated(identity)(False) is True
