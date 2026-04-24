"""
AutoResearch training script.

Usage:
    python train.py [--epochs N] [--lr F] [--batch_size N] [--hidden N] [--dropout F] [--seed N]

Last line of stdout will be:
    METRIC: val_loss=<value>

AutoResearch parses this line to decide commit or revert.
"""

import argparse
import time
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# ── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--epochs",     type=int,   default=10)
parser.add_argument("--lr",         type=float, default=1e-3)
parser.add_argument("--batch_size", type=int,   default=64)
parser.add_argument("--hidden",     type=int,   default=256)
parser.add_argument("--dropout",    type=float, default=0.0)
parser.add_argument("--seed",       type=int,   default=42)
args = parser.parse_args()

torch.manual_seed(args.seed)
np.random.seed(args.seed)

# ── Device ───────────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))

# ── Synthetic dataset ─────────────────────────────────────────────────────────
try:
    from sklearn.datasets import make_classification
    X, y = make_classification(
        n_samples=5000, n_features=64, n_informative=32,
        n_classes=4, n_clusters_per_class=1, random_state=args.seed
    )
    X = X.astype(np.float32)
    y = y.astype(np.int64)
except ImportError:
    rng = np.random.RandomState(args.seed)
    X = rng.randn(5000, 64).astype(np.float32)
    y = (rng.randn(5000) > 0).astype(np.int64)

split = int(0.8 * len(X))
X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]

train_loader = DataLoader(TensorDataset(torch.tensor(X_train), torch.tensor(y_train)),
                          batch_size=args.batch_size, shuffle=True)
val_loader   = DataLoader(TensorDataset(torch.tensor(X_val),   torch.tensor(y_val)),
                          batch_size=args.batch_size)

n_classes = len(np.unique(y))

# ── Model ─────────────────────────────────────────────────────────────────────
model = nn.Sequential(
    nn.Linear(64, args.hidden),
    nn.ReLU(),
    nn.Dropout(args.dropout),
    nn.Linear(args.hidden, args.hidden),
    nn.ReLU(),
    nn.Dropout(args.dropout),
    nn.Linear(args.hidden, n_classes),
).to(device)

optimizer = optim.Adam(model.parameters(), lr=args.lr)
criterion = nn.CrossEntropyLoss()

# ── Training ──────────────────────────────────────────────────────────────────
t0 = time.time()
for epoch in range(1, args.epochs + 1):
    model.train()
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        criterion(model(xb), yb).backward()
        optimizer.step()

# ── Validation ────────────────────────────────────────────────────────────────
model.eval()
total_loss, n = 0.0, 0
with torch.no_grad():
    for xb, yb in val_loader:
        xb, yb = xb.to(device), yb.to(device)
        total_loss += criterion(model(xb), yb).item() * len(xb)
        n += len(xb)

val_loss = total_loss / n
elapsed  = time.time() - t0
print(f"Completed {args.epochs} epochs in {elapsed:.1f}s | val_loss={val_loss:.4f}")

# ── AutoResearch parses this line ─────────────────────────────────────────────
print(f"METRIC: val_loss={val_loss:.4f}")
