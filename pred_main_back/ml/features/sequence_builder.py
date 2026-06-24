from collections import deque
import numpy as np
import torch

class SequenceBuilder:
    def __init__(self, seq_length):
        self.seq_length = seq_length
        self.history = {}

    def transform(self, row_df, engine_id):

        if engine_id not in self.history:
            self.history[engine_id] = deque(maxlen=self.seq_length)

        self.history[engine_id].append(row_df.iloc[0].values)

        seq = np.array(self.history[engine_id])

        if len(seq) < self.seq_length:
            pad = np.zeros(
                (self.seq_length - len(seq), seq.shape[1]), dtype=np.float32
            )
            seq = np.vstack([pad, seq])

        tensor = torch.tensor(seq[np.newaxis], dtype=torch.float32)

        return tensor