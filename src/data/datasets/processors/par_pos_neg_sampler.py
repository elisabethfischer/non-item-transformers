import torch

from typing import Union, List, Dict, Any, Set, Optional
from numpy.random._generator import default_rng

from data.datasets import ITEM_SEQ_ENTRY_NAME, SAMPLE_IDS, POSITIVE_SAMPLES_ENTRY_NAME, NEGATIVE_SAMPLES_ENTRY_NAME
from data.datasets.processors.processor import Processor
from asme.tokenization.tokenizer import Tokenizer

DEFAULT_SAMPLE_SIZE = 3


class ParameterizedPositiveNegativeSamplerProcessor(Processor):
    """
    Takes the input sequence and generates positive and negative target
    sequences (:code data.datasets.{POSITIVE, NEGATIVE}_SAMPLES_ENTRY_NAME).

    The input sequence is updated by cutting of the last t tokens.
    The positive samples are generated by taking the last t tokens of the input sequence.
    For the negative samples, t tokens are drawn uniformly random from the set of tokens not used during the session.

    Example: t=3
        Input:
            session: [1, 5, 7, 8, 10]
        Output:
            session:          [1, 5]
            positive samples: [7, 8, 10]
            negative samples: [2, 9, 6]

    """

    def __init__(self,
                 tokenizer: Tokenizer,
                 seed: int = 42,
                 t: Optional[int] = DEFAULT_SAMPLE_SIZE
                 ):
        super().__init__()
        self._tokenizer = tokenizer
        self._rng = default_rng(seed=seed)
        self.t = DEFAULT_SAMPLE_SIZE if t is None else t

    def _sample_negative_target(self,
                                session: Union[List[int], List[List[int]]]
                                ) -> Union[List[int], List[List[int]]]:

        # we want to use a multinomial distribution to draw negative samples fast
        # start with a uniform distribution over all vocabulary tokens
        weights = torch.ones([len(self._tokenizer)])

        # set weight for special tokens to 0.
        weights[self._tokenizer.get_special_token_ids()] = 0.

        # prevent sampling of tokens already present in the session
        used_tokens = self._get_all_tokens_of_session(session)
        weights[list(used_tokens)] = 0.

        if isinstance(session[0], list):
            results = []
            for seq_step in session[:self.t]:  # skip last t sequence steps
                neg_samples = torch.multinomial(weights, num_samples=self.t, replacement=True).tolist()
                results.append(neg_samples)
            return results

        return torch.multinomial(weights, num_samples=self.t, replacement=True).tolist()

    def _get_all_tokens_of_session(self, session: Union[List[int], List[List[int]]],
                                   ) -> Set[int]:
        if isinstance(session[0], list):
            flat_items = [item for sublist in session for item in sublist]
        else:
            flat_items = session

        return set(flat_items)

    def process(self,
                parsed_sequence: Dict[str, Any]
                ) -> Dict[str, Any]:
        session = parsed_sequence[ITEM_SEQ_ENTRY_NAME]

        if len(session) < (self.t + 1):
            print(session)
            raise AssertionError(f'{parsed_sequence[SAMPLE_IDS]}')

        x = session[:-self.t]
        pos = session[-self.t:]
        neg = self._sample_negative_target(session)

        parsed_sequence[ITEM_SEQ_ENTRY_NAME] = x
        parsed_sequence[POSITIVE_SAMPLES_ENTRY_NAME] = pos
        parsed_sequence[NEGATIVE_SAMPLES_ENTRY_NAME] = neg
        return parsed_sequence
