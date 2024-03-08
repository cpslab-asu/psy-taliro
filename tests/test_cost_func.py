from pytest import fixture

from staliro import TestOptions
from staliro.cost_func import CostFunc, Result, Sample, costfunc


def test_decorator() -> None:
    @costfunc
    def func1(_: Sample) -> Result[str, float]:
        return Result("foo", 1.2)

    @costfunc()
    def func2(_: Sample) -> Result[str, float]:
        return Result("foo", 1.2)

    assert isinstance(func1, CostFunc)
    assert isinstance(func2, CostFunc)


@fixture
def sample() -> Sample:
    return Sample([], TestOptions())


def test_return_result(sample: Sample) -> None:
    @costfunc
    def mycostfunc(_: Sample) -> Result[str, float]:
        return Result("foo", 1.2)

    result = mycostfunc.evaluate(sample)

    assert isinstance(result, Result)
    assert result.value == "foo"
    assert result.extra == 1.2


def test_return_cost(sample: Sample) -> None:
    @costfunc
    def mycostfunc(_: Sample) -> str:
        return "bar"

    result = mycostfunc.evaluate(sample)

    assert isinstance(result, Result)
    assert result.value == "bar"
    assert result.extra is None
