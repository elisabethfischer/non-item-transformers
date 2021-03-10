from typing import Union, Dict, Optional

import torch

import pytorch_lightning as pl

from data.datasets import ITEM_SEQ_ENTRY_NAME, TARGET_ENTRY_NAME
from metrics.container.metrics_container import MetricsContainer
from models.narm.narm_model import NarmModel
from modules import LOG_KEY_VALIDATION_LOSS
from modules.metrics_trait import MetricsTrait
from modules.util.module_util import get_padding_mask, convert_target_to_multi_hot, build_eval_step_return_dict
from tokenization.tokenizer import Tokenizer
from torch import nn

from utils.hyperparameter_utils import save_hyperparameters


class NarmModule(MetricsTrait, pl.LightningModule):
    """
    The Narm module for training the Narm model
    """

    @save_hyperparameters
    def __init__(self,
                 model: NarmModel,
                 item_tokenizer: Tokenizer,
                 metrics: MetricsContainer,
                 learning_rate: float = 0.001,
                 beta_1: float = 0.99,
                 beta_2: float = 0.998
                 ):
        """
        Initializes the Narm Module.
        """
        super().__init__()
        self.model = model

        self.learning_rate = learning_rate
        self.beta_1 = beta_1
        self.beta_2 = beta_2
        self.item_tokenizer = item_tokenizer

        self.metrics = metrics

        self.save_hyperparameters(self.hyperparameters)

    def get_metrics(self) -> MetricsContainer:
        return self.metrics

    def training_step(self,
                      batch: Dict[str, torch.Tensor],
                      batch_idx: int
                      ) -> Optional[Union[torch.Tensor, Dict[str, Union[torch.Tensor, float]]]]:
        """
        Performs a validation step on a batch of sequences and returns the overall loss.

        `batch` must be a dictionary containing the following entries:
            * `ITEM_SEQ_ENTRY_NAME`: a tensor of size (N, S),
            * `TARGET_ENTRY_NAME`: a tensor of size (N) with the target items,

        :param batch: the batch
        :param batch_idx: the batch number.
        :return: A dictionary with entries according to `build_eval_step_return_dict`.

        where N is the batch size and S the max sequence length.
        """

        input_seq = batch[ITEM_SEQ_ENTRY_NAME]
        target = batch[TARGET_ENTRY_NAME]

        padding_mask = get_padding_mask(input_seq, self.item_tokenizer)

        logits = self.model(input_seq, padding_mask)
        loss = self._calc_loss(logits, target)

        return {
            "loss": loss
        }

    def _calc_loss(self,
                   logits: torch.Tensor,
                   target_tensor: torch.Tensor
                   ) -> torch.Tensor:
        if len(target_tensor.size()) == 1:
            # only one item per sequence step
            loss_fnc = nn.CrossEntropyLoss()
            return loss_fnc(logits, target_tensor)

        loss_fnc = nn.BCEWithLogitsLoss()
        target_tensor = convert_target_to_multi_hot(target_tensor, len(self.item_tokenizer), self.item_tokenizer.pad_token_id)
        return loss_fnc(logits, target_tensor)

    def validation_step(self,
                        batch: Dict[str, torch.Tensor],
                        batch_idx: int
                        ) -> Dict[str, torch.Tensor]:
        """
        Performs a validation step on a batch of sequences and returns the entries according
        to `build_eval_step_return_dict`.

        `batch` must be a dictionary containing the following entries:
            * `ITEM_SEQ_ENTRY_NAME`: a tensor of size (N, S),
            * `TARGET_ENTRY_NAME`: a tensor of size (N) with the target items,

        :param batch: the batch
        :param batch_idx: the batch number.
        :return: A dictionary with entries according to `build_eval_step_return_dict`.

        where N is the batch size and S the max sequence length.
        """

        input_seq = batch[ITEM_SEQ_ENTRY_NAME]
        target = batch[TARGET_ENTRY_NAME]

        # calc the padding mask
        padding_mask = get_padding_mask(input_seq, self.item_tokenizer)

        logits = self.model(input_seq, padding_mask)

        loss = self._calc_loss(logits, target)
        self.log(LOG_KEY_VALIDATION_LOSS, loss, prog_bar=True)

        mask = None if len(target.size()) == 1 else ~ target.eq(self.item_tokenizer.pad_token_id)

        return build_eval_step_return_dict(input_seq, logits, target, mask=mask)

    def test_step(self, batch, batch_idx):
        self.validation_step(batch, batch_idx)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(),
                                lr=self.learning_rate,
                                betas=(self.beta_1, self.beta_2))
