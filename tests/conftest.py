import importlib

import pytest

import qre
import registered_types


@pytest.fixture(autouse=True)
def reset_registered_types():
    """Ensure global registered_types is reset to baseline before every test."""
    importlib.reload(registered_types)
    importlib.reload(qre)
