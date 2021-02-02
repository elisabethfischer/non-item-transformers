import math
from typing import Tuple

import torch
from torch import nn
from torch.nn import functional as F

from models.layers.layers import ItemEmbedding
from models.layers.tensor_utils import generate_position_ids


class TransformerEmbedding(nn.Module):
    """
    this transformer embedding combines the item embedding and positional embedding (incl. norm) into a single module
    """

    def __init__(self,
                 item_voc_size: int,
                 max_seq_len: int,
                 embedding_size: int,
                 dropout: float,
                 embedding_pooling_type: str = None,
                 norm_embedding: bool = True):
        super().__init__()

        self.embedding_size = embedding_size

        self.item_embedding = ItemEmbedding(item_voc_size=item_voc_size,
                                            embedding_size=embedding_size,
                                            embedding_pooling_type=embedding_pooling_type)
        self.position_embedding = nn.Embedding(max_seq_len, self.embedding_size)
        self.embedding_norm = nn.LayerNorm(self.embedding_size) if norm_embedding else nn.Identity()
        self.dropout = nn.Dropout(p=dropout)

    def get_item_embedding_weight(self) -> torch.Tensor:
        """
        :return: the weight matrix of the item embedding
        some methods reuse the matrix to reduce the parameter size
        """
        return self.item_embedding.embedding.weight

    def get_item_embedding(self,
                           input_sequence: torch.Tensor,
                           flatten: bool = True
                           ) -> torch.Tensor:
        return self.item_embedding(input_sequence, flatten=flatten)

    def forward(self,
                input_sequence: torch.Tensor,
                position_ids: torch.Tensor = None
                ) -> torch.Tensor:
        """
        :param input_sequence: (N, S)
        :param position_ids: the position ids (N, S) optional, will be generated if not provided

         where S is the sequence length and N the batch size
        :return:
        """
        # generate the position ids if not provided
        if position_ids is None:
            position_ids = generate_position_ids(input_sequence.size(), device=input_sequence.device)

        input_sequence = self.item_embedding(input_sequence)
        input_sequence = input_sequence + self.position_embedding(position_ids)
        input_sequence = self.embedding_norm(input_sequence)

        input_sequence = self.dropout(input_sequence)
        return input_sequence


class TransformerLayer(nn.Module):

    def __init__(self,
                 transformer_hidden_size: int,
                 num_transformer_heads: int,
                 num_transformer_layers: int,
                 dim_feedforward: int,
                 transformer_dropout: float
                 ):
        super().__init__()
        # multi-layers transformer blocks, deep network
        self.transformer_blocks = nn.ModuleList(
            [TransformerBlock(transformer_hidden_size, num_transformer_heads, dim_feedforward, transformer_dropout)
             for _ in range(num_transformer_layers)])

    def forward(self,
                input_sequence: torch.Tensor,
                attention_mask: torch.Tensor
                ) -> torch.Tensor:

        # running over multiple transformer blocks
        for transformer in self.transformer_blocks:
            input_sequence = transformer.forward(input_sequence, attention_mask)

        return input_sequence


class SublayerConnection(nn.Module):
    """
    A residual connection followed by a layer norm.
    Note for code simplicity the norm is first as opposed to last.
    """

    def __init__(self, size, dropout):
        super().__init__()
        self.norm = nn.LayerNorm(size)
        self.dropout = nn.Dropout(dropout)

    def forward(self,
                layer_input: torch.Tensor,
                sublayer
                ):
        """ Apply residual connection to any sublayer with the same size.
        :param layer_input:
        :param sublayer:
        :return:
        """

        return layer_input + self.dropout(sublayer(self.norm(layer_input)))


class Attention(nn.Module):

    """
    Computes 'Scaled Dot Product Attention'
    """
    def forward(self,
                query: torch.Tensor,
                key: torch.Tensor,
                value: torch.Tensor,
                attention_mask: torch.Tensor = None,
                dropout: nn.Dropout = None
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.size()[-1])

        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask == 0, -1e9)

        p_attn = F.softmax(scores, dim=-1)

        if dropout is not None:
            p_attn = dropout(p_attn)

        return torch.matmul(p_attn, value), p_attn


class MultiHeadedAttention(nn.Module):
    """
    Take in model size and number of heads.
    """

    def __init__(self,
                 heads: int,
                 d_model: int,
                 dropout: float = 0.1
                 ):
        super().__init__()
        assert d_model % heads == 0

        # we assume d_v always equals d_k
        self.d_k = d_model // heads
        self.heads = heads

        self.linear_layers = nn.ModuleList([nn.Linear(d_model, d_model) for _ in range(3)])
        self.output_linear = nn.Linear(d_model, d_model)
        self.attention = Attention()

        self.dropout = nn.Dropout(p=dropout)

    def forward(self,
                query: torch.Tensor,
                key: torch.Tensor,
                value: torch.Tensor,
                attention_mask: torch.Tensor = None
                ) -> torch.Tensor:
        batch_size = query.size()[0]

        # 1) Do all the linear projections in batch from d_model => h x d_k
        query, key, value = [l(x).view(batch_size, -1, self.heads, self.d_k).transpose(1, 2)
                             for l, x in zip(self.linear_layers, (query, key, value))]

        # 2) Apply attention on all the projected vectors in batch.
        x, attn = self.attention(query, key, value, attention_mask=attention_mask, dropout=self.dropout)

        # 3) "Concat" using a view and apply a final linear.
        x = x.transpose(1, 2).contiguous().view(batch_size, -1, self.heads * self.d_k)

        return self.output_linear(x)


class PositionwiseFeedForward(nn.Module):
    """
    Implements FFN equation.
    """

    def __init__(self,
                 d_model: int,
                 d_ff: int,
                 dropout: float = 0.1):
        super(PositionwiseFeedForward, self).__init__()
        self.w_1 = nn.Linear(d_model, d_ff)
        self.w_2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self,
                x: torch.Tensor
                ) -> torch.Tensor:
        return self.w_2(self.dropout(self.activation(self.w_1(x))))


class TransformerBlock(nn.Module):
    """
    Bidirectional Encoder = Transformer (self-attention)
    Transformer = MultiHead_Attention + Feed_Forward with sublayer connection
    """

    def __init__(self,
                 hidden: int,
                 attn_heads: int,
                 feed_forward_hidden: int,
                 dropout: float):
        """
        :param hidden: hidden size of transformer
        :param attn_heads: head sizes of multi-head attention
        :param feed_forward_hidden: feed_forward_hidden, usually 4 * hidden_size
        :param dropout: dropout rate
        """

        super().__init__()
        self.attention = MultiHeadedAttention(heads=attn_heads, d_model=hidden, dropout=dropout)
        self.feed_forward = PositionwiseFeedForward(d_model=hidden, d_ff=feed_forward_hidden, dropout=dropout)
        self.input_sublayer = SublayerConnection(size=hidden, dropout=dropout)
        self.output_sublayer = SublayerConnection(size=hidden, dropout=dropout)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self,
                input_sequence: torch.Tensor,
                attention_mask: torch.Tensor
                ) -> torch.Tensor:
        input_sequence = self.input_sublayer(input_sequence, lambda _x: self.attention.forward(_x, _x, _x,
                                                                                               attention_mask=attention_mask))
        input_sequence = self.output_sublayer(input_sequence, self.feed_forward)
        return self.dropout(input_sequence)
