import torch.nn as nn
import json
import joblib
import torch

#LSTM model class definition
class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size  = input_size,
            hidden_size = hidden_size,
            num_layers  = num_layers,
            batch_first = True,
            dropout     = dropout
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out).squeeze()


def load_LSTM_model():
    #if applicable, set device to GPU, for now CPU
    device = "cpu"

    #load the model config, then load the model state dict into a new LSTM instance
    with open("ml/models/latest/config.json") as f:
        loaded_config = json.load(f)

    LOADED_FEATURE_COLUMNS = loaded_config['feature_columns']
    LOADED_SEQ_LENGTH      = loaded_config['seq_length']

    loaded_scaler = joblib.load("ml/models/latest/scaler.pkl")

    loaded_model = LSTM(
        input_size  = loaded_config['input_size'],
        hidden_size = loaded_config['hidden_size'],
        num_layers  = loaded_config['num_layers'],
        dropout     = loaded_config['dropout'],
    ).to(device)

    loaded_model.load_state_dict(
        torch.load("ml/models/latest/model_state_dict.pth", map_location=device)
    )

    #set model into eval mode to diable training specific layers like dropout and batchnorm
    loaded_model.eval()

    return loaded_model, loaded_scaler, LOADED_FEATURE_COLUMNS, LOADED_SEQ_LENGTH
