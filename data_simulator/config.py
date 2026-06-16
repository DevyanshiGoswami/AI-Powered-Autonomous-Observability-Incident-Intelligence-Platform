# config.py

TOTAL_REQUESTS = 5000

SERVICES = ["auth", "payment", "search", "database"]

# load behavior
BASE_LOAD_MIN = 50
BASE_LOAD_MAX = 500

# probabilities
SPIKE_PROBABILITY = 0.1
DB_FAILURE_PROB = 0.05

# thresholds
FAILURE_LATENCY = 900
FAILURE_CPU = 90