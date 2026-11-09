import pytest

from bnbpy import is_compiled


@pytest.mark.core
def test_compilation() -> None:
    assert is_compiled(), 'Compilation failed'
