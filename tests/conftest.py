import importlib

import pytest

import qre


@pytest.fixture(autouse=True)
def reset_registered_types():
    """Ensure global registered_types is reset to baseline before every test."""
    importlib.reload(qre)
