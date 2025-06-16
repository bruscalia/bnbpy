from bnbpy import is_compiled


def test_compilation() -> None:
    assert is_compiled(), 'Compilation failed'
