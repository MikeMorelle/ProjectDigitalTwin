from collections import deque
import numpy as np
import torch

class SequenceBuilder:
    def __init__(self, seq_length):
        #gets sequence length from LSTM model config (s. ml/models/load_LSTM.py)
        self.seq_length = seq_length
        #history buffer for each engine_id to store the last seq_length number of feature vectors
        self.history = {}

    #IN: row_df -> pandas dataframe with one row containing the feature vector for the current cycle
    #    engine_id -> unique identifier for the engine
    #OUT: tensor of shape (1, seq_length, num_features) containing the sequence of feature vectors for the engine_id
    def transform(self, row_df, engine_id):
        #check if history buffer exists for the engine_id, if not create a new deque with maxlen=seq_length
        if engine_id not in self.history:
            self.history[engine_id] = deque(maxlen=self.seq_length)

        #append the current feature vector to the history buffer for the engine_id
        self.history[engine_id].append(row_df.iloc[0].values)

        #convert to numpy array and pad with zeros if the history buffer has less than seq_length number of feature vectors
        seq = np.array(self.history[engine_id])
        if len(seq) < self.seq_length:
            pad = np.zeros(
                (self.seq_length - len(seq), seq.shape[1]), dtype=np.float32
            )
            seq = np.vstack([pad, seq])

        #convert to torch tensor of shape (1, seq_length, num_features) for LSTM model input
        tensor = torch.tensor(seq[np.newaxis], dtype=torch.float32)

        return tensor
    
    #clear to reset the history buffers for all engines -> used when starting a new run or calc shapiq values
    def clear(self):
        self.history = {}