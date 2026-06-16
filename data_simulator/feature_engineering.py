import pandas as pd

INPUT_FILE = "../data/api_logs.csv"
OUTPUT_FILE = "../data/processed_features.csv"


def create_features():
    df = pd.read_csv(INPUT_FILE)

    # sort by time per service
    df = df.sort_values(["service", "timestamp"])

    # convert timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # -------------------------
    # 🔥 Rolling Features
    # -------------------------
    df["latency_mean_5"] = df.groupby("service")["latency"].rolling(5).mean().reset_index(0, drop=True)
    df["latency_std_5"] = df.groupby("service")["latency"].rolling(5).std().reset_index(0, drop=True)

    df["cpu_mean_5"] = df.groupby("service")["cpu"].rolling(5).mean().reset_index(0, drop=True)
    df["memory_mean_5"] = df.groupby("service")["memory"].rolling(5).mean().reset_index(0, drop=True)

    df["error_rate_5"] = df.groupby("service")["errors"].rolling(5).mean().reset_index(0, drop=True)

    # -------------------------
    # 🔥 Trend Features
    # -------------------------
    df["latency_trend"] = df.groupby("service")["latency"].diff()
    df["cpu_trend"] = df.groupby("service")["cpu"].diff()

    # -------------------------
    # 🔥 Volatility (instability)
    # -------------------------
    df["latency_volatility"] = df.groupby("service")["latency"].rolling(10).std().reset_index(0, drop=True)

    # -------------------------
    # 🔥 Traffic spike
    # -------------------------
    df["traffic_change"] = df.groupby("service")["requests"].pct_change()

    # -------------------------
    # 🔥 Error burst
    # -------------------------
    df["error_burst"] = df.groupby("service")["errors"].rolling(10).sum().reset_index(0, drop=True)

    # -------------------------
    # 🔥 Custom Health Score
    # -------------------------
    df["health_score"] = (
        100
        - (0.4 * df["latency"])
        - (0.3 * df["cpu"])
        - (0.3 * df["errors"] * 100)
    )

    # -------------------------
    # 🔥 Drop NaN rows (from rolling)
    # -------------------------
    df = df.dropna()

    # -------------------------
    # 🔥 Encode service (important)
    # -------------------------
    df = pd.get_dummies(df, columns=["service"])

    # -------------------------
    # Save processed data
    # -------------------------
    df.to_csv(OUTPUT_FILE, index=False)

    print("✅ DONE: processed_features.csv created")


if __name__ == "__main__":
    create_features()