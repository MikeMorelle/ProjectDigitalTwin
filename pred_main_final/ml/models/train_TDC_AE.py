import torch, torch.nn as nn, numpy as np, pandas as pd
from torch.utils.data import Dataset, DataLoader

#Anomalie-Modell von https://arxiv.org/html/2502.19307v3#A2

SENSORS = [f"sensor_{i}" for i in range(1, 22)]
FEATURES = ["op1", "op2", "op3"] + SENSORS

def load_data():
    df = pd.read_csv("ml/data/train_FD001.txt", sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle"] + FEATURES
    return df

df = load_data()

def moving_average(x, window=10):
    return pd.DataFrame(x).rolling(
        window, 
        min_periods=1
    ).mean().values

#TemporalDifferenceConsistency AutoEncoder unsupervised Training benötigt temporale Daten, d.h. Sensorwert zum Zeitpunkt t-1,t,t+1 
# daraus können dann neben den Phasenzuständen die Zustands-Ableitungen berechnet werden 
# Physikalische Gesetze typischweise kausale Beziehung aus State und ABleitung -> kleine Änderungen in Baleitung, große in og
class CMAPPSTemporalData(Dataset):
    def __init__(self,data):
        #shape [t, 24 Sensoren]
        self.samples = []
        for engine_id, group in data.groupby("engine_id"):
            split = int(len(group) * 0.6)
            train_part = group.iloc[:split]
            test_part = group.iloc[split:]

            values = torch.tensor(
                train_part[FEATURES].values,
                dtype=torch.float32
            )

            for i in range(1, len(values)-1):
                self.samples.append(
                    (values[i-1], values[i], values[i+1])
                )
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self,idx):
        return self.samples[idx]
    
temporal_data = CMAPPSTemporalData(df)

train_batches = DataLoader(
    temporal_data,
    batch_size=32,
    shuffle=True
)

#extrahiert latente/niedrigere Dimensioen mit Autoencoder (classical embedology)
class TDCAE(nn.Module):

    def __init__(self, input_dim=24, latent_dim=8):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim,24),
            nn.Tanh(),
            nn.Linear(24,24),
            nn.Tanh(),
            nn.Linear(24,latent_dim)
        )

        self.decoder = nn.Sequential(
            nn.Linear(latent_dim,24),
            nn.Tanh(),
            nn.Linear(24,24),
            nn.Tanh(),
            nn.Linear(24,input_dim)
        )
    
    def encode(self, x):
        latent = self.encoder(x)
        z = latent[:,:4]
        z_dot = latent[:,4:]

        return z, z_dot

    def forward(self,x):
        latent = self.encoder(x)

        z = latent[:,0:4]
        z_dot = latent[:,4:8]

        x_rec = self.decoder(latent)
        
        return x_rec, z, z_dot

class TDCAETrainer:
    def __init__(self, model, alpha=100, lr=0.003, dt=1):
        self.model = model
        self.alpha = alpha
        self.dt = dt

        self.optimizer = torch.optim.Adamax(
            model.parameters(),
            lr=lr
        )

        self.mse = nn.MSELoss()

    #für temporale Dynamik: latente Repäresnetaion von t-1 udn t+1 zur Approximation der ABleitung 
    def train_epoch(self, train_batches):
        self.model.train()

        epoch_loss = 0

        for x_prev, x_curr, x_next in train_batches:
            self.optimizer.zero_grad()

            #aktuell + z_dot=Zeitableitung von z
            x_rec,z,z_dot = self.model(x_curr)

            #Nachbarn
            z_prev,_ = self.model.encode(x_prev)
            z_next,_ = self.model.encode(x_next)

            #DIfferent
            dz_est = (z_next-z_prev)/(2*self.dt)

            tdc_loss = self.mse(dz_est, z_dot)
            rec_loss = self.mse(x_rec, x_curr)

            loss = rec_loss + self.alpha * tdc_loss
            loss.backward()
            self.optimizer.step()

            epoch_loss += loss.item()
        return epoch_loss / len(train_batches)
    
    def fit(self, train_batches, epochs=100):
        for epoch in range(epochs):
            loss = self.train_epoch(
                train_batches
            )
            print(f"Epoch {epoch+1} with loss: {loss:.5f}")

    def compute_thresholds(self, train_batches, upper_pct=86, lower_pct=9):
        self.model.eval()
        all_latents = []

        with torch.no_grad():
            for _,x_curr,_ in train_batches:
                _,z,z_dot = self.model(x_curr)
                latent = torch.cat([z,z_dot], dim=1)
                all_latents.append(latent)

        all_latents = torch.cat(all_latents)
        latent_np = all_latents.numpy()
        latent_np = moving_average(latent_np, 10)

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


    def predict(self, x, upper, lower, min_violations=2):
        self.model.eval()
        with torch.no_grad():
            _,z,z_dot = self.model(x)
            latent = torch.cat([z,z_dot],dim=1)

        latent = latent.cpu().numpy()


        violations = (
            (latent > upper) 
            |
            (latent < lower)
        ).sum(axis=1)

        return violations >= min_violations