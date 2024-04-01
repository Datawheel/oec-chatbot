from src.wrapper.lanbot import Langbot 


def test_basic():
    assert Langbot('hi', lambda x: print(x), )