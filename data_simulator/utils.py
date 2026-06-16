# utils.py

import random
import config


def generate_metrics(base_load):
    cpu = min(30 + base_load * 0.5 + random.randint(-5, 5), 100)
    memory = min(25 + base_load * 0.4 + random.randint(-5, 5), 100)
    latency = min(100 + base_load * 2 + random.randint(-20, 50), 2000)
    requests = base_load + random.randint(-20, 20)

    return latency, cpu, memory, requests


def apply_cascading_failure(service, db_failed, latency, cpu):
    errors = 0
    failure = 0

    # database failure
    if service == "database" and db_failed:
        latency += 800
        cpu = min(cpu + 30, 100)
        errors = 1
        failure = 1

    # other services affected
    elif db_failed:
        latency += 300
        cpu = min(cpu + 20, 100)
        errors = random.choice([0, 1])
        failure = 1 if latency > 800 else 0

    return latency, cpu, errors, failure


def check_natural_failure(latency, cpu):
    if latency > config.FAILURE_LATENCY or cpu > config.FAILURE_CPU:
        return 1, 1
    return 0, 0