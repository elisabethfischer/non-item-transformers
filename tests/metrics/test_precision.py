from typing import Tuple

import pytest
import torch
from util import build_sample, EPSILON

from asme.metrics.precision import PrecisionMetric


def get_multiple_item_recommendation_samples():
    return [
        build_sample(torch.tensor([[0, 0, 0, 4, 5]]), torch.tensor([[0, 0, 0, 1, 1]]), 1, torch.tensor(1.)),
        build_sample(torch.tensor([[4, 5, 0, 0, 0]]), torch.tensor([[0, 0, 0, 1, 1]]), 1, torch.tensor(0.)),
        build_sample(torch.tensor([[0, 4, 5, 0, 0]]), torch.tensor([[0, 0, 0, 1, 1]]), 2, torch.tensor(0.)),
        build_sample(torch.tensor([[0, 0, 4, 5, 0]]), torch.tensor([[0, 0, 0, 1, 1]]), 2, torch.tensor(0.5)),
        build_sample(torch.tensor([[0, 0, 0, 4, 5]]), torch.tensor([[0, 0, 0, 1, 1]]), 2, torch.tensor(1.)),
        build_sample(torch.tensor([[0, 0, 0, 4, 5]]), torch.tensor([[0, 0, 0, 1, 1]]), 3, torch.tensor(0.6666)),
        build_sample(torch.tensor([[0, 0, 3, 4, 5]]), torch.tensor([[0, 0, 0, 1, 0]]), 3, torch.tensor(0.3333)),
        build_sample(torch.tensor([[0, 3, 4, 0, 5]]), torch.tensor([[0, 0, 1, 1, 1]]), 3, torch.tensor(0.6666)),
        build_sample(torch.tensor([[3, 4, 0, 0, 5]]), torch.tensor([[0, 0, 1, 1, 1]]), 3, torch.tensor(0.3333)),
        build_sample(torch.tensor([[0, 3, 4, 0, 5]]), torch.tensor([[0, 0, 0, 1, 1]]), 5, torch.tensor(0.4)),
        build_sample(torch.tensor([[0, 3, 4, 0, 5]]), torch.tensor([[0, 0, 0, 0, 1]]), 5, torch.tensor(0.2)),

    ]


class TestPrecision:

    @pytest.mark.parametrize("sample", get_multiple_item_recommendation_samples())
    def test_multiple_item_recommendation(self,
                                          sample: Tuple[torch.Tensor, torch.Tensor, int, torch.Tensor]
                                          ):
        predictions, target, k, value = sample
        instance = PrecisionMetric(k=k)
        instance.update(predictions, target)

        precision = instance.compute()
        assert torch.sum(torch.abs(precision - value)) < EPSILON
