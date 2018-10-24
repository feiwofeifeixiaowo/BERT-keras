import keras
import numpy as np
import keras.backend as K
from typing import Optional


def _get_pos_encoding_matrix(max_len, d_emb):
    pos_enc = np.array(
        [[pos / np.power(10000, 2 * (j // 2) / d_emb) for j in range(d_emb)] if pos != 0 else np.zeros(d_emb) for pos in
         range(max_len)])
    pos_enc[1:, 0::2] = np.sin(pos_enc[1:, 0::2])  # dim 2i
    pos_enc[1:, 1::2] = np.cos(pos_enc[1:, 1::2])  # dim 2i+1
    return pos_enc


class Embedding:
    def __init__(self, output_dim: int, dropout: float, vocab_size: int, num_segments: int,
                 max_len: int, trainable_pos_embedding: bool, use_one_dropout: bool,
                 token_emb_weight: Optional[np.array] = None, segment_emb_weight: Optional[np.array] = None,
                 pos_emb_weight: Optional[np.array] = None):
        self.token_emb = keras.layers.Embedding(vocab_size, output_dim, input_length=max_len,
                                                weights=None if token_emb_weight is None else [token_emb_weight])
        self.segment_emb = keras.layers.Embedding(num_segments, output_dim, input_length=max_len,
                                                  weights=None if segment_emb_weight is None else [segment_emb_weight])
        self.max_len = max_len
        if not trainable_pos_embedding:
            self.pos_emb = keras.layers.Embedding(max_len, output_dim, trainable=False, input_length=max_len, weights=[
                _get_pos_encoding_matrix(max_len, output_dim) if pos_emb_weight is None else [pos_emb_weight]])
        else:
            self.pos_emb = keras.layers.Embedding(max_len, output_dim, input_length=max_len)
        self.dropout = keras.layers.Dropout(dropout)
        self.use_one_dropout = use_one_dropout

    def __call__(self, tokens, segment_ids):
        token_embedding = self.token_emb(tokens)
        segment_embedding = self.segment_emb(segment_ids)
        # TODO make it cleaner/better
        pos_embedding = keras.layers.Lambda(
            lambda x: self.pos_emb(K.variable(np.arange(self.max_len).reshape((1, -1)))))(segment_embedding)
        if self.use_one_dropout:
            return self.dropout(keras.layers.add([token_embedding, segment_embedding, pos_embedding]))
        else:
            return keras.layers.add(
                [self.dropout(token_embedding), self.dropout(segment_embedding), self.dropout(pos_embedding)])
