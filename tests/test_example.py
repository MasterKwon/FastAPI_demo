import pytest

def test_addition():
    assert 1 + 1 == 2

def test_string_concatenation():
    assert "hello" + "world" == "helloworld"

@pytest.fixture
def sample_list():
    return [1, 2, 3, 4, 5]

def test_list_length(sample_list):
    assert len(sample_list) == 5

def test_list_sum(sample_list):
    assert sum(sample_list) == 15

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0 