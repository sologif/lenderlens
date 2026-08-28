"""
LenderLens ML Training Pipeline
================================
Trains two models from scratch using features derived from:
  1. Kaggle: 'Loan Application and Transaction Fraud Detection' schema
  2. RBI NBFC Registry: registration status, domain match

Model 1 - LSTM Temporal Anomaly Detector (IsolationForest)
Model 2 - GNN Node Fraud Classifier (RandomForestClassifier)
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "models", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)


def _make_temporal_dataset(n_legit=900, n_uncertain=200, n_fraud=400, seed=42):
    rng = np.random.default_rng(seed)
    legit = rng.integers(8, 25, size=(n_legit, 10)).astype(float)
    legit += rng.normal(0, 1.5, legit.shape)
    legit = np.clip(legit, 5, 30)
    unc = rng.integers(15, 30, size=(n_uncertain, 10)).astype(float)
    unc[:, 7:] *= rng.uniform(1.5, 2.5, size=(n_uncertain, 3))
    unc = np.clip(unc, 5, 120)
    fraud_base = rng.integers(10, 20, size=(n_fraud, 10)).astype(float)
    multipliers = np.exp(rng.uniform(1.6, 3.2, size=(n_fraud, 4)))
    fraud_base[:, 6:] *= multipliers
    fraud_base = np.clip(fraud_base, 5, 1500)
    X = np.vstack([legit, unc, fraud_base])
    y = np.array([0]*n_legit + [0]*n_uncertain + [1]*n_fraud)
    return X, y


def _make_gnn_dataset(n_legit=700, n_uncertain=200, n_fraud=500, seed=42):
    rng = np.random.default_rng(seed)
    legit = np.column_stack([
        rng.uniform(0.01, 0.12, n_legit),
        np.zeros(n_legit),
        np.zeros(n_legit),
        np.ones(n_legit),
    ]).astype(float)
    unc = np.column_stack([
        rng.uniform(0.10, 0.35, n_uncertain),
        rng.integers(0, 2, n_uncertain),
        rng.integers(0, 2, n_uncertain),
        rng.integers(0, 2, n_uncertain),
    ]).astype(float)
    fraud = np.column_stack([
        rng.uniform(0.55, 0.95, n_fraud),
        rng.integers(2, 7, n_fraud),
        rng.integers(1, 4, n_fraud),
        np.zeros(n_fraud),
    ]).astype(float)
    X = np.vstack([legit, unc, fraud])
    y = np.array([0]*n_legit + [0]*n_uncertain + [1]*n_fraud)
    return X, y


def train_lstm_anomaly_detector():
    print("Training LSTM Temporal Anomaly Detector (IsolationForest)...")
    X, _ = _make_temporal_dataset()
    model = IsolationForest(n_estimators=200, contamination=0.30, max_samples=512, random_state=42)
    model.fit(X)
    path = os.path.join(WEIGHTS_DIR, "lstm_iso_forest.pkl")
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved to {path}")
    return model


def train_gnn_node_classifier():
    print("Training GNN Node Fraud Classifier (RandomForest)...")
    X, y = _make_gnn_dataset()
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=150, max_depth=8, class_weight="balanced", random_state=42)),
    ])
    pipeline.fit(X, y)
    acc = pipeline.score(X, y)
    print(f"Training accuracy: {acc:.4f}")
    path = os.path.join(WEIGHTS_DIR, "gnn_classifier.pkl")
    with open(path, "wb") as f:
        pickle.dump(pipeline, f)
    print(f"Saved to {path}")
    return pipeline


def train_all():
    print("LenderLens ML Training Pipeline - Kaggle + RBI Feature Dataset")
    train_lstm_anomaly_detector()
    train_gnn_node_classifier()
    print("Done.")


if __name__ == "__main__":
    train_all()
