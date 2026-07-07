import torch, torch.nn as nn, numpy as np, pandas as pd
from torch.utils.data import Dataset, DataLoader
from collections import deque
from ml.data.load_data import load_data
from config import SENSORS, OPS

#model from https://arxiv.org/html/2502.19307v3

FEATURES = OPS + SENSORS

df = load_data("FD001")

#smooth sensor data with in paper specified window size
def moving_average(x, window=12):
    return pd.DataFrame(x).rolling(
        window, 
        min_periods=1
    ).mean().values

#TDCAE needs a temporal dataset with t-1, t, t+1 for each engine_id to learn the temporal dynamics of the system
class CMAPPSTemporalData(Dataset):
    def __init__(self,data):
        #save all samples as tuples of (past, now, future) for each engine_id 
        self.samples = []

        #group by engine to remain consistency
        for engine_id, group in data.groupby("engine_id"):
            #60% of data for training
            split = int(len(group) * 0.6)
            train_part = group.iloc[:split]
            test_part = group.iloc[split:]

            #tensor of feat values
            values = torch.tensor(
                train_part[FEATURES].values,
                dtype=torch.float32
            )

            #build temporal triplets
            for i in range(1, len(values)-1):
                self.samples.append(
                    (values[i-1], values[i], values[i+1])
                )
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self,idx):
        return self.samples[idx]

temporal_data = CMAPPSTemporalData(df)

#dataloader for mini batch training
train_batches = DataLoader(
    temporal_data,
    batch_size=32,
    shuffle=True
)

#Temporal Difference Consistency AutoEncoder (TDCAE) 
#learns latent states as well as their temporal dynamics (z_dot) to detect anomalies in the system 
class TDCAE(nn.Module):

    def __init__(self, input_dim=24, latent_dim=10):
        super().__init__()

        #encoder projects in latent space of size latent_dim (5 for z and 5 for z_dot) -> paper uses 10 and 8 latent dimensions?
        self.encoder = nn.Sequential(
            nn.Linear(input_dim,24),
            nn.Tanh(),
            nn.Linear(24,24),
            nn.Tanh(),
            nn.Linear(24,latent_dim)
        )

        #decoder reconstructs the input from the latent space
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim,24),
            nn.Tanh(),
            nn.Linear(24,24),
            nn.Tanh(),
            nn.Linear(24,input_dim)
        )
    
    def encode(self, x):
        #extract latent representation
        latent = self.encoder(x)
        #separete in state z and temporal derivative z_dot
        z = latent[:,:5]
        z_dot = latent[:,5:]

        return z, z_dot

    def forward(self,x):
        latent = self.encoder(x)

        z = latent[:,:5]
        z_dot = latent[:,5:]

        #reconstruct the input from the latent representation
        x_rec = self.decoder(latent)
        
        return x_rec, z, z_dot

#trainer for TDCAE with reconstruction loss and temporal difference consistency loss
class TDCAETrainer:
    def __init__(self, model, alpha=100, lr=0.003, dt=1):
        self.model = model
        self.alpha = alpha  #weight for temporal difference consistency loss
        self.dt = dt    #time difference between samples (1 as an example)

        #paper used Adamax opti
        self.optimizer = torch.optim.Adamax(
            model.parameters(),
            lr=lr
        )
        #paper used MSE loss
        self.mse = nn.MSELoss()

    def train_epoch(self, train_batches):
        #activate training mode to enable dropout and batchnorm layers
        self.model.train()

        epoch_loss = 0

        for x_prev, x_curr, x_next in train_batches:
            self.optimizer.zero_grad()

            #predict current state
            x_rec,z,z_dot = self.model(x_curr)

            #latent states of temporal neighbours
            z_prev,_ = self.model.encode(x_prev)
            z_next,_ = self.model.encode(x_next)

            #approximation of temporal derivative
            dz_est = (z_next-z_prev)/(2*self.dt)

            tdc_loss = self.mse(dz_est, z_dot)
            rec_loss = self.mse(x_rec, x_curr)

            #loss = dynamic consistency loss + reconstruction loss
            loss = rec_loss + self.alpha * tdc_loss
            loss.backward()
            self.optimizer.step()

            epoch_loss += loss.item()
        return epoch_loss / len(train_batches)
    
    def fit(self, train_batches, epochs=50):
        #for multiple epochs
        for epoch in range(epochs):
            loss = self.train_epoch(
                train_batches
            )
            print(f"Epoch {epoch+1} with loss: {loss:.5f}")

    def compute_thresholds(self, train_batches, upper_pct=86, lower_pct=9):
        #set model into eval mode to disable training specific layers like dropout and batchnorm
        self.model.eval()
        all_latents = []

        with torch.no_grad():
            #extract latent states for all training samples to compute thresholds for anomaly detection
            for _,x_curr,_ in train_batches:
                _,z,z_dot = self.model(x_curr)
                #combi of state and temporal derivative 
                latent = torch.cat([z,z_dot], dim=1)
                all_latents.append(latent)

        all_latents = torch.cat(all_latents)
        latent_np = all_latents.numpy()
        #smoothen
        latent_np = moving_average(latent_np, 10)

        #percentile based thresholds for each latent dimension to detect anomalies in the system -> once calc, in paper dynamically
        upper = np.percentile(
            latent_np,
            upper_pct,
            axis=0
        )
        lower = np.percentile(
            latent_np,
            lower_pct,
            axis=0
        )

        return upper, lower

#anomaly detection for running system
class OnlineDetector:
    def __init__(self, upper_offset, lower_offset, window=12):
        self.window=window
        #tolerance for each latent dimension to account for noise and variability in the system -> once calc, in paper dynamically
        self.upper_offset = upper_offset
        self.lower_offset = lower_offset
        self.history = None
    
    def update(self, latent):
        #ensure 1D vector
        latent = latent.flatten()

        #init history buffers for each latent dimension to store the last window number of latent states
        if self.history is None:
            self.history = [
                deque([value], maxlen=self.window)
                for value in latent
            ]
        
        baseline= []

        #smoothed mean as dynamic reference for each latent dimension to detect anomalies in the system
        for value, history in zip(latent, self.history):
            history.append(value)
            baseline.append(np.mean(history))

        baseline = np.array(baseline)

        upper = baseline + self.upper_offset
        lower = baseline - self.lower_offset

        #check for violations of the thresholds for each latent dimension 
        violations = (
            (latent>upper)
            |
            (latent<lower)
        )

        #anomaly if at least 2 latent dimensions violate the thresholds
        return violations.sum() >= 2
        