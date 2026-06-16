import asyncio
import json
import random
from datetime import datetime
from collections import defaultdict, deque
from self_healing import auto_remediate
import numpy as np
import pandas as pd
import pickle
import websockets
import sqlite3
from flask import request
from explainability import explain_prediction
from event_store import save_event
from event_store import get_events
from flask import Flask, jsonify
from threading import Thread
from flask_cors import CORS
from prometheus_client import (
    start_http_server,
    Gauge
)
app = Flask(__name__)
CORS(app)
registered_services = {}
incoming_metrics = []
# ---------------------------------
# PROMETHEUS METRICS
# ---------------------------------

risk_metric = Gauge(
    "ai_risk_score",
    "AI predicted infrastructure risk",
    ["service"]
)

latency_metric = Gauge(
    "service_latency",
    "Service latency",
    ["service"]
)

cpu_metric = Gauge(
    "service_cpu_usage",
    "CPU usage",
    ["service"]
)

health_metric = Gauge(
    "service_health_score",
    "Health score",
    ["service"]
)
# ---------------------------------
# SLA / SLO RULES
# ---------------------------------
SLA_RULES = {

    "latency": 500,
    "cpu": 85,
    "memory": 90,
    "risk": 0.80

}
# ---------------------------------
# SERVICE DEPENDENCY GRAPH
# ---------------------------------
SERVICE_DEPENDENCIES = {

    "auth": ["database"],

    "payment": [
        "database",
        "auth"
    ],

    "search": [
        "database"
    ],

    "database": []

}

# -------------------------
# LOAD MODELS
# -------------------------
model = pickle.load(open("data/final_model.pkl", "rb"))
scaler = pickle.load(open("data/scaler.pkl", "rb"))
anomaly_model = pickle.load(open("data/anomaly_model.pkl", "rb"))

# -------------------------
# DATABASE
# -------------------------
conn = sqlite3.connect("incidents.db", check_same_thread=False)
cursor = conn.cursor()

# -------------------------
# SERVICE DEPENDENCIES
# -------------------------
DEPENDENCIES = {

    "auth": ["database"],

    "payment": ["database"],

    "search": ["database"],

    "database": []

}
# -------------------------
# SERVICE HEALTH MEMORY
# -------------------------
service_health = {
    "auth": 0,
    "payment": 0,
    "search": 0,
    "database": 0
}

# -------------------------
# FEATURE COLUMNS
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
# MEMORY
# -------------------------
history = defaultdict(lambda: deque(maxlen=10))

SERVICES = ["auth", "payment", "search", "database"]


# -------------------------
# GENERATE DATA
# -------------------------
def generate_data():
    return {
        "timestamp": str(datetime.now()),
        "service": random.choice(SERVICES),
        "latency": random.randint(100, 1000),
        "cpu": random.randint(40, 95),
        "memory": random.randint(30, 90),
        "requests": random.randint(50, 300),
        "errors": random.choice([0, 1])
    }

# ---------------------------------
# AI HEALTH SCORE
# ---------------------------------
def calculate_health_score(
    latency,
    cpu,
    memory,
    errors,
    risk
):

    score = 100

    # latency penalty
    if latency > 700:
        score -= 25
    elif latency > 400:
        score -= 15

    # cpu penalty
    if cpu > 85:
        score -= 20
    elif cpu > 70:
        score -= 10

    # memory penalty
    if memory > 85:
        score -= 15
    elif memory > 70:
        score -= 8

    # errors penalty
    if errors > 0:
        score -= 20

    # AI risk penalty
    score -= int(risk * 30)

    # keep between 0-100
    score = max(0, min(100, score))

    return score
# ---------------------------------
# SLA / SLO VIOLATION ENGINE
# ---------------------------------
def check_slo_violations(
    latency,
    errors,
    risk
):

    violations = []

    # latency SLO
    if latency > 300:
        violations.append(
            "Latency SLO breached"
        )

    # error SLO
    if errors > 0:
        violations.append(
            "Error rate SLO breached"
        )

    # reliability SLA
    if risk > 0.75:
        violations.append(
            "Reliability SLA at risk"
        )

    if len(violations) > 0:

        status = "VIOLATED"

    else:

        status = "HEALTHY"

    return {
        "status": status,
        "violations": violations
    }
# ---------------------------------
# CASCADE FAILURE DETECTION
# ---------------------------------
def detect_cascade_failure(
    service,
    risk
):

    impacted_services = []

    if risk > 0.60:

        for dependent_service, dependencies in SERVICE_DEPENDENCIES.items():

            if service in dependencies:

                impacted_services.append(
                    dependent_service
                )

    return impacted_services

# ---------------------------------
# SLA VIOLATION DETECTION
# ---------------------------------
def detect_sla_violations(
    data,
    risk
):

    violations = []

    if data["latency"] > SLA_RULES["latency"]:

        violations.append(
            "Latency SLA breached"
        )

    if data["cpu"] > SLA_RULES["cpu"]:

        violations.append(
            "CPU SLA breached"
        )

    if data["memory"] > SLA_RULES["memory"]:

        violations.append(
            "Memory SLA breached"
        )

    if risk > SLA_RULES["risk"]:

        violations.append(
            "AI risk threshold breached"
        )

    return violations

# ---------------------------------
# AI FAILURE FORECASTING
# ---------------------------------
def generate_forecast(
    latency,
    cpu,
    memory,
    risk
):

    forecast = {
        "status": "STABLE",
        "confidence": 0,
        "message": "System stable"
    }

    score = 0

    # latency trend
    if latency > 700:
        score += 35

    elif latency > 400:
        score += 20

    # cpu trend
    if cpu > 85:
        score += 30

    elif cpu > 70:
        score += 15

    # memory trend
    if memory > 85:
        score += 20

    elif memory > 70:
        score += 10

    # risk contribution
    score += int(risk * 30)

    # determine forecast
    if score >= 70:

        forecast = {

            "status": "FAILURE LIKELY",

            "confidence": min(
                95,
                score
            ),

            "message":
            "Service degradation increasing rapidly"

        }

    elif score >= 45:

        forecast = {

            "status": "UNSTABLE",

            "confidence": score,

            "message":
            "Potential instability detected"

        }

    return forecast

# ---------------------------------
# INCIDENT CORRELATION ENGINE
# ---------------------------------
def correlate_incidents(
    service,
    dependencies,
    risk,
    cascade_impacts
):

    correlation = {

        "root_cause": None,
        "related_services": [],
        "summary": "No major correlated incident"

    }

    # database correlation
    if service == "database" and risk > 0.7:

        correlation = {

            "root_cause":
            "Database instability detected",

            "related_services":
            cascade_impacts,

            "summary":
            "Database outage may impact dependent services"

        }

    # payment correlation
    elif (
        service == "payment"
        and "database" in dependencies
        and risk > 0.7
    ):

        correlation = {

            "root_cause":
            "Possible upstream database degradation",

            "related_services":
            ["database"],

            "summary":
            "Payment instability likely linked to database latency"

        }

    # auth correlation
    elif (
        service == "auth"
        and "database" in dependencies
        and risk > 0.7
    ):

        correlation = {

            "root_cause":
            "Authentication dependency degradation",

            "related_services":
            ["database"],

            "summary":
            "Auth failures may originate from database instability"

        }

    # search correlation
    elif (
        service == "search"
        and risk > 0.7
    ):

        correlation = {

            "root_cause":
            "Search infrastructure instability",

            "related_services":
            dependencies,

            "summary":
            "Search service degradation affecting dependent APIs"

        }

    return correlation

# -------------------------
# WEBSOCKET SERVER
# -------------------------
async def handler(websocket):
    while True:

        if incoming_metrics:

            data = incoming_metrics.pop(0)

        else:

            data = generate_data()

        service = data["service"]

        history[service].append(data)

        records = list(history[service])

        # wait for enough data
        if len(records) < 5:
            await asyncio.sleep(1)
            continue

        df_hist = pd.DataFrame(records)

        # -------------------------
        # FEATURES
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
        # FINAL DATAFRAME
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

        prediction = int(model.predict(X_final)[0])
        risk = float(model.predict_proba(X_final)[0][1])
        # -------------------------
        # DEPENDENCY INTELLIGENCE
        # -------------------------
        dependency_risk = 0

        dependencies = DEPENDENCIES.get(service, [])

        for dep in dependencies:

            dep_risk = service_health.get(dep, 0)

            dependency_risk += dep_risk * 0.15

        # increase risk from unhealthy dependencies
        risk += dependency_risk

        # cap risk
        risk = min(risk, 1.0)

        # update service health memory
        service_health[service] = risk
        # -------------------------
        # SHAP EXPLANATION
        # -------------------------
        explanations = explain_prediction(df)

        # -------------------------
        # ROOT CAUSE AI
        # -------------------------
        causes = []

        if data["latency"] > 700:
            causes.append("High latency spike")

        if data["cpu"] > 85:
            causes.append("CPU overload")

        if error_rate_5 > 0.4:
            causes.append("High error rate")

        if latency_volatility > 250:
            causes.append("Latency instability")

        if traffic_change > 0.5:
            causes.append("Sudden traffic surge")

        if error_burst >= 3:
            causes.append("Error burst detected")

        if len(causes) == 0:
            causes.append("Minor instability detected")

        # -------------------------
        # STORE INCIDENT
        # -------------------------
        if risk > 0.7:

            cursor.execute("""
            INSERT INTO incidents (timestamp, service, risk, causes)
            VALUES (?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                service,
                round(risk, 2),
                ", ".join(causes)
            ))

            conn.commit()

            print("💾 Incident stored")

        # -------------------------
        # SEND TO FRONTEND
        # -------------------------
        # -------------------------
        # SELF HEALING
        # -------------------------
        healing = auto_remediate(service, risk)
        health_score = calculate_health_score(
            data["latency"],
            data["cpu"],
            data["memory"],
            data["errors"],
            risk
        )
        cascade_impacts = detect_cascade_failure(
        service,
        risk
    )
        slo_data = check_slo_violations(
        data["latency"],
        data["errors"],
        risk
    )
        forecast = generate_forecast(
        data["latency"],
        data["cpu"],
        data["memory"],
        risk
    )
        correlation = correlate_incidents(
        service,
        dependencies,
        risk,
        cascade_impacts
    )
        # ---------------------------------
        # UPDATE PROMETHEUS METRICS
        # ---------------------------------
        print("PROMETHEUS UPDATE", service, risk)
        risk_metric.labels(
            service=service
        ).set(risk)

        latency_metric.labels(
            service=service
        ).set(data["latency"])

        cpu_metric.labels(
            service=service
        ).set(data["cpu"])

        health_metric.labels(
            service=service
        ).set(health_score)
        response = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "service": service,
            "latency": data["latency"],
            "cpu": data["cpu"],
            "risk": round(risk, 2),
            "prediction": prediction,
            "causes": causes,
            "explanations": explanations,
            "dependencies": dependencies,
            "health_score": health_score,
            "forecast": forecast,
            "cascade_impacts": cascade_impacts,
            "correlation": correlation,
            "slo": slo_data,
            "healing": healing
        }
        save_event(response)
        print("EVENT SAVED:", response)

        try:
            await websocket.send(json.dumps(response))
            print("📡 Sent:", response)

        except websockets.exceptions.ConnectionClosed:
            print("⚠️ Frontend disconnected")
            break

        await asyncio.sleep(1)
@app.route("/incidents")
def incidents():

    return jsonify(get_events())

@app.route("/metrics-ingest", methods=["POST"])
def metrics_ingest():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "message": "No JSON received"
        }, 400

    incoming_metrics.append(data)

    print("Received metrics:", data)

    return {
        "status": "success",
        "received": data
    }
@app.route(
    "/register-service",
    methods=["POST"]
)
def register_service():

    data = request.json

    service = data["service"]

    registered_services[service] = {

        "dependencies":
        data.get(
            "dependencies",
            []
        ),

        "team":
        data.get(
            "team",
            "unknown"
        )

    }

    return {

        "status":
        "registered",

        "service":
        service

    }
@app.route("/test-metric")
def test_metric():

    incoming_metrics.append({

        "service":"payment",

        "latency":900,

        "cpu":88,

        "memory":75,

        "requests":200,

        "errors":5

    })

    return {
        "status":"sent"
    }
@app.route("/services")
def get_services():

    return registered_services

@app.route("/timeline")
def timeline():

    return jsonify(get_events())
def run_flask():

    app.run(
        host="0.0.0.0",
        port=5500
    )

# ---------------------------------
# START PROMETHEUS EXPORTER
# ---------------------------------

start_http_server(8000)
# START FLASK IN SEPARATE THREAD
Thread(target=run_flask).start()
# -------------------------
# START SERVER
# -------------------------
async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("🚀 WebSocket running on ws://localhost:8765")
        await asyncio.Future()


asyncio.run(main())