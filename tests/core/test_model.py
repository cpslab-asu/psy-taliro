from __future__ import annotations

from typing import Any
from unittest import TestCase

import staliro.core.model as model


class ModelResult(TestCase):
    def setUp(self) -> None:
        self.trace2d = model.Trace([1, 2], [[1, 2, 3], [4, 5, 6]])

    def test_basic_result(self) -> None:
        data = model.BasicResult(self.trace2d)
        self.assertEqual(data.trace, self.trace2d)
        self.assertIsNone(data.extra)

    def test_extra_result(self) -> None:
        data = model.ExtraResult(self.trace2d, "foo")
        self.assertEqual(data.trace, self.trace2d)
        self.assertEqual(data.extra, "foo")

    def test_failure_result(self) -> None:
        data: model.FailureResult[Any, str] = model.FailureResult("foo")
        self.assertEqual(data.trace, model.Trace([], []))
        self.assertEqual(data.extra, "foo")
