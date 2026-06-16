import pandas as pd
import numpy as np
import pickle

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

INPUT_FILE = "../data/processed_features.csv"

MODEL_OUTPUT = "../data/final_model.pkl"
SCALER_OUTPUT = "../data/scaler.pkl"
ANOMALY_OUTPUT = "../data/anomaly_model.pkl"


def train():
    df = pd.read_csv(INPUT_FILE)

    # -------------------------
    # 🎯 Target
    # -------------------------
    y = df["failure"]

    # -------------------------
    # 🔥 Drop non-feature columns
    # -------------------------
    X = df.drop(columns=["failure", "timestamp"])

    # -------------------------
    # 🔥 Scaling
    # -------------------------
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # -------------------------
    # 🔥 Train/Test split
    # -------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    # -------------------------
    # 🔥 1. Anomaly Model
    # -------------------------
    anomaly_model = IsolationForest(contamination=0.1, random_state=42)
    anomaly_model.fit(X_train)

    # anomaly scores
    anomaly_scores = anomaly_model.decision_function(X_scaled)

    # reshape for combining
    anomaly_scores = anomaly_scores.reshape(-1, 1)

    # -------------------------
    # 🔥 Combine features + anomaly
    # -------------------------
    X_combined = np.hstack((X_scaled, anomaly_scores))

    # split again
    X_train_c, X_test_c, y_train, y_test = train_test_split(
        X_combined, y, test_size=0.2, random_state=42
    )

    # -------------------------
    # 🔥 2. Classifier
    # -------------------------
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train_c, y_train)

    # -------------------------
    # 🎯 Evaluation
    # -------------------------
    acc = clf.score(X_test_c, y_test)
    print(f"✅ Accuracy: {acc:.4f}")

    # -------------------------
    # 💾 Save models
    # -------------------------
    pickle.dump(clf, open(MODEL_OUTPUT, "wb"))
    pickle.dump(scaler, open(SCALER_OUTPUT, "wb"))
    pickle.dump(anomaly_model, open(ANOMALY_OUTPUT, "wb"))

    print("✅ Models saved successfully")


if __name__ == "__main__":
    train()