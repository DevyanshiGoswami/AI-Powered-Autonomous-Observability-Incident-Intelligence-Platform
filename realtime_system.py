import threading
import time
import random
from queue import Queue
from datetime import datetime

import numpy as np
import pandas as pd
import pickle
from collections import defaultdict, deque

# store last 10 records per service
history = defaultdict(lambda: deque(maxlen=10))

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

# -------------------------
# Load models
# -------------------------
model = pickle.load(open("data/final_model.pkl", "rb"))
scaler = pickle.load(open("data/scaler.pkl", "rb"))
anomaly_model = pickle.load(open("data/anomaly_model.pkl", "rb"))

queue = Queue()

SERVICES = ["auth", "payment", "search", "database"]

# -------------------------
# Producer (Simulator)
# -------------------------
def producer():
    while True:
        base = random.randint(50, 300)

        data = {
            "timestamp": str(datetime.now()),
            "service": random.choice(SERVICES),
            "latency": random.randint(100, 1000),
            "cpu": random.randint(40, 95),
            "memory": random.randint(30, 90),
            "requests": base,
            "errors": random.choice([0, 1])
        }

        queue.put(data)
        print("📤 Produced:", data)

        time.sleep(1)


# -------------------------
# Consumer (Prediction)
# -------------------------
def consumer():
    while True:
        try:
            data = queue.get()
            service = data["service"]

            print("📥 Consumed:", data)

            # store history
            history[service].append(data)

            records = list(history[service])

            # need at least 5 points
            if len(records) < 5:
                print("⏳ Not enough data for features yet...")
                continue

            df_hist = pd.DataFrame(records)

            # -------------------------
            # 🔥 REAL FEATURES
            # -------------------------
            latency_mean_5 = df_hist["latency"].tail(5).mean()
            latency_std_5 = df_hist["latency"].tail(5).std()

            cpu_mean_5 = df_hist["cpu"].tail(5).mean()
            memory_mean_5 = df_hist["memory"].tail(5).mean()

            error_rate_5 = df_hist["errors"].tail(5).mean()

            latency_trend = df_hist["latency"].iloc[-1] - df_hist["latency"].iloc[-2]
            cpu_trend = df_hist["cpu"].iloc[-1] - df_hist["cpu"].iloc[-2]

            latency_volatility = df_hist["latency"].std()

            traffic_change = (
                (df_hist["requests"].iloc[-1] - df_hist["requests"].iloc[-2]) /
                max(df_hist["requests"].iloc[-2], 1)
            )

            error_burst = df_hist["errors"].sum()

            health_score = (
                100
                - (0.4 * data["latency"])
                - (0.3 * data["cpu"])
                - (0.3 * data["errors"] * 100)
            )

            # -------------------------
            # FINAL INPUT
            # -------------------------
            df = pd.DataFrame([{
                "latency": data["latency"],
                "cpu": data["cpu"],
                "memory": data["memory"],
                "requests": data["requests"],
                "errors": data["errors"],

                "latency_mean_5": latency_mean_5,
                "latency_std_5": latency_std_5,
                "cpu_mean_5": cpu_mean_5,
                "memory_mean_5": memory_mean_5,
                "error_rate_5": error_rate_5,

                "latency_trend": latency_trend,
                "cpu_trend": cpu_trend,
                "latency_volatility": latency_volatility,
                "traffic_change": traffic_change,
                "error_burst": error_burst,
                "health_score": health_score,

                "service_auth": 1 if service == "auth" else 0,
                "service_database": 1 if service == "database" else 0,
                "service_payment": 1 if service == "payment" else 0,
                "service_search": 1 if service == "search" else 0,
            }])

            df = df[FEATURE_COLUMNS]

            # -------------------------
            # MODEL
            # -------------------------
            X_scaled = scaler.transform(df)

            anomaly_score = anomaly_model.decision_function(X_scaled)
            X_final = np.hstack((X_scaled, anomaly_score.reshape(-1, 1)))

            prediction = model.predict(X_final)[0]
            prob = model.predict_proba(X_final)[0][1]

            print(f"🧠 SMART Prediction: {prediction} | Risk: {prob:.2f}")

# -------------------------
# 🚨 ALERT SYSTEM
            # -------------------------
            if prob > 0.7:
                print(f"🚨 ALERT: High failure risk in {service} service!")

            # -------------------------
            # ⚡ AUTO-ACTION SYSTEM
            # -------------------------
            if prob > 0.85:
                print(f"🚀 ACTION: Scaling {service} service...")

        except Exception as e:
            print("❌ ERROR:", e)

# -------------------------
# Run threads
# -------------------------
if __name__ == "__main__":
    t1 = threading.Thread(target=producer, daemon=True)
    t2 = threading.Thread(target=consumer, daemon=True)

    t1.start()
    t2.start()

    while True:
        time.sleep(1)