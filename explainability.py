import shap
import pickle
import pandas as pd
import numpy as np

# -------------------------
# LOAD MODELS
# -------------------------
model = pickle.load(open("data/final_model.pkl", "rb"))
scaler = pickle.load(open("data/scaler.pkl", "rb"))
anomaly_model = pickle.load(open("data/anomaly_model.pkl", "rb"))

# -------------------------
# FEATURES
# -------------------------
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
# SHAP EXPLAINER
# -------------------------
explainer = shap.TreeExplainer(model)

# -------------------------
# EXPLAIN FUNCTION
# -------------------------
def explain_prediction(df):

    # scale
    X_scaled = scaler.transform(df)

    # anomaly score
    anomaly_score = anomaly_model.decision_function(X_scaled)

    # final input
    X_final = np.hstack((X_scaled, anomaly_score.reshape(-1, 1)))

    # shap values
    shap_values = explainer.shap_values(X_final)

    # handle binary classifier output
    if isinstance(shap_values, list):
        values = shap_values[1][0]
    else:
        values = shap_values[0]

    # feature importance pairs
    impacts = []

    for i, value in enumerate(values[:-1]):  # exclude anomaly score

        feature_names = {
            "latency": "Request latency",
            "cpu": "CPU usage",
            "memory": "Memory usage",
            "requests": "Traffic volume",
            "errors": "Error count",
            "latency_mean_5": "Average latency",
            "latency_std_5": "Latency instability",
            "cpu_mean_5": "Average CPU load",
            "memory_mean_5": "Average memory usage",
            "error_rate_5": "Recent error rate",
            "latency_trend": "Latency trend",
            "cpu_trend": "CPU trend",
            "latency_volatility": "Latency volatility",
            "traffic_change": "Traffic spike",
            "error_burst": "Error burst",
            "health_score": "Service health score",
            "service_auth": "Auth service",
            "service_database": "Database service",
            "service_payment": "Payment service",
            "service_search": "Search service"
        }

        impact_value = np.array(value).flatten()[0]

        impacts.append({
            "feature": feature_names.get(
                FEATURE_COLUMNS[i],
                FEATURE_COLUMNS[i]
            ),
            "impact": round(float(impact_value), 4)
        })

    # sort strongest impacts
    impacts = sorted(
        impacts,
        key=lambda x: abs(x["impact"]),
        reverse=True
    )

    return impacts[:5]