"""
Tests configuration.

The only import in this module causes unit tests to execute before the integration suite.
"""
from pytest_reorder import default_reordering_hook as pytest_collection_modifyitems  # noqa
