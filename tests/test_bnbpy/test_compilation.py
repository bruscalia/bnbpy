from bnbpy import is_compiled


def test_compilation():
    assert is_compiled(), 'Compilation failed'
