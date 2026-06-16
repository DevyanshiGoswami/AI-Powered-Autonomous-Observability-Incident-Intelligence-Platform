from fastapi import FastAPI
import numpy as np
import pandas as pd
import pickle

app = FastAPI()

# load models
model = pickle.load(open("../data/final_model.pkl", "rb"))
scaler = pickle.load(open("../data/scaler.pkl", "rb"))
anomaly_model = pickle.load(open("../data/anomaly_model.pkl", "rb"))

# IMPORTANT: feature columns (must match training)
FEATURE_COLUMNS = [
    'latency', 'cpu', 'memory', 'requests', 'errors',
    'latency_mean_5', 'latency_std_5',
    'cpu_mean_5', 'memory_mean_5',
    'error_rate_5',
    'latency_trend', 'cpu_trend',
    'latency_volatility',
    'traffic_change',
    'error_burst',
    'health_score',
    'service_auth', 'service_database',
    'service_payment', 'service_search'
]


@app.post("/predict")
def predict(data: dict):

    # convert input to dataframe
    df = pd.DataFrame([data])

    # ensure all columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    df = df[FEATURE_COLUMNS]

    # scale
    X_scaled = scaler.transform(df)

    # anomaly score
    anomaly_score = anomaly_model.decision_function(X_scaled)
    anomaly_score = anomaly_score.reshape(-1, 1)

    # combine
    X_final = np.hstack((X_scaled, anomaly_score))

    # predict
    prediction = model.predict(X_final)[0]
    probability = model.predict_proba(X_final)[0][1]

    return {
        "failure_prediction": int(prediction),
        "failure_probability": float(probability)
    }